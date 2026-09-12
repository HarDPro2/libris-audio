#!/usr/bin/env python3
"""Vuelve a subir la biblioteca entera, pasando por el motor de calidad nuevo.

QUE ARREGLA DE UNA VEZ
----------------------
  1. El texto se extrae con el arreglo de guiones QUE USA DICCIONARIO, asi que
     ni se parten palabras ni se pegan los guiones de verdad.
  2. Pasa la revision de calidad al subir (OCR, informe en revision.json).
  3. Se guarda el ARCHIVO ORIGINAL en R2. Es lo que faltaba: hasta ahora el
     texto extraido era el unico master y no habia de donde reprocesar.
  4. `added_by` pasa a ser TU usuario. Los 97 libros entraron como
     "biblioteca", que es la razon de que nadie pueda borrarlos desde la app.

ORDEN OBLIGATORIO
-----------------
  1) Desplegar el backend nuevo en Cloud Run. Si no, la subida usa el codigo
     viejo y no sirve de nada.
  2) python subir_biblioteca.py --carpeta "E:\\PROYECTO LIBRIS AUDIO\\LIBROS"
     (solo informa: que archivo va con que ficha, y que se queda fuera)
  3) ... --subir

QUE SE PIERDE
-------------
Cada libro resubido recibe un book_id NUEVO, asi que el progreso de lectura y
los favoritos guardados de esos libros se quedan apuntando a nada. Para una
biblioteca de uso personal es barato; conviene saberlo antes.

CREDENCIALES
------------
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
    APPWRITE_API_KEY  (para borrar la ficha vieja)
    LIBRIS_EMAIL  LIBRIS_PASSWORD  (tu cuenta; si faltan, las pide)
"""
import argparse
import getpass
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalogo import emparejar                                   # noqa: E402
from reparar_libros import cliente_r2, listar_libros, API        # noqa: E402
import resetear_libros as reset                                  # noqa: E402

EXTENSIONES = (".pdf", ".epub", ".mobi", ".fb2", ".txt", ".docx")
REGISTRO = "migracion_biblioteca.json"


# ── Sesion de Appwrite ──────────────────────────────────────────────────────
def abrir_sesion(email: str, password: str) -> str:
    """Devuelve el secreto de sesion, que es lo que el backend espera como
    `Authorization: Bearer ...` (lo usa como cookie a_session_<proyecto>)."""
    url = f"{reset.AW_ENDPOINT}/account/sessions/email"
    datos = json.dumps({"email": email, "password": password}).encode()
    pet = urllib.request.Request(url, data=datos, method="POST", headers={
        "Content-Type": "application/json",
        "X-Appwrite-Project": reset.AW_PROJECT,
    })
    with urllib.request.urlopen(pet, timeout=30) as r:
        cuerpo = json.load(r)
    secreto = cuerpo.get("secret") or ""
    if not secreto:
        raise SystemExit("Appwrite no devolvio 'secret'. Revisa email y clave.")
    print(f"sesion abierta como {cuerpo.get('userId', '?')}")
    return secreto


