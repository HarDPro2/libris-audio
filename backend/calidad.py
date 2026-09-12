"""Motor de calidad de texto — deteccion de errores de OCR.

POR QUE NO UN CORRECTOR NORMAL
------------------------------
Medido sobre 20 paginas escaneadas reales: un corrector ortografico corriente
marca el 53% de las palabras y propone barbaridades como "adoraban -> adorable"
o "anos -> ano". Destruiria el texto.

LOS TRES FILTROS
----------------
Un error de OCR tiene tres marcas A LA VEZ. Exigirlas todas separa la senal
del ruido:

  1. Es RARA en el libro (<= RARA_MAX usos). Un error de escaneo sale una o dos
     veces; una palabra de verdad se repite.
  2. Esta a UNA LETRA de una palabra FRECUENTE del mismo libro. El libro es su
     propio diccionario: asi se acierta con "Motecuhzoma", que no esta en
     ningun diccionario del mundo.
  3. NO es una palabra espanola valida, segun un diccionario CON MORFOLOGIA
     (hunspell). Esto es lo que salva "anos", "adoraban", "fiestas", "que",
     "eran", "hacia" de ser tocadas.

Medicion real, 20 paginas:
    874 palabras distintas -> 55 (filtros 1+2) -> 16 (los tres). 98% menos.

LO QUE ESTO NO PUEDE HACER, Y POR ESO EXISTE LA CAPA DE IA
----------------------------------------------------------
  a) Elegir bien el destino. Marca "dias -> dios" cuando deberia ser "dias".
     Solo el contexto de la frase lo resuelve.
  b) Ver errores SISTEMATICOS. En el libro medido, "carirulo" sale 80 veces y
     es, el mismo, un error de OCR de "capitulo". Como es frecuente, la
     frecuencia nunca lo delata. Una IA lo ve a la primera.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass, field

# Una palabra es "rara" con este numero de usos o menos.
RARA_MAX = 2
# Y "frecuente" con este numero o mas. El hueco entre ambos es deliberado:
# las palabras de frecuencia media no son ni una cosa ni la otra.
FRECUENTE_MIN = 5
# Minimo de letras para plantearse nada. Las palabras de 1-3 letras dan
# demasiados falsos positivos ("mes/mas", "por/par").
LARGO_MIN = 4

_PALABRA  = re.compile(r"[^\W\d_]+", re.UNICODE)
_ROMANO   = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)


@dataclass
class Candidata:
    """Una palabra sospechosa de ser un error de OCR."""
    palabra:      str
    usos:         int
    destino:      str          # la palabra frecuente a la que se parece
    usos_destino: int
    destino_valido: bool       # si el destino es espanol de verdad
    contextos:    list[str] = field(default_factory=list)

    @property
    def sistematico(self) -> bool:
        """El destino tampoco es espanol: el error afecta tambien a las
        {usos_destino} apariciones del destino. Es el caso mas rentable."""
        return not self.destino_valido


# ---------------------------------------------------------------------------
# Diccionario
# ---------------------------------------------------------------------------

class Diccionario:
    """Envoltorio sobre hunspell. Si no esta disponible, lo dice y no miente.

    Sin diccionario NO se puede filtrar: se devolveria basura. Por eso
    `disponible` es False y el motor se abstiene en vez de hacer estropicios.
    """

    # El primero es el que viaja DENTRO del repositorio (backend/diccionarios/).
    # Asi el motor funciona igual en Cloud Run, en Windows y en el portatil de
    # cualquiera, sin depender de que el sistema traiga hunspell instalado.
    # Los de /usr/share quedan como respaldo por si algun dia falta el nuestro.
    EMPAQUETADO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "diccionarios", "es_ES")
    RUTAS = (EMPAQUETADO,
             "/usr/share/hunspell/es_ES", "/usr/share/hunspell/es_MX",
             "/usr/share/myspell/es_ES")

    def __init__(self, ruta: str | None = None):
        self._dic = None
        self.ruta = None
        candidatas = [ruta] if ruta else list(self.RUTAS)
        for r in candidatas:
            if not r or not os.path.exists(r + ".dic"):
                continue
            try:
                from spylls.hunspell import Dictionary
                self._dic = Dictionary.from_files(r)
                self.ruta = r
                break
            except Exception:
                continue

    @property
    def disponible(self) -> bool:
        return self._dic is not None

    def existe(self, palabra: str) -> bool:
        if self._dic is None:
            return True          # sin diccionario, se asume valida: no se toca
        try:
            return bool(self._dic.lookup(palabra))
        except Exception:
            return True


# ---------------------------------------------------------------------------
# Distancia de edicion 1 — rapida, sin librerias
# ---------------------------------------------------------------------------

def a_una_letra(a: str, b: str) -> bool:
    """True si se pasa de `a` a `b` cambiando, quitando o anadiendo una letra."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    corta, larga = (a, b) if len(a) < len(b) else (b, a)
    i = j = saltos = 0
    while i < len(corta) and j < len(larga):
        if corta[i] != larga[j]:
            saltos += 1
            if saltos > 1:
                return False
            j += 1
        else:
            i += 1
            j += 1
    return True


