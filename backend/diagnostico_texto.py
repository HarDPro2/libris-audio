#!/usr/bin/env python3
"""Mira el texto de un libro en R2 y cuenta CADA forma de palabra partida.

POR QUE
-------
"El libro de los espiritus" (Kardec) da 17 palabras partidas en 231 partes, y
sin embargo es el libro que se lee mal. O el problema no son los guiones, o el
corte tiene una forma que el patron de reparacion no reconoce. Antes de
prometer nada hay que mirar el texto.

    python diagnostico_texto.py --libro 2a31e15dfebd
    python diagnostico_texto.py --libro 2a31e15dfebd --parte 100 --ver

No escribe nada nunca. Solo lee y cuenta.
"""
import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guiones import mejor_separacion                  # noqa: E402
from reparar_libros import cliente_r2, listar_libros   # noqa: E402

# Cuantas veces tiene que salir un token raro para considerarlo basura de
# encabezado o pie de pagina, y no una palabra del libro.
MIN_APARICIONES_BASURA = 5
PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)

# Cada forma que puede tomar una palabra cortada, con nombre propio.
FORMAS = {
    "guion + espacio   (inge- nioso)":
        re.compile(r"[^\W\d_]{2,}-[ \t]+[a-záéíóúüñ][^\W\d_]*", re.UNICODE),
    "espacio + guion   (inge -nioso)":
        re.compile(r"[^\W\d_]{2,}[ \t]+-[a-záéíóúüñ][^\W\d_]*", re.UNICODE),
    "pegado            (inge-nioso)":
        re.compile(r"[^\W\d_]{2,}-[a-záéíóúüñ][^\W\d_]*", re.UNICODE),
    "guion al final de linea":
        re.compile(r"[^\W\d_]{2,}-\s*\n", re.UNICODE),
    "guion suelto entre espacios":
        re.compile(r"[^\W\d_]{2,}[ \t]+-[ \t]+[a-záéíóúüñ]", re.UNICODE),
    "raya de dialogo (— o –)":
        re.compile(r"[^\W\d_]{2,}[ \t]*[—–][ \t]*[a-záéíóúüñ]", re.UNICODE),
    "guion blando (caracter invisible)":
        re.compile("[^\\W\\d_]{2,}­[^\\W\\d_]+", re.UNICODE),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--libro", required=True)
    ap.add_argument("--parte", type=int, help="ensena esta parte entera")
    ap.add_argument("--ver", action="store_true", help="con --parte, la imprime")
    ap.add_argument("--ejemplos", type=int, default=8)
    ap.add_argument("--revision", action="store_true",
                    help="ensena el informe de calidad que dejo la subida")
    args = ap.parse_args()

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")
    titulo = next((b.get("title") for b in listar_libros()
                   if b.get("book_id") == args.libro), "(no esta en el catalogo)")

    claves, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": f"{args.libro}/text/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        claves += [o["Key"] for o in r.get("Contents", []) if o["Key"].endswith(".txt")]
        if not r.get("IsTruncated"):
            break
        token = r.get("NextContinuationToken")
    claves.sort(key=lambda k: int(re.search(r"part_(\d+)", k).group(1)))
    if not claves:
        sys.exit("Ese libro no tiene texto en R2.")

    print(f"{titulo}  ·  {len(claves)} partes\n")

    if args.revision:
        import json
        # Lo que la subida dejo escrito: que corrigio y que dejo pendiente.
        try:
            crudo = s3.get_object(Bucket=bucket,
                                  Key=f"{args.libro}/revision.json")["Body"].read()
            inf = json.loads(crudo)
        except Exception as e:
            sys.exit(f"Ese libro no tiene revision.json ({e}).\n"
                     "Los subidos antes del motor de calidad no lo tienen.")
        ia = inf.get("ia", {})
        print(f"  guiones unidos     : {inf.get('guiones_unidos', 0)}")
        print(f"  palabras sospechosas: {inf.get('candidatas', {})}")
        print(f"  segundos           : {inf.get('segundos')}")
        print(f"  IA ejecutada       : {ia.get('ejecutada')}"
              + (f"  ({ia.get('motivo_omitida')})" if not ia.get("ejecutada") else ""))
        for d in ia.get("aplicadas", [])[:20]:
            print(f"     corregido  {d['palabra']} -> {d['correcta']}"
                  f"  ({d['confianza']})")
        for d in ia.get("pendientes", [])[:20]:
            print(f"     pendiente  {d['palabra']} -> {d.get('propuesta')}"
                  f"  ({d.get('motivo')})")

        # Y comprobar que el original quedo guardado.
        originales = s3.list_objects_v2(Bucket=bucket,
                                        Prefix=f"{args.libro}/original/")
        archivos = [o["Key"] for o in originales.get("Contents", [])]
        if archivos:
            tam = originales["Contents"][0]["Size"] / 1048576
            print(f"\n  ARCHIVO ORIGINAL guardado: {archivos[0]}  ({tam:.1f} MB)")
            print("  -> este libro se puede reprocesar de cero cuando el "
                  "motor mejore.")
        else:
            print("\n  sin archivo original (subido antes de guardarlos)")
        return

    if args.parte is not None:
        clave = f"{args.libro}/text/part_{args.parte}.txt"
        texto = s3.get_object(Bucket=bucket, Key=clave)["Body"].read().decode("utf-8", "replace")
        print(f"--- {clave} · {len(texto)} caracteres ---")
        if args.ver:
            print(texto)
        print("\nrecuento en ESTA parte:")
        for nombre, patron in FORMAS.items():
            hallados = patron.findall(texto)
            if hallados:
                print(f"  {len(hallados):5}  {nombre}")
                for h in hallados[:args.ejemplos]:
                    print(f"           «{' '.join(h.split())}»")
        return

    totales = Counter()
    ejemplos = {nombre: [] for nombre in FORMAS}
    caracteres = 0
    for k in claves:
        t = s3.get_object(Bucket=bucket, Key=k)["Body"].read().decode("utf-8", "replace")
        caracteres += len(t)
        for nombre, patron in FORMAS.items():
            for m in patron.finditer(t):
                totales[nombre] += 1
                if len(ejemplos[nombre]) < args.ejemplos:
                    ejemplos[nombre].append(" ".join(m.group(0).split()))

    # --- basura repetida y palabras pegadas ---
    try:
        from calidad import Diccionario
        dic = Diccionario()
    except Exception:
        dic = None
    es_valida = ((lambda w: dic.existe(w) or dic.existe(w.lower()))
                 if dic and dic.disponible else None)

    print(f"{caracteres:,} caracteres en total\n")
    print("FORMAS DE PALABRA PARTIDA ENCONTRADAS:")
    for nombre in FORMAS:
        n = totales[nombre]
        marca = "  " if not n else ">>"
        print(f"{marca} {n:6}  {nombre}")
        for e in ejemplos[nombre]:
            print(f"             «{e}»")
    if not sum(totales.values()):
        print("\n  Ninguna. Si el libro se lee mal, el problema NO son los guiones.")

    if es_valida is None:
        print("\n(sin diccionario no puedo buscar basura ni palabras pegadas)")
        return

    # 1. BASURA REPETIDA — encabezados y pies que se colaron en el texto.
    #    Firma: no es palabra espanola, sale muchas veces, y casi siempre en
    #    mayusculas o como numero romano.
    frec = Counter()
    for k in claves:
        t = s3.get_object(Bucket=bucket, Key=k)["Body"].read().decode("utf-8", "replace")
        for w in PALABRA.findall(t):
            frec[w] += 1

    basura = [(w, n) for w, n in frec.items()
              if n >= MIN_APARICIONES_BASURA and len(w) <= 8
              and not es_valida(w)
              and (w.isupper() or re.fullmatch(r"[IVXLCDM]+", w, re.I))]
    basura.sort(key=lambda x: -x[1])
    print(f"\nBASURA REPETIDA (encabezados y pies dentro del texto): "
          f"{len(basura)} tokens, {sum(n for _, n in basura)} apariciones")
    for w, n in basura[:20]:
        print(f"  {n:6}  «{w}»")

    # 2. PALABRAS PEGADAS — falta el espacio. Se exige que las DOS mitades
    #    sean palabras espanolas de 2 letras o mas; si no, salen plurales
    #    partidos por la «s» y diminutivos destrozados.
    pegadas, vistas = [], set()
    for w, n in frec.items():
        if len(w) < 5 or es_valida(w) or w.lower() in vistas:
            continue
        corte = mejor_separacion(w, frec, es_valida)
        if corte:
            pegadas.append((w, f"{corte[0]} {corte[1]}", n))
            vistas.add(w.lower())
    pegadas.sort(key=lambda x: -x[2])
    print(f"\nPALABRAS PEGADAS (falta el espacio): {len(pegadas)} distintas, "
          f"{sum(n for _, _, n in pegadas)} apariciones")
    for w, arreglo, n in pegadas[:25]:
        print(f"  {n:6}  «{w}»  ->  «{arreglo}»")


if __name__ == "__main__":
    main()
