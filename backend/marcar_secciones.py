#!/usr/bin/env python3
"""Marca las secciones saltables en los libros YA subidos.

El detector corre al subir, así que los libros que entraron antes no tienen
secciones: narran el índice alfabético entero, la página de créditos y la
bibliografía, como siempre. Este script los pone al día.

ES BARATO, y conviene saber por qué: NO resintetiza nada y NO vuelve a subir
el texto. Solo lee las partes que ya están en R2, detecta las secciones y
añade dos claves al `index.json` de cada libro. Un libro de 300 partes se
arregla leyendo 300 archivos de texto y escribiendo uno.

SIMULA POR DEFECTO. No toca nada hasta que se le pasa --aplicar.

    python marcar_secciones.py                        # simula todos
    python marcar_secciones.py --libro 2a31e15dfebd   # simula uno
    python marcar_secciones.py --aplicar              # escribe
    python marcar_secciones.py --aplicar --borrar-audio

QUÉ HACE --borrar-audio
-----------------------
Las partes que ahora quedan marcadas como «no se narra» YA tienen su MP3
generado y pagado, ocupando sitio en R2 para siempre. Con esta opción se
borran, junto con sus tiempos de karaoke. No se regeneran: el motor devuelve
409 en cuanto ve la marca. Va aparte porque borrar es lo único que no se
deshace.

RESPALDO
--------
Antes de sobrescribir un `index.json` se guarda una copia en
`{book_id}/index_original.json`, y solo la primera vez, para que el original
no se pierda por volver a ejecutar.

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secciones import (detectar, marcar_prosa, repartir,          # noqa: E402
                       como_json)

# OJO: una variable PUESTA A VACIO no es lo mismo que una variable ausente, y
# `os.environ.get(x, defecto)` no distingue — con R2_BUCKET_NAME="" devuelve la
# cadena vacia, no el defecto, y el script iria a buscar a un bucket sin
# nombre. Pasa mas de lo que parece: basta una linea de PowerShell a la que se
# le olvido el valor.
BUCKET = (os.environ.get("R2_BUCKET_NAME") or "").strip() or "libris-audio"
_PARTE = re.compile(r"/text/part_(\d+)\.txt$")
# Cuantas partes se bajan a la vez. Dieciseis va sobrado para R2 y no hace
# falta tocarlo; se deja a mano por si alguna vez da problemas de cuota.
HILOS = 16


# ── Lo único que piensa: aislado a propósito, para poder probarlo ───────────
def analizar(trozos: list[str]) -> tuple[dict, list]:
    """De las partes de un libro a sus secciones. Sin red, sin R2, sin nada.

    El texto se reconstruye juntando las partes con un salto de línea. No es
    byte a byte el original —quien partió el libro hizo `.strip()` en cada
    trozo— pero da igual: todo lo que se calcula aquí se calcula sobre ESTE
    texto, así que las posiciones cuadran entre sí, que es lo que importa.
    """
    texto = "\n".join(trozos)
    secs = marcar_prosa(detectar(texto), texto)
    partes = repartir(texto, trozos, secs)
    return como_json(secs, partes), secs


# ── R2 ──────────────────────────────────────────────────────────────────────
def cliente_r2():
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3.  Instálalo con:  pip install boto3")

    requeridas = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")
    faltan = [v for v in requeridas
              if not (os.environ.get(v) or "").strip()]
    if faltan:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltan))
    ejemplo = [v for v in requeridas
               if os.environ[v].strip().strip("'\"") in ("...", "")
               or "<" in os.environ[v]
               or os.environ[v].strip().startswith("PEGA_AQUI")]
    if ejemplo:
        sys.exit("Estas variables tienen valores de ejemplo, no los reales: "
                 + ", ".join(ejemplo))
    ep = os.environ["R2_ENDPOINT_URL"].strip()
    if not ep.startswith("https://") or not ep.endswith(".r2.cloudflarestorage.com"):
        sys.exit("R2_ENDPOINT_URL no tiene la forma esperada.\n"
                 "  Esperado: https://<id-de-cuenta>.r2.cloudflarestorage.com\n"
                 f"  Recibido: {ep}")
    return boto3.client("s3", endpoint_url=ep,
                        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                        region_name="auto")


def _paginas(s3, **kw):
    token = None
    while True:
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        yield r
        if not r.get("IsTruncated"):
            return
        token = r.get("NextContinuationToken")


# En el bucket no todo lo que cuelga de la raiz es un libro: `music/` es la
# musica de fondo de la app.
NO_SON_LIBROS = {"music"}


def libros(s3) -> list[str]:
    """Los identificadores que hay en el bucket. Sin pasar por la API: esto
    tiene que poder correr aunque el backend esté caído."""
    salida = []
    for r in _paginas(s3, Bucket=BUCKET, Delimiter="/"):
        salida += [p["Prefix"].rstrip("/") for p in r.get("CommonPrefixes", [])]
    return sorted(x for x in salida if x not in NO_SON_LIBROS)


def claves(s3, prefijo: str) -> dict:
    """{clave: fecha de modificación}. La fecha es lo que permite saltarse un
    libro que ya está al día sin tener que bajar su texto entero."""
    salida = {}
    for r in _paginas(s3, Bucket=BUCKET, Prefix=prefijo):
        for o in r.get("Contents", []):
            salida[o["Key"]] = o.get("LastModified")
    return salida


def bajar(s3, clave: str) -> bytes:
    return s3.get_object(Bucket=BUCKET, Key=clave)["Body"].read()


def bajar_muchas(s3, claves_ordenadas: list[str]) -> list[str]:
    """Las partes de un libro, en paralelo y en orden.

    En serie, 97 libros son mas de doce mil descargas de una en una y la
    revision entera se iba a una hora. La red espera casi todo el tiempo, asi
    que esto es puro tiempo muerto: con dieciseis a la vez baja a minutos.
    El orden se conserva porque `map` devuelve en el orden de entrada.
    """
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=HILOS) as pool:
        return [b.decode("utf-8", "replace")
                for b in pool.map(lambda k: bajar(s3, k), claves_ordenadas)]


def subir(s3, clave: str, datos: bytes):
    s3.put_object(Bucket=BUCKET, Key=clave, Body=datos,
                  ContentType="application/json; charset=utf-8")


# ── Un libro ────────────────────────────────────────────────────────────────
def al_dia(s3, libro: str, todas: dict) -> bool:
    """Si este libro ya tiene sus secciones y su texto no ha cambiado desde.

    Sin esto, cada revisión vuelve a bajar el texto entero de los 97 libros
    aunque no haya cambiado nada. Con esto, la segunda pasada es instantánea:
    solo se miran los libros cuyo texto es MÁS NUEVO que su índice.
    """
    clave_indice = f"{libro}/index.json"
    fecha_indice = todas.get(clave_indice)
    if fecha_indice is None:
        return False
    try:
        indice = json.loads(bajar(s3, clave_indice).decode("utf-8"))
    except Exception:
        return False
    if "secciones" not in indice:
        return False
    for k, fecha in todas.items():
        if _PARTE.search(k) and fecha and fecha > fecha_indice:
            return False
    return True


def procesar(s3, libro: str, aplicar: bool, borrar_audio: bool,
             crear_indice: bool, rehacer: bool = False) -> dict:
    todas = claves(s3, f"{libro}/")
    if not rehacer and al_dia(s3, libro, todas):
        return {"libro": libro, "estado": "ya estaba al día"}
    partes = sorted(((int(m.group(1)), k) for k in todas
                     if (m := _PARTE.search(k))), key=lambda x: x[0])
    if not partes:
        return {"libro": libro, "estado": "sin texto"}

    # Los indices tienen que ser 0..n-1 sin huecos, o las posiciones que
    # calculemos no corresponden a las partes que pide la app.
    if [i for i, _ in partes] != list(range(len(partes))):
        return {"libro": libro, "estado": "partes con huecos",
                "detalle": f"{len(partes)} partes, la última es "
                           f"{partes[-1][0]}"}

    trozos = bajar_muchas(s3, [k for _, k in partes])
    datos, secs = analizar(trozos)
    marcadas = len(datos["partes"])
    sin_audio = sum(1 for v in datos["partes"].values() if not v["sintetizar"])

    tiene_indice = f"{libro}/index.json" in todas
    if not tiene_indice and not crear_indice:
        return {"libro": libro, "estado": "sin index.json",
                "secciones": secs, "marcadas": marcadas,
                "sin_audio": sin_audio, "total": len(trozos)}

    borrables = []
    if borrar_audio:
        sin_narrar = {i for i, v in datos["partes"].items()
                      if not v["sintetizar"]}
        borrables = [k for k in todas
                     if (m := re.search(r"/(?:audio|timing)/part_(\d+)_", k))
                     and m.group(1) in sin_narrar]

    if aplicar:
        indice = {}
        if tiene_indice:
            crudo = bajar(s3, f"{libro}/index.json")
            try:
                indice = json.loads(crudo.decode("utf-8"))
            except Exception:
                indice = {}
            if f"{libro}/index_original.json" not in todas:
                subir(s3, f"{libro}/index_original.json", crudo)
        indice.update(datos)
        subir(s3, f"{libro}/index.json",
              json.dumps(indice, ensure_ascii=False).encode("utf-8"))
        for k in borrables:
            s3.delete_object(Bucket=BUCKET, Key=k)

    # «Mirado y no hay nada» TAMBIEN es un resultado, y hay que guardarlo.
    #
    # Antes se salia aqui sin escribir, y el efecto era que los 80 libros sin
    # secciones —el grueso del catalogo— no quedaban marcados como revisados
    # y se bajaban ENTEROS en cada pasada. De ahi venia la hora. Ahora se les
    # escribe `secciones: []`, que es la verdad, y `al_dia` los reconoce.
    if not secs:
        return {"libro": libro, "estado": "nada que marcar",
                "total": len(trozos)}

    return {"libro": libro, "estado": "aplicado" if aplicar else "simulado",
            "secciones": secs, "marcadas": marcadas, "sin_audio": sin_audio,
            "total": len(trozos), "borrables": len(borrables),
            "creado": not tiene_indice}


def detallar(trozos: list[str]) -> None:
    """Enseña en qué se fijó el detector, para poder discutir un «nada que marcar».

    Que un libro no tenga secciones puede ser la respuesta correcta —una novela
    no tiene índice— o puede ser que el detector se esté quedando corto. La
    diferencia no se adivina mirando el resultado: hay que ver las medidas.
    """
    from secciones import (_es_linea_de_lista, _densidad_referencias,
                           _SENAS_CREDITOS, _CABECERAS, RACHA_MINIMA,
                           ZONA_CREDITOS)
    texto = "\n".join(trozos)
    lineas = texto.splitlines()
    total = len(lineas)
    print(f"\n  {total} líneas, {len(trozos)} partes")

    tope = max(6, int(total * ZONA_CREDITOS))
    senas = [(i, l.strip()[:60]) for i, l in enumerate(lineas[:tope])
             if any(x in l.lower() for x in _SENAS_CREDITOS)]
    print(f"  señas de créditos en las primeras {tope} líneas: {len(senas)}"
          f"   (hacen falta 2 juntas)")
    for i, l in senas[:5]:
        print(f"      línea {i}: {l}")

    cabeceras = [(i, l.strip()[:40], c) for i, l in enumerate(lineas)
                 for c, pat in _CABECERAS if pat.match(l.strip())]
    print(f"  cabeceras encontradas: {len(cabeceras)}")
    for i, l, c in cabeceras[:8]:
        print(f"      línea {i} ({i / total:.0%} del libro)  {c:12s} «{l}»")

    racha = mejor = fin = 0
    for i, l in enumerate(lineas):
        if _es_linea_de_lista(l):
            racha += 1
            if racha > mejor:
                mejor, fin = racha, i
        else:
            racha = 0
    print(f"  racha más larga con forma de lista: {mejor} líneas"
          f"  (hacen falta {RACHA_MINIMA})")
    if mejor:
        print(f"      acaba en la línea {fin} ({fin / total:.0%} del libro)")
        for l in lineas[max(0, fin - mejor + 1):fin + 1][:4]:
            print(f"      {_densidad_referencias(l):.2f} | {l.strip()[:66]}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--libro", help="solo este identificador")
    p.add_argument("--aplicar", action="store_true",
                   help="escribe de verdad (por defecto solo simula)")
    p.add_argument("--borrar-audio", action="store_true",
                   help="borra el MP3 ya generado de las partes que no se narran")
    p.add_argument("--crear-indice", action="store_true",
                   help="crea el index.json en los libros que no lo tengan")
    p.add_argument("--rehacer", action="store_true",
                   help="no saltarse los libros que ya están al día")
    p.add_argument("--detalle", action="store_true",
                   help="con --libro: enseña en qué se fijó el detector")
    args = p.parse_args()

    s3 = cliente_r2()
    lista = [args.libro] if args.libro else libros(s3)
    if not lista:
        sys.exit("No hay libros en el bucket.")

    print(f"{'SIMULACIÓN' if not args.aplicar else 'APLICANDO'} · "
          f"{len(lista)} libro(s) · bucket {BUCKET}\n")

    if args.detalle:
        if not args.libro:
            sys.exit("--detalle necesita --libro.")
        todas = claves(s3, f"{args.libro}/")
        partes = sorted(((int(m.group(1)), k) for k in todas
                         if (m := _PARTE.search(k))), key=lambda x: x[0])
        if not partes:
            sys.exit("Ese libro no tiene texto en R2.")
        detallar(bajar_muchas(s3, [k for _, k in partes]))
        return

    resumen = {}
    total_sin_audio = total_partes = total_borrables = total_boton = 0
    for libro in lista:
        try:
            r = procesar(s3, libro, args.aplicar, args.borrar_audio,
                         args.crear_indice, args.rehacer)
        except Exception as e:
            print(f"  {libro}  ERROR  {type(e).__name__}: {e}")
            resumen["error"] = resumen.get("error", 0) + 1
            continue
        resumen[r["estado"]] = resumen.get(r["estado"], 0) + 1
        if not r.get("secciones"):
            print(f"  {libro}  {r['estado']}"
                  + (f"  ({r.get('total', '?')} partes)" if r.get("total") else ""))
            continue
        total_sin_audio += r["sin_audio"]
        total_boton += r["marcadas"]
        total_partes += r["total"]
        total_borrables += r.get("borrables", 0)
        detalle = ", ".join(f"{s.clase}({'audio' if s.sintetizar else 'sin audio'})"
                            for s in r["secciones"])
        # Se enseñan los DOS numeros: las partes que dejan de sintetizarse y
        # las que ganan boton. No son lo mismo — una bibliografia en prosa se
        # sigue narrando y aun asi lleva su «Saltar bibliografia»— y enseñar
        # solo el primero hacia parecer que esos libros no ganaban nada.
        print(f"  {libro}  {r['sin_audio']:3d} sin narrar · "
              f"{r['marcadas']:3d} con botón  de {r['total']:<4d}"
              f"  ·  {detalle}")
        if r.get("borrables"):
            print(f"               {r['borrables']} archivos de audio "
                  + ("BORRADOS" if (args.aplicar and args.borrar_audio)
                     else "que se pueden borrar (--aplicar --borrar-audio)"))

    print("\n" + "=" * 60)
    for estado, n in sorted(resumen.items()):
        print(f"  {estado:22s} {n}")
    if total_partes:
        print(f"\n  {total_boton} partes ganan botón de salto, y de ellas "
              f"{total_sin_audio} dejan además de sintetizarse.")
        print(f"  (de las {total_partes} partes de los libros con secciones)")
    if total_borrables:
        if args.aplicar and args.borrar_audio:
            print(f"  {total_borrables} archivos de audio viejos BORRADOS")
        else:
            print(f"  {total_borrables} archivos de audio viejos se pueden "
                  f"borrar  (--aplicar --borrar-audio)")
    if not args.aplicar:
        print("\n  No se ha escrito nada. Para hacerlo: --aplicar")


if __name__ == "__main__":
    main()
