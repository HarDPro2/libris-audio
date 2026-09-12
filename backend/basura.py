"""Encabezados y pies de pagina incrustados dentro de las frases.

EL PROBLEMA, MEDIDO
-------------------
"El libro de los espiritus" (Kardec), 231 partes, 854.724 caracteres:
674 apariciones de 36 tokens de encabezado metidos a mitad de oracion.

    ...nadie se inquietaria por lo que RVC necesita, cuando aun no sabe hablar
    ...y afables, les LS—CVII profesan todo su afecto
    ...para perfeccionarse, RVC para mejorarse

Los mas repetidos: LS (123), LT (67), CII (38), CI (35), LC (33), CVI (31).
Son dos cosas pegadas: un CODIGO de obra (LS = Libro de los Espiritus) y el
numero de pagina en ROMANOS. El TTS los lee: "ele-ese ciento siete".

LA REGLA QUE LO HACE SEGURO
---------------------------
Un token sospechoso solo se borra si esta RODEADO DE MINUSCULAS: palabra en
minuscula antes y palabra en minuscula despues. Un encabezado que se cayo
dentro de una frase cumple eso siempre. Un romano legitimo, no:

    "CAPITULO II. De las leyes"     -> II va tras mayuscula: se queda
    "...el Libro II de la obra..."  -> igual: se queda
    "...les LS—CVII profesan..."    -> minusculas a los dos lados: fuera

Asi ni los numeros de capitulo ni los nombres en mayusculas corren peligro, y
no hace falta lista blanca de nada.
"""
from __future__ import annotations

import re
from collections import Counter

# Cuantas veces tiene que salir para considerarlo encabezado y no una palabra.
MIN_APARICIONES = 5
# Los ROMANOS sueltos piden mas. Un romano de numero de pagina sale en cada
# pagina: en "El libro de los espiritus" son CI(26), CII(29), CVI(24). Uno de
# referencia sale un puñado de veces: en "Los Mediums" son XII(5), VII(5),
# IV(7) — y ahi "el parrafo XII de la introduccion" es legitimo. El umbral
# separa los dos libros sin tocar nada mas.
MIN_APARICIONES_ROMANO = 10
# Un codigo de encabezado es una SIGLA CORTA: LS, LT, IEMC, PGF, RVC. Con el
# limite en 8 entraban "ALLAN" y "KARDEC" de la portada, que salen muchas
# veces, estan en mayusculas y no son palabras del diccionario — y el par
# "ALLAN KARDEC" se borraba entero. Los romanos si pueden ser mas largos
# (CVIII, CXII), asi que tienen su propio limite.
MAX_LARGO_SIGLA = 4
MAX_LARGO_ROMANO = 8

PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)

# Una cabecera puede ser una FRASE repetida, no una sigla. En "El libro de
# Los Mediums" la cabecera es el nombre del autor: ALLAN KARDEC sale 206
# veces y MEDIUMS 209. Token a token no hay forma de distinguir eso de la
# portada — y estrechar la regla para salvar la portada dejaba 621
# apariciones sin tocar. La senal buena es la SECUENCIA que se repite.
MIN_APARICIONES_CABECERA = 10
MAX_PALABRAS_CABECERA = 6
_RACHA_MAYUSCULAS = re.compile(
    r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ]+(?:[ \t]+[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ]+)+",
    re.UNICODE)
ROMANO = re.compile(r"^[IVXLCDM]+$")
_MINUSCULA = re.compile(r"[a-záéíóúüñ]", re.UNICODE)
_ALFA = re.compile(r"[^\W\d_]", re.UNICODE)
_ULTIMA_PALABRA = re.compile(r"([^\W\d_]+)[^\w]*$", re.UNICODE)
_PRIMERA_PALABRA = re.compile(r"^[^\w]*([^\W\d_]+)", re.UNICODE)
_FIN_FRASE = re.compile(r"[.!?»\n][^\w]*$")

