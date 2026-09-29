#!/usr/bin/env python3
"""Enseña lo que hay GUARDADO en R2 para una parte de un libro.

Antes de reparar nada hay que ver qué se está leyendo de verdad. El extractor
de hoy puede estar perfecto y el texto guardado venir de uno de hace meses.

    python ver_parte.py 504691f6cf9e 100
    python ver_parte.py 504691f6cf9e 100 --lineas 40

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import os
import sys

BUCKET = (os.environ.get("R2_BUCKET_NAME") or "").strip() or "libris-audio"


def cliente():
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3.  Instálalo con:  pip install boto3")
    req = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")
    faltan = [v for v in req if not (os.environ.get(v) or "").strip()]
    if faltan:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltan))
    return boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT_URL"].strip(),
                        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                        region_name="auto")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("libro")
    p.add_argument("parte", type=int)
    p.add_argument("--lineas", type=int, default=25)
    a = p.parse_args()

    s3 = cliente()
    clave = f"{a.libro}/text/part_{a.parte}.txt"
    try:
        texto = s3.get_object(Bucket=BUCKET, Key=clave)["Body"].read().decode("utf-8")
    except Exception as e:
        sys.exit(f"No pude leer {clave}: {e}")

    lineas = texto.splitlines()
    print(f"{clave} · {len(texto)} caracteres · {len(lineas)} líneas\n")
    for i, l in enumerate(lineas[:a.lineas]):
        print(f"  {i:3d} | {l[:96]}")
    if len(lineas) > a.lineas:
        print(f"  … y {len(lineas) - a.lineas} líneas más")

    # Lo que delata una cabecera guardada: líneas cortas y sueltas repetidas,
    # y líneas de solo cifras.
    cortas = [l for l in lineas if 0 < len(l.strip()) <= 60
              and len(l.split()) <= 8]
    cifras = [l for l in lineas if l.strip().isdigit()]
    print(f"\n  líneas cortas sueltas: {len(cortas)}   ·   de solo cifras: {len(cifras)}")
    if cifras:
        print(f"  ejemplos de cifras sueltas: {', '.join(cifras[:8])}")


if __name__ == "__main__":
    main()
