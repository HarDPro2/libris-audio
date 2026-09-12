"""Emparejar archivos del disco con fichas del catalogo.

POR QUE HACE FALTA
------------------
Los titulos del catalogo y los nombres de archivo no coinciden:

    "Ana Karenina Tolstoi Leon"   <->  Ana_Karenina-Tolstoi_Leon.pdf
    "charles bukowsky la senda"   <->  charles-bukowsky-la-senda-del-perdedor.pdf

Para volver a subir la biblioteca hay que saber que archivo corresponde a que
ficha, y sobre todo que archivos NO corresponden a ninguna. En la carpeta de
libros hay tambien extractos bancarios y apuntes: emparejar por catalogo es lo
que impide que acaben subidos a una biblioteca compartida.

COMO EMPAREJA
-------------
Sin tildes, sin puntuacion, todo en minusculas, y comparando CONJUNTOS de
palabras: gana la ficha que comparte mas palabras con el nombre del archivo,
siempre que comparta al menos la mitad de las del titulo.
"""
from __future__ import annotations

import re
import unicodedata

# Palabras que no distinguen nada: aparecen en medio titulo de la biblioteca.
VACIAS = {"de", "del", "la", "el", "los", "las", "y", "e", "o", "un", "una",
          "en", "al", "por", "para", "con", "sin", "a", "su", "libro", "pdf"}

# Cuanto del titulo tiene que aparecer en el nombre del archivo.
COBERTURA_MINIMA = 0.5


def normalizar(texto: str) -> list[str]:
    """Palabras significativas, sin tildes ni puntuacion."""
    sin_tilde = "".join(c for c in unicodedata.normalize("NFD", texto)
                        if unicodedata.category(c) != "Mn")
    palabras = re.split(r"[^0-9A-Za-z]+", sin_tilde.lower())
    return [p for p in palabras if p and p not in VACIAS and len(p) > 1]


def emparejar(archivos: list[str], fichas: list[dict]) -> tuple[dict, list, list]:
    """Devuelve (emparejados, archivos_sueltos, fichas_sin_archivo).

    `emparejados` es {nombre_de_archivo: ficha}. Cada ficha se usa una sola
    vez: si dos archivos apuntan a la misma, gana el que mas se parece y el
    otro queda suelto para que lo mires a mano.
    """
    tokens_ficha = {}
    for f in fichas:
        tokens_ficha[f["book_id"]] = set(normalizar(f.get("title") or ""))

    # Todas las parejas posibles con su puntuacion, de mejor a peor.
    parejas = []
    for a in archivos:
        ta = set(normalizar(a.rsplit(".", 1)[0]))
        for f in fichas:
            tf = tokens_ficha[f["book_id"]]
            if not tf:
                continue
            comunes = ta & tf
            cobertura = len(comunes) / len(tf)
            if cobertura < COBERTURA_MINIMA:
                continue
            # A igual cobertura, gana el archivo con menos palabras de sobra:
            # asi "Pedro-Paramo.pdf" no le roba la ficha a
            # "Juan Rulfo - Pedro Paramo.pdf".
            parejas.append((cobertura, -len(ta - tf), len(comunes), a,
                            f["book_id"]))

    # Ordena solo por los numeros y el nombre: dos fichas nunca se comparan
    # entre si (son diccionarios y no tienen orden).
    parejas.sort(key=lambda p: (p[0], p[1], p[2], p[3]), reverse=True)
    por_id = {f["book_id"]: f for f in fichas}
    emparejados, usadas = {}, set()
    for _, _, _, a, book_id in parejas:
        if a in emparejados or book_id in usadas:
            continue
        emparejados[a] = por_id[book_id]
        usadas.add(book_id)

    sueltos = [a for a in archivos if a not in emparejados]
    sin_archivo = [f for f in fichas if f["book_id"] not in usadas]
    return emparejados, sueltos, sin_archivo
