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
            if _candidata(linea):
                donde[linea].append((p, j, n))

    salida: dict[str, int] = {}
    for linea, apariciones in donde.items():
        if len(apariciones) < MIN_PAGINAS:
            continue
        # Nunca dos veces en la misma página: eso es un personaje, no una
        # cabecera.
        por_pagina = Counter(p for p, _, _ in apariciones)
        if max(por_pagina.values()) > 1:
            continue
        en_borde = sum(1 for _, j, n in apariciones if j < ZONA or j >= n - ZONA)
        if en_borde / len(apariciones) >= BORDE_MINIMO:
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