# Palabras tras las que un numero romano es una REFERENCIA de verdad, no un
# encabezado caido. "el capitulo CVII" y "el Libro II" son legitimos; sin esta
# lista se borraban, porque "capitulo" y "Libro" acaban en minuscula.
REFERENCIAS = {
    "capitulo", "capítulo", "capitulos", "capítulos", "libro", "libros",
    "tomo", "tomos", "parte", "partes", "volumen", "volumenes", "volúmenes",
    "seccion", "sección", "articulo", "artículo", "numero", "número", "num",
    "pregunta", "preguntas", "item", "ley", "leyes", "pagina", "página",
    "vease", "véase", "ver", "nota", "notas", "apartado", "punto", "puntos",
    "cuestion", "cuestión", "siglo", "siglos", "epoca", "época", "tabla",
    "figura", "lamina", "lámina", "canto", "acto", "escena", "salmo",
    "version", "versión", "edicion", "edición",
    # De "Los Mediums": "el parrafo XII de la introduccion" se borraba.
    "parrafo", "párrafo", "parrafos", "párrafos", "inciso", "incisos",
    "apendice", "apéndice", "anexo", "leccion", "lección", "versiculo",
    "versículo", "verso", "versos", "estrofa", "cuadro", "titulo", "título",
    "grado", "grados", "regla", "reglas", "maxima", "máxima", "serie",
    "sesion", "sesión", "obra", "obras", "orden", "clase", "prefacio",
    "introduccion", "introducción",
}


def detectar_basura(frec: Counter, es_valida,
                    min_apariciones: int = MIN_APARICIONES) -> set[str]:
    """Tokens que parecen encabezado: en mayusculas o numero romano, no son
    palabras espanolas, y se repiten."""
    salida = set()
    for w, n in frec.items():
        if n < min_apariciones or es_valida(w):
            continue
        if ROMANO.match(w.upper()):
            if len(w) <= MAX_LARGO_ROMANO and n >= MIN_APARICIONES_ROMANO:
                salida.add(w)
        elif w.isupper() and len(w) <= MAX_LARGO_SIGLA:
            salida.add(w)
    return salida


def detectar_cabeceras(textos: list[str],
                       min_apariciones: int = MIN_APARICIONES_CABECERA
                       ) -> list[str]:
    """Secuencias de palabras EN MAYUSCULAS que se repiten por todo el libro.

    Son las cabeceras de pagina: "ALLAN KARDEC", "EL LIBRO DE LOS MEDIUMS".
    Se devuelven de la mas larga a la mas corta, para que al construir el
    patron gane siempre la mas completa.
    """
    cuenta: Counter = Counter()
    for t in textos:
        for m in _RACHA_MAYUSCULAS.finditer(t):
            racha = " ".join(m.group(0).split())
            if len(racha.split()) <= MAX_PALABRAS_CABECERA:
                cuenta[racha] += 1
    return sorted((r for r, n in cuenta.items() if n >= min_apariciones),
                  key=len, reverse=True)


def frecuencias(textos: list[str]) -> Counter:
    c: Counter = Counter()
    for t in textos:
        for w in PALABRA.findall(t):
            c[w] += 1
    return c


def _contexto_bueno_antes(texto: str, i: int) -> bool:
    """True si lo de delante es una palabra en minuscula que NO introduce una
    referencia. Es decir: si el token de delante parece texto corrido."""
    trozo = texto[max(0, i - 60):i]
    if _FIN_FRASE.search(trozo):
        return False                      # empieza frase: no es un encabezado
    m = _ULTIMA_PALABRA.search(trozo)
    if not m:
        return False
    palabra = m.group(1)
    if palabra[:1].isupper():
        return False                      # "el Libro II", "Vease II"
    if palabra.lower() in REFERENCIAS:
        return False                      # "el capitulo CVII"
    return bool(_MINUSCULA.match(palabra[:1]))


def _contexto_bueno_despues(texto: str, i: int) -> bool:
    trozo = texto[i:i + 60]
    if re.match(r"^[^\w]*[.!?«]", trozo):
        return False
    m = _PRIMERA_PALABRA.search(trozo)
    if not m:
        return False
    return bool(_MINUSCULA.match(m.group(1)[:1]))


