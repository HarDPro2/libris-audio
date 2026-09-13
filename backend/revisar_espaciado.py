#!/usr/bin/env python3
"""Busca en el catalogo los libros con el texto destrozado por el espaciado.

EL PROBLEMA, Y COMO SE DESCUBRIO
--------------------------------
PyMuPDF 1.24.1 —la version que fija `requirements.txt` y que corre en Cloud
Run— no sabe leer el espaciado de ciertas fuentes y devuelve las letras
separadas una por una:

    d ín a br e su s pé t a l o s pa r a a r o ma r e l a ir e

Salio midiendo el corpus de Quantum Text Codex contra pypdfium2: un libro de
792 paginas de poesia tenia el 74,8% de sus "palabras" de una sola letra. Con
PyMuPDF 1.27 el mismo libro sale perfecto, asi que es un fallo suyo ya
corregido aguas arriba.

Pero los libros que se subieron con la version vieja tienen ESE texto guardado
en R2, y el audio se genero a partir de el. El TTS los lee letra por letra.

QUE HACE ESTE SCRIPT
--------------------
Recorre el catalogo, baja una muestra del texto de cada libro y cuenta que
porcentaje de sus palabras son de UNA sola letra. En espanol de verdad eso
ronda el 2-4% («a», «y», «o», «e»); el 10% ya es un libro con muchas
iniciales. Por encima del 25% no hay duda: esta roto.

NO TOCA NADA. Solo mira y avisa. Arreglar un libro roto es resubirlo con la
version nueva de PyMuPDF, que es lo unico que lo cura.

    python revisar_espaciado.py               # todo el catalogo
    python revisar_espaciado.py --partes 5    # mas muestra por libro

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reparar_libros import (claves, cliente_r2, listar_libros,   # noqa: E402
                            _num)

# Por encima de esto no hay duda: el texto esta roto.
ROTO = 25.0
# Entre este y el anterior, conviene mirarlo a ojo.
SOSPECHOSO = 10.0


def letras_sueltas(texto: str) -> float:
    piezas = texto.split()
    if len(piezas) < 100:
        return 0.0
    return 100.0 * sum(1 for w in piezas if len(w) == 1) / len(piezas)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--partes", type=int, default=3,
                   help="Cuantas partes bajar por libro (por defecto 3).")
    p.add_argument("--libro", help="Revisar solo este book_id.")
    a = p.parse_args()

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME", "libris-audio")

    libros = listar_libros()
    if a.libro:
        libros = [l for l in libros if l.get("id") == a.libro]
        if not libros:
            print(f"No hay ningun libro con id {a.libro}")
            return 1

    print(f"{len(libros)} libros en el catalogo\n")
    rotos, sospechosos, vacios = [], [], []

    for libro in libros:
        bid = libro.get("id")
        titulo = (libro.get("title") or bid)[:52]
        try:
            partes = sorted((k for k in claves(s3, bucket, f"{bid}/text/")
                             if k.endswith(".txt")), key=_num)
        except Exception as e:
            print(f"  !! {titulo:52s} no se pudo listar: {e}")
            continue
        if not partes:
            vacios.append(titulo)
            continue

        # Del centro del libro, que es donde esta el cuerpo: el principio
        # suele ser portada y creditos.
        medio = len(partes) // 2
        elegidas = partes[medio:medio + a.partes] or partes[:a.partes]
        trozos = []
        for k in elegidas:
            try:
                trozos.append(s3.get_object(Bucket=bucket, Key=k)["Body"]
                              .read().decode("utf-8", "ignore"))
            except Exception:
                pass
        if not trozos:
            vacios.append(titulo)
            continue

        pct = letras_sueltas("\n".join(trozos))
        if pct >= ROTO:
            rotos.append((titulo, bid, pct, len(partes)))
            print(f"  ROTO      {titulo:52s} {pct:5.1f}%  ({len(partes)} partes)")
        elif pct >= SOSPECHOSO:
            sospechosos.append((titulo, bid, pct))
            print(f"  ¿?        {titulo:52s} {pct:5.1f}%")
        else:
            print(f"  bien      {titulo:52s} {pct:5.1f}%")

    print("\n" + "=" * 68)
    if vacios:
        print(f"{len(vacios)} libros sin texto en R2 (nunca se proceso)")
    if not rotos and not sospechosos:
        print("Ningun libro con el texto destrozado. No hay nada que resubir.")
        return 0
    if rotos:
        print(f"\n{len(rotos)} LIBROS ROTOS — hay que resubirlos con PyMuPDF "
              f"nuevo:\n")
        for titulo, bid, pct, n in rotos:
            print(f"  {titulo:52s} {pct:5.1f}%  id={bid}")
        print("\nResubirlos es lo unico que los cura: el texto de R2 ya nacio\n"
              "asi y no se puede reconstruir desde el. Borra el libro en la\n"
              "app y vuelve a subir el PDF con el backend ya actualizado.")
    if sospechosos:
        print(f"\n{len(sospechosos)} para mirar a ojo (entre "
              f"{SOSPECHOSO:.0f}% y {ROTO:.0f}%):\n")
        for titulo, bid, pct in sospechosos:
            print(f"  {titulo:52s} {pct:5.1f}%  id={bid}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
