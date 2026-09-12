#!/usr/bin/env python3
"""Borra un libro por completo: R2 y ficha de Appwrite. Para volver a subirlo.

PARA QUE EXISTE ESTO
--------------------
La app no puede borrar estos 97 libros: el endpoint exige que
`added_by` sea el usuario que pide el borrado, y todos se cargaron con
added_by = "biblioteca". Nadie es su propietario, asi que el boton
"Borrar definitivamente" no le aparece a nadie. Esta es la puerta de servicio.

LO QUE HAY QUE SABER ANTES DE USARLO
-----------------------------------
R2 NO guarda el archivo original de los libros subidos antes del 12-09-2026:
solo el texto ya extraido. Para esos libros, borrar es DEFINITIVO — no hay de
donde reprocesar. Comprueba primero que tienes el PDF/EPUB a mano:

    python resetear_libros.py --libro XXXX          # solo mira y cuenta
    python resetear_libros.py --libro XXXX --borrar  # borra de verdad

Desde hoy las subidas nuevas guardan `{book_id}/original/<archivo>`, y en esos
casos el script lo avisa: se puede borrar sin perder nada.

Variables de entorno:
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
    APPWRITE_ENDPOINT  APPWRITE_PROJECT_ID  APPWRITE_API_KEY  APPWRITE_DATABASE_ID
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reparar_libros import cliente_r2, listar_libros   # noqa: E402

AW_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://nyc.cloud.appwrite.io/v1")
AW_PROJECT  = os.environ.get("APPWRITE_PROJECT_ID", "6a72f5d6002eeff78bc2")
AW_KEY      = os.environ.get("APPWRITE_API_KEY", "")
AW_DB       = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")
COLECCION   = "global_books"


# Valores que la gente pega cuando el comando traia un hueco por rellenar.
# Sin esta comprobacion, una clave "..." da un HTTP 401 con traza de treinta
# lineas y nadie entiende que el problema era el portapapeles.
PLACEHOLDERS = ("", "...", "…", "TU_CLAVE", "XXX")


def comprobar_aw_key():
    clave = (AW_KEY or "").strip()
    if clave in PLACEHOLDERS or "<" in clave or clave.count(".") == len(clave):
        raise SystemExit(
            "APPWRITE_API_KEY no tiene una clave de verdad"
            + (f" (vale {clave!r})" if len(clave) < 20 else "")
            + ".\n"
            "  Sacala de Cloud Run, en la variable APPWRITE_API_KEY:\n"
            "    gcloud run services describe libris-audio-backend "
            "--region us-west1 \\\n"
            "      --format=\"value(spec.template.spec.containers[0].env)\"\n"
            "  Empieza por 'standard_'. Y luego, en PowerShell:\n"
            "    $env:APPWRITE_API_KEY = \"standard_...la clave entera...\"")
    if not clave.startswith("standard_"):
        print("  aviso: la APPWRITE_API_KEY no empieza por 'standard_'; "
              "si falla, revisa que sea la buena.")


def _aw(metodo: str, ruta: str, cuerpo=None):
    url = f"{AW_ENDPOINT}/databases/{AW_DB}/collections/{COLECCION}{ruta}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(url, data=datos, method=metodo, headers={
        "Content-Type": "application/json",
        "X-Appwrite-Project": AW_PROJECT,
        "X-Appwrite-Key": AW_KEY,
    })
    with urllib.request.urlopen(pet, timeout=60) as r:
        cuerpo = r.read()
        return json.loads(cuerpo) if cuerpo else {}


def ficha_appwrite(book_id: str):
    consulta = json.dumps({"method": "equal", "attribute": "book_id",
                           "values": [book_id]})
    ruta = "/documents?" + urllib.parse.urlencode({"queries[0]": consulta})
    try:
        docs = _aw("GET", ruta).get("documents", [])
        return docs[0] if docs else None
    except Exception as e:
        print(f"  !! no puedo consultar Appwrite: {e}")
        return None


def claves_del_libro(s3, bucket, book_id):
    salida, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": f"{book_id}/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        salida += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return salida
        token = r.get("NextContinuationToken")


def resumen(claves):
    grupos = {}
    for k in claves:
        parte = k.split("/", 2)[1] if k.count("/") >= 1 else "(raiz)"
        if parte.endswith(".json") or parte.endswith(".png"):
            parte = "(sueltos)"
        grupos[parte] = grupos.get(parte, 0) + 1
    return grupos


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--libro", action="append", required=True,
                    help="book_id; se puede repetir")
    ap.add_argument("--borrar", action="store_true",
                    help="borra de verdad (sin esto solo informa)")
    args = ap.parse_args()

    if args.borrar:
        comprobar_aw_key()

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")
    titulos = {b.get("book_id"): b.get("title") for b in listar_libros()}

    print(f"bucket {bucket} · {'BORRANDO' if args.borrar else 'SOLO INFORMA'}\n")
    for book_id in args.libro:
        titulo = titulos.get(book_id, "(no esta en el catalogo)")
        claves = claves_del_libro(s3, bucket, book_id)
        tiene_original = any("/original/" in k for k in claves)
        print(f"  {book_id}  {titulo}")
        print(f"     {len(claves)} objetos en R2: {resumen(claves)}")
        if tiene_original:
            print("     hay ARCHIVO ORIGINAL guardado: se puede reprocesar "
                  "despues de borrar")
        else:
            print("     SIN archivo original en R2: borrar es DEFINITIVO. "
                  "Necesitas el PDF/EPUB en tu disco para volver a subirlo.")

        ficha = ficha_appwrite(book_id)
        print(f"     ficha en Appwrite: {'si' if ficha else 'NO'}"
              + (f" (added_by={ficha.get('added_by')!r})" if ficha else ""))

        if not args.borrar:
            continue

        # R2, en lotes de 1000 (el limite de delete_objects)
        for i in range(0, len(claves), 1000):
            lote = [{"Key": k} for k in claves[i:i + 1000]]
            s3.delete_objects(Bucket=bucket, Delete={"Objects": lote})
        print(f"     borrados {len(claves)} objetos de R2")

        if ficha:
            try:
                _aw("DELETE", f"/documents/{ficha['$id']}")
                print("     ficha de Appwrite borrada")
            except Exception as e:
                print(f"     !! R2 borrado pero la ficha sigue: {e}")
                print("        el libro apareceria en el catalogo sin contenido")
        print()

    if not args.borrar:
        print("Nada borrado. Anade --borrar cuando lo hayas comprobado.")
    else:
        print("Hecho. Vuelve a subir los archivos desde la app: la subida ya "
              "pasa el motor de calidad y guarda el original.")


if __name__ == "__main__":
    main()