# ---------------------------------------------------------------------------
# Los tres filtros
# ---------------------------------------------------------------------------

def frecuencias(textos: list[str]) -> Counter:
    c: Counter = Counter()
    for t in textos:
        for w in _PALABRA.findall(t):
            if len(w) >= LARGO_MIN:
                c[w.lower()] += 1
    return c


_FRASE = re.compile(r"[^.!?\n]+[.!?]?")


def contextos_de(textos: list[str], palabras: set[str],
                 cuantos: int = 2) -> dict[str, list[str]]:
    """Frases de ejemplo para MUCHAS palabras, en UNA sola pasada.

    Antes esto se hacia con una expresion regular por palabra sobre el libro
    entero: medido en un libro de 872 KB con 35 candidatas, 25,6 s de los 27 s
    que tardaba todo el motor. Recorriendo el texto una vez e indexando por
    palabra baja a decimas de segundo. Es lo que hace viable revisar al subir.
    """
    faltan = set(palabras)
    salida: dict[str, list[str]] = {w: [] for w in faltan}
    for t in textos:
        for m in _FRASE.finditer(t):
            if not faltan:
                return salida
            frase = m.group(0)
            presentes = {w.lower() for w in _PALABRA.findall(frase)} & faltan
            if not presentes:
                continue
            limpia = " ".join(frase.split())[:180]
            if not limpia:
                continue
            for w in presentes:
                salida[w].append(limpia)
                if len(salida[w]) >= cuantos:
                    faltan.discard(w)
    return salida


def _contexto(textos: list[str], palabra: str, cuantos: int = 2) -> list[str]:
    """Una sola palabra. Se conserva por comodidad en pruebas."""
    return contextos_de(textos, {palabra.lower()}, cuantos).get(palabra.lower(), [])


def detectar(textos: list[str], dic: Diccionario | None = None,
             con_contexto: bool = True) -> list[Candidata]:
    """Devuelve las palabras sospechosas de ser un error de OCR."""
    dic = dic or Diccionario()
    if not dic.disponible:
        return []          # sin diccionario no se arriesga nada

    frec = frecuencias(textos)
    raras      = [w for w, c in frec.items() if c <= RARA_MAX]
    frecuentes = [w for w, c in frec.items() if c >= FRECUENTE_MIN]

    salida: list[Candidata] = []
    for r in raras:
        if _ROMANO.match(r) or dic.existe(r):
            continue
        for f in frecuentes:
            if a_una_letra(r, f):
                salida.append(Candidata(
                    palabra=r, usos=frec[r],
                    destino=f, usos_destino=frec[f],
                    destino_valido=dic.existe(f),
                ))
                break

    # Los contextos, al final y de una sola pasada por el texto.
    if con_contexto and salida:
        ctx = contextos_de(textos, {c.palabra for c in salida})
        for c in salida:
            c.contextos = ctx.get(c.palabra, [])
    # Primero las sistematicas y las que mas ocurrencias arreglan
    salida.sort(key=lambda c: (not c.sistematico, -c.usos_destino))
    return salida


def resumen(cands: list[Candidata]) -> dict:
    sist = [c for c in cands if c.sistematico]
    return {
        "candidatas":   len(cands),
        "sistematicas": len(sist),
        "ocurrencias_en_juego": sum(c.usos + (c.usos_destino if c.sistematico else 0)
                                    for c in cands),
    }
