#!/usr/bin/env python3
"""Compara el texto de un libro con su respaldo: que cambio, exactamente.

Cada reparacion guarda el texto de antes en {book_id}/text_original/. Esto lo
pone al lado del actual y ensena SOLO lo que cambio, con su contexto. Es la
forma objetiva de comprobar una mejora sin escuchar el libro entero, y sobre
todo de cazar un destrozo que no hubieramos previsto.

    python comparar.py --libro 2a31e15dfebd                  # resumen y muestras
    python comparar.py --libro 2a31e15dfebd --parte 100      # una parte entera
    python comparar.py --libro 2a31e15dfebd --solo-sospechoso

Lo ultimo filtra los cambios que merecen un vistazo humano: los que ALARGAN
el texto o cambian algo que no es ni un guion ni una sigla.

No escribe nada nunca.
"""
import argparse
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reparar_libros import cliente_r2, listar_libros   # noqa: E402

PALABRA = re.compile(r"\S+")


def leer(s3, bucket, clave):
    try:
        return s3.get_object(Bucket=bucket, Key=clave)["Body"].read().decode("utf-8", "replace")
    except Exception:
        return None


def cambios(antes: str, ahora: str, contexto: int = 6):
    """(quitado, puesto, frase_antes, frase_ahora) por cada tramo que cambio."""
    a, b = PALABRA.findall(antes), PALABRA.findall(ahora)
    salida = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == "equal":
            continue
        ini_a, fin_a = max(0, i1 - contexto), min(len(a), i2 + contexto)
        ini_b, fin_b = max(0, j1 - contexto), min(len(b), j2 + contexto)
        salida.append((" ".join(a[i1:i2]), " ".join(b[j1:j2]),
                       " ".join(a[ini_a:fin_a]), " ".join(b[ini_b:fin_b])))
    return salida


# Una racha de palabras EN MAYUSCULAS es la cabecera de pagina.
_CABECERA = re.compile(r"\b[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ]+(?:\s+[A-ZÁÉÍÓÚÜÑ]"
                       r"[A-ZÁÉÍÓÚÜÑ]+)*\b")


def _letras(texto: str) -> str:
    return texto.replace("- ", "").replace(" ", "").lower()


def sospechoso(quitado: str, puesto: str) -> bool:
    """Un cambio que NO es de los que esperamos."""
    if len(puesto) > len(quitado):
        return True                       # el texto crecio: no lo hace ninguna
    if _letras(quitado) == _letras(puesto):
        return False                      # union de guion: mismas letras

    # Los dos arreglos a la vez: la cabecera habia caido DENTRO de la palabra
    # partida. Medido en "Los Mediums": 96 de los 681 cambios son de esta
    # clase, y son el mejor resultado posible, no un problema.
    #     "prac- EL LIBRO DE LOS MEDIUMS ticas"  ->  "practicas"
    sin_cabecera = _CABECERA.sub(" ", quitado)
    if _letras(sin_cabecera) == _letras(puesto):
        return False
    if not puesto.strip():
        return False                      # borrado limpio: basura

    # Borrado de palabras: lo que queda estaba ya, en el mismo orden. Es lo
    # que hace el limpiador de basura cuando el tramo que cambio arrastra
    # palabras de contexto.
    quedan, tenia = puesto.split(), quitado.split()
    i = 0
    for palabra in tenia:
        if i < len(quedan) and quedan[i] == palabra:
            i += 1
    if i == len(quedan) and len(quedan) < len(tenia):
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--libro", required=True)
    ap.add_argument("--parte", type=int)
    ap.add_argument("--muestras", type=int, default=15)
    ap.add_argument("--solo-sospechoso", action="store_true")
    args = ap.parse_args()

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")
    titulo = next((b.get("title") for b in listar_libros()
                   if b.get("book_id") == args.libro), "(?)")

    copias, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": f"{args.libro}/text_original/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        copias += [o["Key"] for o in r.get("Contents", []) if o["Key"].endswith(".txt")]
        if not r.get("IsTruncated"):
            break
        token = r.get("NextContinuationToken")
    if not copias:
        sys.exit("Ese libro no tiene respaldo: no se ha reparado nunca.")
    copias.sort(key=lambda k: int(re.search(r"part_(\d+)", k).group(1)))
    if args.parte is not None:
        copias = [k for k in copias if f"part_{args.parte}." in k]
        if not copias:
            sys.exit(f"La parte {args.parte} no tiene respaldo (no cambio).")

    print(f"{titulo}  ·  {len(copias)} partes con respaldo\n")

    total = crecidos = sospechosos = 0
    muestras, raros = [], []
    for clave in copias:
        n = int(re.search(r"part_(\d+)", clave).group(1))
        antes = leer(s3, bucket, clave)
        ahora = leer(s3, bucket, f"{args.libro}/text/part_{n}.txt")
        if antes is None or ahora is None:
            continue
        for quitado, puesto, ctx_a, ctx_b in cambios(antes, ahora):
            total += 1
            if len(puesto) > len(quitado):
                crecidos += 1
            if sospechoso(quitado, puesto):
                sospechosos += 1
                if len(raros) < args.muestras:
                    raros.append((n, quitado, puesto, ctx_a, ctx_b))
            elif len(muestras) < args.muestras:
                muestras.append((n, quitado, puesto))

    print(f"  cambios en total : {total}")
    print(f"  el texto crecio  : {crecidos}   (deberia ser 0)")
    print(f"  para mirar a ojo : {sospechosos}")

    if not args.solo_sospechoso and muestras:
        print("\nCAMBIOS NORMALES (union de guion o basura quitada):")
        for n, q, p in muestras:
            print(f"  parte {n:4}  «{q[:46]}»  ->  «{p[:46]}»")

    if raros:
        print("\nPARA MIRAR A OJO:")
        for n, q, p, ca, cb in raros:
            print(f"  parte {n}")
            print(f"     antes: ...{ca[:110]}...")
            print(f"     ahora: ...{cb[:110]}...")
    elif sospechosos == 0:
        print("\n  Ningun cambio raro: todo son uniones de guion y basura quitada.")


if __name__ == "__main__":
    main()
