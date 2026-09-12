"""Palabras cortadas por guion al final de linea.

EL PROBLEMA REAL
----------------
Los libros compuestos a maquina, y casi todo PDF maquetado o escaneado, parten
las palabras al llegar al margen:  "inge-" / "nioso".  Al unir las lineas con
un espacio quedaba "inge- nioso" y el TTS leia DOS palabras.

Medido sobre "El libro de los espiritus" (Kardec), parte 100 de 231:
12 palabras partidas en 3.200 caracteres. En el libro entero, ~2.700.

LO DELICADO NO ES UNIR, ES SABER CUANDO
---------------------------------------
  "inge-nioso"        -> pegar sin guion
  "teorico-practico"  -> pegar CONSERVANDO el guion
  "corporai- para"    -> NO pegar: el OCR ya rompio la palabra y "para" es
                         una palabra de verdad; pegarlas da "corporaipara"

Sin diccionario, la senal mas fiable es el propio documento: si "ingenioso"
aparece suelto en otra pagina, unir es correcto.

Este modulo no importa nada pesado a proposito (solo `re` y `collections`),
para que sus pruebas se puedan correr en cualquier maquina sin montar el
backend completo.
"""
from __future__ import annotations

import re
from collections import Counter

# Solo guion normal y guion blando. La raya (—) y el semirraya (–) son marcas
# de dialogo en espanol y NO se tocan jamas.
_GUIONES = "-­"

_FIN_CORTE = re.compile(rf"^(.*?)([^\W\d_]+)[{_GUIONES}]$", re.UNICODE)
_INI_CONT  = re.compile(r"^([^\W\d_]+)(.*)$", re.UNICODE)
_PALABRA   = re.compile(rf"[^\W\d_]+(?:[{_GUIONES}][^\W\d_]+)*", re.UNICODE)

# Salvaguarda contra el caso "corporai- para".
#
# Una continuacion de corte en espanol casi siempre es una silaba corta:
# -cia, -ter, -tos, -nes, -do, -de. Cuando la continuacion tiene 4 letras o
# mas Y ademas es una palabra que el documento usa suelta muchas veces, lo
# mas probable es que NO fuera un corte de palabra.
#
# El limite de 4 letras esta puesto justo por encima de las silabas: deja
# pasar "-cia", "-tos", "-nes" y "-de" (que si son cortes) y solo desconfia
# de continuaciones largas como "para".
MIN_LETRAS_SOSPECHA = 4
MIN_USOS_SOSPECHA   = 3


def vocabulario(paginas: list[str]) -> Counter:
    """Palabras que el propio documento usa, en minusculas y con su frecuencia.

    Se construye con las lineas COMPLETAS (las que no acaban en guion), que
    son las unicas que contienen palabras enteras fiables.
    """
    vocab: Counter = Counter()
    for pagina in paginas:
        for linea in pagina.splitlines():
            s = linea.strip()
            if not s or s[-1] in _GUIONES:
                continue
            for w in _PALABRA.findall(s):
                if len(w) > 2:
                    vocab[w.lower()] += 1
    return vocab


def decidir_union(izq: str, der: str, vocab: Counter) -> str | None:
    """Devuelve la palabra ya reunida, o None si no hay que unir."""
    junto    = izq + der
    guionado = izq + "-" + der
    hay_junto    = junto.lower() in vocab
    hay_guionado = guionado.lower() in vocab

    if hay_junto and not hay_guionado:
        return junto
    if hay_guionado and not hay_junto:
        return guionado

    if (not hay_junto
            and len(der) >= MIN_LETRAS_SOSPECHA
            and vocab.get(der.lower(), 0) >= MIN_USOS_SOSPECHA):
        return None      # continuacion sospechosa: mejor no tocar

    # Sin pistas: los cortes de linea son mucho mas frecuentes que los
    # compuestos con guion, asi que se une.
    return junto


def unir_palabras_cortadas(lineas: list[str], vocab: Counter) -> list[str]:
    """Une la ultima palabra de una linea con la primera de la siguiente
    cuando la primera acaba en guion de corte."""
    salida: list[str] = []
    i = 0
    while i < len(lineas):
        actual = lineas[i]
        # Puede encadenarse: una linea ya unida vuelve a acabar en guion.
        while i + 1 < len(lineas):
            m_izq = _FIN_CORTE.match(actual)
            if not m_izq:
                break
            m_der = _INI_CONT.match(lineas[i + 1])
            # La continuacion tiene que empezar en minuscula: si empieza en
            # mayuscula o en numero es otra cosa (titulo, item, nombre propio)
            # y el guion probablemente era un guion de verdad.
            if not m_der or not m_der.group(1)[:1].islower():
                break
            delante, izq = m_izq.group(1), m_izq.group(2)
            der, resto   = m_der.group(1), m_der.group(2)
            unida = decidir_union(izq, der, vocab)
            if unida is None:
                break
            actual = delante + unida + resto
            i += 1
        salida.append(actual)
        i += 1
    return salida


# ---------------------------------------------------------------------------
# Reparacion de texto YA guardado
#
# Los libros subidos antes de este arreglo tienen el texto guardado en R2 ya
# limpio: las lineas se unieron con espacios y los saltos desaparecieron. El
# corte quedo dentro del texto, como "carac- ter", y unir_palabras_cortadas()
# no sirve porque ya no hay lineas que unir.
#
# Ojo: en un PDF recien extraido, un "palabra- palabra" a media linea NO suele
# ser un corte, sino un inciso con raya mal codificada; por eso el extractor
# solo mira el final de linea. Aqui el contexto es otro — este texto viene de
# un pipeline que convirtio los saltos en espacios — asi que si es un corte.
# Aun asi se pasa por la misma decision, que es la que protege de los casos
# raros.
# ---------------------------------------------------------------------------

_CORTE_EN_TEXTO = re.compile(
    rf"([^\W\d_]+)[{_GUIONES}][ \t]+([a-záéíóúüñ][^\W\d_]*)", re.UNICODE
)


def reparar_texto_plano(texto: str, vocab: Counter) -> tuple[str, int]:
    """Repara cortes dentro de un texto ya unido. Devuelve (texto, arreglos)."""
    arreglos = 0

    def _sustituir(m):
        nonlocal arreglos
        unida = decidir_union(m.group(1), m.group(2), vocab)
        if unida is None:
            return m.group(0)          # se deja tal cual
        arreglos += 1
        return unida

    return _CORTE_EN_TEXTO.sub(_sustituir, texto), arreglos


def vocabulario_de_textos(textos: list[str]) -> Counter:
    """Vocabulario a partir de textos ya unidos (una sola linea cada uno).

    Se ignoran los fragmentos pegados a un guion, que son justo los rotos.
    """
    vocab: Counter = Counter()
    for t in textos:
        limpio = _CORTE_EN_TEXTO.sub(" ", t)
        for w in _PALABRA.findall(limpio):
            if len(w) > 2:
                vocab[w.lower()] += 1
    return vocab
