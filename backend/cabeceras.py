"""Las cabeceras de página, que el TTS lee en cada hoja.

EL PROBLEMA, TAL COMO LO CONTÓ HARD P.: «me lee los encabezados, tanto de la
introducción como de cada capítulo, y cada hoja lee de nuevo». En «El libro de
los espíritus» las cabeceras alternan par/impar, como en cualquier libro
impreso, y debajo va el número de página:

    Libro Segundo – Capítulo VI        ← cabecera (páginas pares)
    192                                ← número de página
    [224a] – ¿Cuánto pueden durar…     ← el texto de verdad

    Vida Espírita                      ← cabecera (páginas impares)
    193
    didos del cuerpo material y en espera…

Leído en voz alta, eso es «Libro Segundo, Capítulo Sexto. Ciento noventa y
dos.» cada vez que pasa una hoja, o sea cada minuto y medio de audio.

POR QUÉ NO BASTA LO QUE YA HABÍA
--------------------------------
`basura.detectar_cabeceras` caza rachas en MAYÚSCULAS —«ALLAN KARDEC»— y estas
van en Mayúscula Inicial, así que no las ve. Y el filtro geométrico del
extractor (descartar lo que cae en el 6% de arriba o de abajo de la página) no
llega: estas cabeceras están DENTRO de esa banda.

LA SEÑAL, Y POR QUÉ NO ES «SE REPITE MUCHO»
-------------------------------------------
Lo primero que uno intenta —borrar la línea corta que se repite— destroza una
obra de teatro. Medido sobre los libros de prueba:

    MEDEA  88x    JASÓN  39x    EGEO  27x    EL CORO  26x

Son los nombres de los personajes antes de cada parlamento. Borrarlos deja al
oyente sin saber quién habla. Y en «1984», «—Sí.» sale 17 veces.

Lo que de verdad separa una cabecera de un nombre de personaje es DÓNDE CAE:

                        en el borde de la página   veces en la misma página
    cabeceras                   95 – 100 %                    1
    personajes de Medea         15 –  33 %                  4 – 7
    diálogo de «1984»               24 %                      5

Sin una sola zona gris, y con el umbral en el 85% queda margen de sobra por los
dos lados. Una cabecera está arriba (o abajo) de TODAS las páginas donde sale,
y nunca dos veces en la misma; un personaje aparece a media página y varias
veces seguidas.

Esto necesita saber dónde acaba cada página, así que corre EN LA EXTRACCIÓN,
mientras esa información existe. Una vez que el texto se guarda como un solo
bloque, ya no se puede distinguir.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# Cuántas líneas cuentan como «el borde» por arriba y por abajo.
ZONA = 3
# En menos páginas que esto no hay evidencia suficiente. Un libro de veinte
# páginas con una cabecera no merece el riesgo.
MIN_PAGINAS = 8
# La proporción de apariciones que tienen que caer en el borde. Ver la tabla
# de arriba: las cabeceras están en el 95-100%, lo demás por debajo del 33%.
BORDE_MINIMO = 0.85
# Una cabecera es corta. El pie de «1984» —«www.philosophia.cl / Escuela de
# Filosofía Universidad ARCIS»— es de los largos y son 7 palabras.
MAX_CARACTERES = 80
MAX_PALABRAS = 10
# Una pagina tiene que ser mas larga que las dos zonas juntas, o «el borde» no
# significa nada: en una pagina de cinco lineas con ZONA=3, todo es borde y
# cualquier cosa repetida pasaria por cabecera. Las paginas de un libro de
# verdad tienen treinta o cuarenta lineas; las cortas son aperturas de capitulo
# o paginas casi en blanco, y perderles la cabecera no cuesta nada.
MIN_LINEAS_PAGINA = 2 * ZONA + 1

# EL NUMERO DE PAGINA DETRAS: la señal que no se puede falsificar.
#
# Medido sobre «El libro de los espiritus» (Kardec), cabecera «Creacion», sus
# nueve apariciones:
#
#     pag 91, 93, 95, 97, 99  -> linea 0, y detras '91', '93', '95'...  CABECERA
#     pag 89                  -> linea 3, detras 'Formacion de los mundos'  portadilla
#     pag 71                  -> linea 7, entre '• Capitulo III' y '• Capitulo IV'  sumario
#     pag 5                   -> dentro de 'Capitulo III – Creacion'  indice
#
# Solo cinco son cabecera, y el minimo de ocho paginas las dejaba fuera: el
# titulo de un capitulo hace de cabecera SOLO dentro de su capitulo, y solo en
# las impares. Un capitulo corto nunca llega a ocho.
#
# Pero esas cinco llevan el numero de pagina pegado detras, y ninguna de las
# otras cuatro lo lleva. Esa señal es tan limpia que no hace falta exigir ocho
# paginas: con cuatro basta, porque una portadilla, un sumario o una entrada de
# indice no tienen un numero suelto justo debajo.
MIN_PAGINAS_CON_NUMERO = 4
_NUMERO_DE_PAGINA = re.compile(r"^\s*(?:\d{1,4}|[ivxlcdmIVXLCDM]{1,7})\s*$")

_SOLO_CIFRAS = re.compile(r"^\d{1,4}$")
_EMPIEZA_MINUSCULA = re.compile(r"^[a-záéíóúüñ]")


@dataclass
class Informe:
    """Qué se quitó, para poder discutirlo en vez de confiar."""
    cabeceras: list[tuple[str, int]] = field(default_factory=list)
    numeros: int = 0
    total: int = 0

    def resumen(self) -> str:
        if not self.total:
            return "sin cabeceras de página"
        partes = [f"{t} ({n}x)" for t, n in self.cabeceras[:4]]
        if len(self.cabeceras) > 4:
            partes.append(f"y {len(self.cabeceras) - 4} más")
        cola = f" · {self.numeros} números de página" if self.numeros else ""
        return f"{self.total} líneas fuera: " + ", ".join(partes) + cola


def _utiles(lineas: list[str]) -> list[tuple[int, str]]:
    """Las líneas con contenido, con su sitio en la lista original.

    La posición se cuenta entre ESTAS, no entre las líneas en bruto: una página
    que empieza con dos líneas en blanco tendría la cabecera en el índice 2 y
    el umbral de zona se comería la diferencia. Cada proyecto guarda los
    blancos a su manera y el detector no debería enterarse.
    """
    return [(i, l.strip()) for i, l in enumerate(lineas) if l.strip()]


def _candidata(linea: str) -> bool:
    return bool(linea) and len(linea) <= MAX_CARACTERES \
        and len(linea.split()) <= MAX_PALABRAS


def detectar(paginas: list[list[str]]) -> dict[str, int]:
    """Las líneas que son cabecera de página, con cuántas veces salen."""
    if len(paginas) < MIN_PAGINAS:
        return {}

    donde: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for p, lineas in enumerate(paginas):
        utiles = _utiles(lineas)
        n = len(utiles)
        if n < MIN_LINEAS_PAGINA:
            continue
        for j, (_, linea) in enumerate(utiles):
            if not _candidata(linea):
                continue
            siguiente = utiles[j + 1][1] if j + 1 < n else ""
            donde[linea].append(
                (p, j, n, bool(_NUMERO_DE_PAGINA.match(siguiente))))

    salida: dict[str, int] = {}
    for linea, apariciones in donde.items():
        # Nunca dos veces en la misma página: eso es un personaje de teatro,
        # no una cabecera.
        por_pagina = Counter(p for p, _, _, _ in apariciones)
        if max(por_pagina.values()) > 1:
            continue

        en_borde = [a for a in apariciones
                    if a[1] < ZONA or a[1] >= a[2] - ZONA]

        # CAMINO 1 — el número de página detrás. Pocas apariciones bastan
        # porque la señal no admite confusión. Ver MIN_PAGINAS_CON_NUMERO.
        if sum(1 for a in en_borde if a[3]) >= MIN_PAGINAS_CON_NUMERO:
            salida[linea] = len(apariciones)
            continue

        # CAMINO 2 — el de siempre, para las cabeceras que el original no
        # numera: muchas páginas y casi siempre en el borde.
        if len(apariciones) < MIN_PAGINAS:
            continue
        if len(en_borde) / len(apariciones) >= BORDE_MINIMO:
            salida[linea] = len(apariciones)
    return salida


def _es_capitular(linea: str, siguiente: str) -> bool:
    """Una letra suelta seguida de texto en minúscula es una CAPITULAR.

    Quitarla dejaría «uchos hombres…» en vez de «Muchos hombres…», que es peor
    que el problema que veníamos a resolver. En Kardec la «M» que se repite 34
    veces NO es esto —es un ornamento, y detrás va el título del capítulo, con
    mayúscula— pero otro libro sí puede traerlas.
    """
    if len(linea) != 1 or not linea.isalpha() or not linea.isupper():
        return False
    return bool(_EMPIEZA_MINUSCULA.match(siguiente))


def limpiar(paginas: list[list[str]],
            con_numeros: bool = True) -> tuple[list[list[str]], Informe]:
    """Quita las cabeceras y los números de página. Devuelve las páginas y el parte.

    `con_numeros` quita además la línea de solo cifras que va pegada a la
    cabecera. Se puede apagar por si algún libro las necesita.
    """
    encontradas = detectar(paginas)
    informe = Informe(cabeceras=sorted(encontradas.items(),
                                       key=lambda x: -x[1]))
    if not encontradas and not con_numeros:
        return paginas, informe

    limpias: list[list[str]] = []
    for lineas in paginas:
        utiles = _utiles(lineas)
        n = len(utiles)
        if n < MIN_LINEAS_PAGINA:
            limpias.append(list(lineas))
            continue
        # Los sitios que hay que borrar, en índices de la lista ORIGINAL, para
        # no tocar los blancos que separan los párrafos.
        borrar: set[int] = set()
        for j, (sitio, linea) in enumerate(utiles):
            if not (j < ZONA or j >= n - ZONA):
                continue
            if linea in encontradas:
                siguiente = utiles[j + 1][1] if j + 1 < n else ""
                if _es_capitular(linea, siguiente):
                    continue
                borrar.add(sitio)
                informe.total += 1
            elif con_numeros and _SOLO_CIFRAS.match(linea):
                borrar.add(sitio)
                informe.numeros += 1
                informe.total += 1
        limpias.append([l for i, l in enumerate(lineas) if i not in borrar])
    return limpias, informe