def limpiar(texto: str, basura: set[str],
            registro: list | None = None,
            pares_siempre: bool = True) -> tuple[str, int]:
    """Quita los encabezados incrustados. Devuelve (texto, quitados).

    `pares_siempre`: la forma CODIGO—ROMANO ("LS—CVII", "LT—CVIII") se quita
    SIEMPRE, con punto delante o sin el. Un libro no cita asi — Kardec escribe
    "Vease el Libro de los Medios, capitulo..." —, esa forma solo la produce
    el encabezado de la pagina escaneada. Sin esto se quedaban todos los que
    caen justo detras de un punto, que el TTS lee igual.
    Los tokens SUELTOS siguen necesitando estar rodeados de minusculas.
    """
    if not basura:
        return texto, 0

    # El codigo puede venir solo ("RVC") o pegado al romano ("LS—CVII").
    alternativas = "|".join(sorted((re.escape(b) for b in basura),
                                   key=len, reverse=True))
    siglas = sorted((b for b in basura if not ROMANO.match(b.upper())),
                    key=len, reverse=True)
    romanos = sorted((b for b in basura if ROMANO.match(b.upper())),
                     key=len, reverse=True)
    alt_sigla = "|".join(re.escape(b) for b in siglas) or r"(?!x)x"
    alt_romano = "|".join(re.escape(b) for b in romanos) or r"(?!x)x"

    # El codigo puede venir solo ("RVC"), con guion ("LS—CVII") o con un
    # espacio en medio ("LS CVII"), y encadenado.
    patron = re.compile(
        rf"(?<![^\W\d_])(?:{alternativas})"
        rf"(?:(?:[ \t]*[—–-][ \t]*|[ \t]+)(?:{alternativas}))*"
        rf"(?![^\W\d_])", re.UNICODE)

    # EL par que se quita sin mirar el contexto es UNO solo: SIGLA + GUION +
    # ROMANO ("LS—CVII"). Esa forma solo la produce el encabezado.
    #
    # Antes valia cualquier pareja de tokens sospechosos separados por guion
    # O POR ESPACIO, y eso se llevaba por delante "ALLAN KARDEC" de la portada
    # y el "CAPITULO III II" de los titulos. Dos romanos seguidos, dos siglas
    # seguidas o cualquier cosa separada solo por un espacio vuelven a pasar
    # por la regla del contexto.
    _es_par = re.compile(rf"^(?:{alt_sigla})[ \t]*[—–-][ \t]*(?:{alt_romano})$",
                         re.UNICODE)

    quitados = 0
    trozos, ultimo = [], 0
    for m in patron.finditer(texto):
        par = bool(_es_par.match(m.group(0)))
        if not (pares_siempre and par):
            if not (_contexto_bueno_antes(texto, m.start())
                    and _contexto_bueno_despues(texto, m.end())):
                continue
        quitados += 1
        if registro is not None:
            ini = max(0, m.start() - 30)
            registro.append((m.group(0),
                             " ".join(texto[ini:m.end() + 30].split())))
        trozos.append(texto[ultimo:m.start()])
        ultimo = m.end()
    if not quitados:
        return texto, 0
    trozos.append(texto[ultimo:])
    # Los espacios y las comas que se quedan colgando al quitar el token.
    salida = "".join(trozos)
    salida = re.sub(r"[ \t]{2,}", " ", salida)
    salida = re.sub(r"[ \t]+([,;:.])", r"\1", salida)
    salida = re.sub(r"[ \t]+$", "", salida)          # el que quedo al final
    salida = re.sub(r"[ \t]+\n", "\n", salida)
    return salida, quitados


def limpiar_cabeceras(texto: str, cabeceras: list[str],
                      registro: list | None = None) -> tuple[str, int]:
    """Quita las cabeceras de pagina repetidas.

    Regla propia, distinta de la de los tokens sueltos: una secuencia que se
    repite 200 veces por el libro es cabecera SIEMPRE, caiga donde caiga —
    tambien detras de un punto, que es donde mas cae. Lo unico que la salva es
    que delante haya una palabra en MAYUSCULA, porque eso es la portada:

        "...para recibir. ALLAN KARDEC En este caso..."     -> fuera
        "COMPILADA POR ALLAN KARDEC Traduccion de Jose"     -> se queda
        "ALLAN KARDEC" al principio de una parte           -> se queda

    Esto ultimo puede dejar alguna cabecera suelta al principio de una parte,
    y es a proposito: ahi tambien empiezan los titulos de capitulo.
    """
    if not cabeceras:
        return texto, 0
    alternativas = "|".join(re.escape(c) for c in
                            sorted(cabeceras, key=len, reverse=True))
    patron = re.compile(rf"(?<![^\W\d_])(?:{alternativas})(?![^\W\d_])",
                        re.UNICODE)

    quitadas = 0
    trozos, ultimo = [], 0
    for m in patron.finditer(texto):
        anterior = _ULTIMA_PALABRA.search(texto[max(0, m.start() - 60):m.start()])
        if anterior is None or anterior.group(1)[:1].isupper():
            continue                      # portada, o principio de la parte
        quitadas += 1
        if registro is not None:
            ini = max(0, m.start() - 30)
            registro.append((m.group(0),
                             " ".join(texto[ini:m.end() + 30].split())))
        trozos.append(texto[ultimo:m.start()])
        ultimo = m.end()
    if not quitadas:
        return texto, 0
    trozos.append(texto[ultimo:])
    salida = "".join(trozos)
    salida = re.sub(r"[ \t]{2,}", " ", salida)
    salida = re.sub(r"[ \t]+([,;:.])", r"\1", salida)
    salida = re.sub(r"[ \t]+$", "", salida)
    salida = re.sub(r"[ \t]+\n", "\n", salida)
    return salida, quitadas