# ── Subida multipart, sin dependencias ──────────────────────────────────────
def subir(ruta: str, titulo: str, categoria: str, token: str,
          espera: int = 900) -> dict:
    limite = f"----libris{uuid.uuid4().hex}"
    nombre = os.path.basename(ruta)
    tipo = mimetypes.guess_type(nombre)[0] or "application/octet-stream"
    with open(ruta, "rb") as f:
        contenido = f.read()

    partes = []
    for campo, valor in (("title", titulo), ("category", categoria)):
        partes.append(
            f"--{limite}\r\nContent-Disposition: form-data; name=\"{campo}\"\r\n\r\n"
            f"{valor}\r\n".encode())
    partes.append(
        f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{nombre}\"\r\nContent-Type: {tipo}\r\n\r\n".encode())
    partes.append(contenido)
    partes.append(f"\r\n--{limite}--\r\n".encode())
    cuerpo = b"".join(partes)

    pet = urllib.request.Request(
        f"{API}/api/upload-pdf", data=cuerpo, method="POST", headers={
            "Content-Type": f"multipart/form-data; boundary={limite}",
            "Content-Length": str(len(cuerpo)),
            "Authorization": f"Bearer {token}",
        })
    try:
        with urllib.request.urlopen(pet, timeout=espera) as r:
            return {"ok": True, "respuesta": json.load(r)}
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:300]
        return {"ok": False, "error": f"HTTP {e.code}: {detalle}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def cargar_registro():
    if os.path.exists(REGISTRO):
        with open(REGISTRO, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_registro(reg):
    with open(REGISTRO, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", required=True, help="carpeta con los archivos")
    ap.add_argument("--subir", action="store_true", help="hazlo de verdad")
    ap.add_argument("--archivo", action="append",
                    help="solo este archivo; se puede repetir")
    ap.add_argument("--limite", type=int, help="corta despues de N libros")
    ap.add_argument("--sin-borrar", action="store_true",
                    help="sube sin borrar el libro viejo (quedaran duplicados)")
    args = ap.parse_args()

    if not os.path.isdir(args.carpeta):
        sys.exit(f"No existe la carpeta: {args.carpeta}")

    archivos = sorted(f for f in os.listdir(args.carpeta)
                      if f.lower().endswith(EXTENSIONES))
    fichas = listar_libros()
    emparejados, sueltos, sin_archivo = emparejar(archivos, fichas)

    if args.archivo:
        pedidos = set(args.archivo)
        emparejados = {a: f for a, f in emparejados.items() if a in pedidos}

    print(f"{len(archivos)} archivos · {len(fichas)} fichas · "
          f"{len(emparejados)} emparejados\n")

    print("SE VAN A RESUBIR:")
    orden = sorted(emparejados.items(), key=lambda kv: kv[1]["title"])
    if args.limite:
        orden = orden[:args.limite]
    for a, f in orden:
        mb = os.path.getsize(os.path.join(args.carpeta, a)) / 1048576
        print(f"   {f['title'][:44]:44} <- {a[:40]:40} {mb:5.1f} MB")

    print(f"\nSE QUEDAN FUERA — archivos sin ficha ({len(sueltos)}):")
    for a in sueltos:
        print(f"   {a}")
    print(f"\nSE QUEDAN FUERA — fichas sin archivo en disco ({len(sin_archivo)}).")
    print("   Estas NO se pueden reprocesar: no hay original en ningun sitio.")
    for f in sorted(sin_archivo, key=lambda x: x["title"]):
        print(f"   {f['title']}")

    if not args.subir:
        print(f"\n[SIMULACION] Nada tocado. Revisa las tres listas y anade --subir.")
        return

    email = os.environ.get("LIBRIS_EMAIL") or input("\nEmail de tu cuenta: ").strip()
    password = os.environ.get("LIBRIS_PASSWORD") or getpass.getpass("Clave: ")
    token = abrir_sesion(email, password)

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")
    reg = cargar_registro()
    hechos = fallidos = 0

    for i, (archivo, ficha) in enumerate(orden, 1):
        book_id = ficha["book_id"]
        if reg.get(archivo, {}).get("ok"):
            print(f"  [{i}/{len(orden)}] {ficha['title'][:40]:40} ya estaba hecho")
            continue

        print(f"  [{i}/{len(orden)}] {ficha['title'][:40]:40} ", end="", flush=True)
        t0 = time.time()

        if not args.sin_borrar:
            try:
                claves = reset.claves_del_libro(s3, bucket, book_id)
                for j in range(0, len(claves), 1000):
                    s3.delete_objects(Bucket=bucket, Delete={
                        "Objects": [{"Key": k} for k in claves[j:j + 1000]]})
                doc = reset.ficha_appwrite(book_id)
                if doc:
                    reset._aw("DELETE", f"/documents/{doc['$id']}")
                print(f"borrado({len(claves)}) ", end="", flush=True)
            except Exception as e:
                print(f"FALLO al borrar: {e}")
                reg[archivo] = {"ok": False, "error": f"borrado: {e}"}
                guardar_registro(reg); fallidos += 1
                continue

        res = subir(os.path.join(args.carpeta, archivo), ficha["title"],
                    ficha.get("category") or "General", token)
        segundos = time.time() - t0
        if res["ok"]:
            nuevo = (res["respuesta"] or {}).get("book_id", "?")
            print(f"OK {nuevo} ({segundos:.0f}s)")
            reg[archivo] = {"ok": True, "book_id_viejo": book_id,
                            "book_id_nuevo": nuevo, "segundos": round(segundos)}
            hechos += 1
        else:
            print(f"FALLO ({segundos:.0f}s) {res['error']}")
            reg[archivo] = {"ok": False, "book_id_viejo": book_id,
                            "error": res["error"]}
            fallidos += 1
        guardar_registro(reg)

    print(f"\n  subidos: {hechos} · fallidos: {fallidos}")
    print(f"  registro en {REGISTRO} — volver a lanzarlo continua donde iba.")
    if fallidos:
        print("  OJO: los fallidos se borraron y no se subieron. Vuelve a "
              "lanzarlo para reintentarlos.")


if __name__ == "__main__":
    main()
