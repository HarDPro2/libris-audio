#!/usr/bin/env python3
"""Repara las palabras partidas por guion en los libros YA subidos.

Los libros que entraron antes del arreglo tienen el texto guardado en R2 con
las palabras cortadas ("carac- ter"), y el audio se genero a partir de ese
texto. Arreglar solo el texto no basta: el MP3 cacheado seguiria diciendo
"carac" y "ter" por separado. Por eso este script tambien borra el audio y los
tiempos de karaoke de las partes que cambien, para que se regeneren solos la
proxima vez que alguien las escuche.

SIMULA POR DEFECTO. No toca nada hasta que se le pasa --aplicar.

    python reparar_libros.py                      # simula todos los libros
    python reparar_libros.py --libro 2a31e15dfebd # simula uno
    python reparar_libros.py --libro 2a31e15dfebd --aplicar

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guiones import reparar_texto_plano, vocabulario_de_textos   # noqa: E402

API = os.environ.get(
    "LIBRIS_API",
    "https://libris-audio-backend-856706599879.us-west1.run.app",
).rstrip("/")

PAT_ROTA = re.compile(r"[^\W\d_]+-\s+[a-záéíóúüñ]+", re.UNICODE)


# ── Comprobaciones antes de tocar nada ──────────────────────────────────────
def cliente_r2():
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3.  Instalalo con:  pip install boto3")

    requeridas = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")
    faltan = [v for v in requeridas if not os.environ.get(v)]
    if faltan:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltan))

    ejemplo = [v for v in requeridas
               if os.environ[v].strip() in ("...", "") or "<" in os.environ[v]]
    if ejemplo:
        sys.exit(
            "Estas variables tienen valores de ejemplo, no los reales: "
            + ", ".join(ejemplo)
            + "\nSacalos de Cloud Run:\n"
            "    gcloud run services describe libris-backend --region us-central1 "
            "--format=\"value(spec.template.spec.containers[0].env)\""
        )

    ep = os.environ["R2_ENDPOINT_URL"].strip()
    if not ep.startswith("https://") or not ep.endswith(".r2.cloudflarestorage.com"):
        sys.exit("R2_ENDPOINT_URL no tiene la forma esperada.\n"
                 "  Esperado: https://<id-de-cuenta>.r2.cloudflarestorage.com\n"
                 f"  Recibido: {ep}")

    return boto3.client(
        "s3",
        endpoint_url=ep,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def listar_libros():
    import urllib.request, json
    with urllib.request.urlopen(f"{API}/api/books", timeout=60) as r:
        return json.load(r)


def claves(s3, bucket, prefijo):
    salida, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefijo}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        salida += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return salida
        token = r.get("NextContinuationToken")


def procesar(s3, bucket, libro, aplicar, ver_ejemplos):
    book_id = libro.get("book_id")
    titulo  = (libro.get("title") or "")[:44]
    if not book_id:
        return 0, 0, 0

    partes = sorted(
        (k for k in claves(s3, bucket, f"{book_id}/text/") if k.endswith(".txt")),
        key=lambda k: int(re.search(r"part_(\d+)", k).group(1)),
    )
    if not partes:
        print(f"  --  {titulo:46} sin texto en R2")
        return 0, 0, 0

    # El vocabulario se construye con el LIBRO ENTERO: cuantas mas paginas,
    # mejores decisiones. Con una sola parte se decide casi a ciegas.
    textos = []
    for k in partes:
        textos.append(s3.get_object(Bucket=bucket, Key=k)["Body"].read().decode("utf-8", "replace"))
    vocab = vocabulario_de_textos(textos)

    rotas_antes = sum(len(PAT_ROTA.findall(t)) for t in textos)
    cambiadas, arreglos_total, ejemplos = [], 0, []

    for k, t in zip(partes, textos):
        nuevo, n = reparar_texto_plano(t, vocab)
        if n:
            arreglos_total += n
            cambiadas.append((k, nuevo))
            if len(ejemplos) < 6:
                for m in list(PAT_ROTA.finditer(t))[:2]:
                    frag = m.group(0)
                    izq = frag.split("-")[0]
                    d = re.search(re.escape(izq) + r"-?[a-záéíóúüñ]*", nuevo)
                    ejemplos.append((frag, d.group(0) if d else "?"))

    restos = sum(len(PAT_ROTA.findall(n)) for _, n in cambiadas)
    marca = "OK " if arreglos_total else "-- "
    print(f"  {marca} {titulo:46} {len(partes):4} partes · "
          f"{rotas_antes:5} partidas · {arreglos_total:5} arregladas · "
          f"{len(cambiadas):4} partes a reescribir")
    if ver_ejemplos and ejemplos:
        for a, b in ejemplos[:6]:
            print(f"        «{a}»  ->  «{b}»")
    if restos:
        print(f"        (la salvaguarda dejo {restos} sin tocar a proposito)")

    if not aplicar or not cambiadas:
        return rotas_antes, arreglos_total, 0

    # 1) Texto corregido
    for k, nuevo in cambiadas:
        s3.put_object(Bucket=bucket, Key=k, Body=nuevo.encode("utf-8"),
                      ContentType="text/plain; charset=utf-8")

    # 2) Audio y tiempos de karaoke de las partes que cambiaron.
    #    Se generaron a partir del texto roto, asi que ya no valen. Borrarlos
    #    hace que se regeneren solos la proxima vez que alguien escuche.
    indices = {int(re.search(r"part_(\d+)", k).group(1)) for k, _ in cambiadas}
    borrados = 0
    for prefijo in (f"{book_id}/audio/", f"{book_id}/timing/"):
        for k in claves(s3, bucket, prefijo):
            m = re.search(r"part_(\d+)", k)
            if m and int(m.group(1)) in indices:
                s3.delete_object(Bucket=bucket, Key=k)
                borrados += 1
    print(f"        aplicado: {len(cambiadas)} partes reescritas · "
          f"{borrados} archivos de audio/karaoke invalidados")
    return rotas_antes, arreglos_total, borrados


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--libro", help="book_id concreto; si falta, todos")
    ap.add_argument("--aplicar", action="store_true", help="escribe de verdad")
    ap.add_argument("--sin-ejemplos", action="store_true")
    args = ap.parse_args()

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")

    libros = listar_libros()
    if args.libro:
        libros = [l for l in libros if l.get("book_id") == args.libro]
        if not libros:
            sys.exit(f"No encuentro el libro {args.libro} en {API}/api/books")

    print(f"{len(libros)} libro(s) · bucket {bucket} · "
          f"{'APLICANDO CAMBIOS' if args.aplicar else 'SIMULACION'}\n")

    tot_rotas = tot_arreglos = tot_borrados = 0
    for l in libros:
        try:
            a, b, c = procesar(s3, bucket, l, args.aplicar, not args.sin_ejemplos)
            tot_rotas += a; tot_arreglos += b; tot_borrados += c
        except Exception as e:
            print(f"  !!  {(l.get('title') or '')[:46]:46} error: {e}")

    print(f"\n  palabras partidas encontradas : {tot_rotas}")
    print(f"  palabras reunidas             : {tot_arreglos}")
    if args.aplicar:
        print(f"  audio/karaoke invalidado      : {tot_borrados} archivos")
        print("\nHecho. El audio se regenera solo la proxima vez que se escuche.")
    else:
        print("\n[SIMULACION] No se escribio nada. Revisa los ejemplos de arriba.")
        print("Si estan bien:  python reparar_libros.py --aplicar")


if __name__ == "__main__":
    main()
