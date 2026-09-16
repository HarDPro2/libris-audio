"""Como se DICE un texto — lo que hay que arreglar antes de fonemizar.

Un libro no esta escrito para leerse en voz alta. Trae cifras, romanos,
abreviaturas y simbolos que un lector humano convierte sin pensar y que un TTS
no sabe hacer: se los salta, los deletrea o dice «numero».

    en 1605, el cap. XII, pag. 47, el 80% de los casos
    en mil seiscientos cinco, el capitulo doce, pagina cuarenta y siete,
    el ochenta por ciento de los casos

EL PRINCIPIO: ANTE LA DUDA, NO SE TOCA
--------------------------------------
Esto corre sobre el texto que se va a leer, sin nadie mirando. Un cambio malo
no se nota hasta que alguien escucha el audiolibro y oye un disparate. Asi que
cada regla lleva su condicion, y lo que no encaja se queda como esta.

El caso que mas obliga a esto son los ROMANOS. «V» puede ser el numero cinco o
la inicial de Vicente; «MIX» puede ser 1009 o una palabra en ingles. Por eso un
romano solo se convierte cuando algo del contexto lo confirma: que venga detras
de «capitulo», «siglo», «tomo»... o detras de un nombre propio, como en
«Felipe II». Una letra suelta no se toca nunca.
"""
from __future__ import annotations

import re

from numeros import cardinal, desde_romano, ordinal

# Detras de estas palabras, un romano es un numero seguro.
REFERENCIAS = {
    "capitulo", "capítulo", "capitulos", "capítulos", "libro", "libros",
    "tomo", "tomos", "parte", "partes", "volumen", "volúmenes", "volumenes",
    "seccion", "sección", "acto", "escena", "canto", "jornada", "apendice",
    "apéndice", "anexo", "leccion", "lección", "figura", "lamina", "lámina",
    "tabla", "cuadro", "articulo", "artículo", "salmo", "version", "versión",
    "siglo", "siglos", "num", "núm", "numero", "número", "pagina", "página",
    "pag", "pág", "vease", "véase", "guerra", "congreso", "olimpiada",
}
# Detras de estas, se lee como ORDINAL: «Felipe II» es «Felipe segundo».
# Hasta el diez; de ahi para arriba se dice el cardinal.
ORDINAL_TRAS_NOMBRE = 10

ABREVIATURAS = {
    "sr": "señor", "sra": "señora", "srta": "señorita", "dr": "doctor",
    "dra": "doctora", "d": "don", "dña": "doña", "dn": "don",
    "prof": "profesor", "profa": "profesora", "ing": "ingeniero",
    "lic": "licenciado", "gral": "general", "cnel": "coronel",
    "pag": "página", "pág": "página", "pags": "páginas", "págs": "páginas",
    "cap": "capítulo", "caps": "capítulos", "vol": "volumen",
    "núm": "número", "num": "número", "nro": "número", "art": "artículo",
    "ed": "edición", "edit": "editorial", "trad": "traducción",
    "etc": "etcétera", "aprox": "aproximadamente", "máx": "máximo",
    "mín": "mínimo", "ej": "ejemplo", "ss": "siguientes", "fig": "figura",
    "sig": "siguiente", "vs": "versus", "av": "avenida", "avda": "avenida",
    "izq": "izquierda", "dcha": "derecha", "depto": "departamento",
    "admón": "administración", "atte": "atentamente", "cta": "cuenta",
}
SIMBOLOS = {
    "%": " por ciento", "‰": " por mil", "&": " y ", "§": "párrafo ",
    "©": "copyright ", "®": " marca registrada", "°": " grados",
    "€": " euros", "$": " dólares", "£": " libras",
    "+": " más ", "=": " igual a ", "×": " por ", "÷": " entre ",
}

_NOMBRE_PROPIO = re.compile(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+$")
_MILES = re.compile(r"\b\d{1,3}(?:\.\d{3})+\b")
_DECIMAL = re.compile(r"\b(\d+),(\d+)\b")
_ENTERO = re.compile(r"\b\d+\b")
_ORDINAL_MARCA = re.compile(r"\b(\d+)\s*[.]?\s*([ºª°])")
_ROMANO = re.compile(r"\b([IVXLCDM]{2,})\b")
# Detras de la abreviatura puede venir puntuacion: «etc.,» y «(cap. 3)» son
# tan normales como «etc. » al final de la frase.
_ABREV = re.compile(r"\b([A-Za-zÁÉÍÓÚÑáéíóúñ]{1,6})\.(?=[\s,;:)\]}»\"]|$)")
# Una inicial suelta: «H.» en «D. H. Lawrence».
_INICIAL = re.compile(r"\s*[A-ZÁÉÍÓÚÑ]\.")
_RANGO = re.compile(r"\b(\d+)\s*[-–—]\s*(\d+)\b")
# Una cadena de tres o mas grupos unidos por guion no es un rango: es un
# codigo. Ver `_es_rango`.
_CADENA = re.compile(r"\b\d+(?:\s*[-–—]\s*\d+){2,}\b")
# Un «+» seguido de VARIOS grupos de cifras es un telefono internacional, no
# una suma. Se exigen dos grupos o mas para no tocar «2 + 3».
_TELEFONO = re.compile(r"\+\s*\d+(?:\s+\d+){1,}")
# En espanol el decimal lleva coma, asi que un punto entre cifras solo puede
# ser dos cosas: separador de miles («1.250») o un codigo («CDD: 133.93»).
# Este coge los dos y `_son_miles` decide cual es cual.
_PUNTO_ENTRE_CIFRAS = re.compile(r"\b\d+(?:\.\d+)+\b")
_SON_MILES = re.compile(r"^\d{1,3}(?:\.\d{3})+$")


def _son_miles(s: str) -> bool:
    """«1.250» son miles; «133.93» es una clasificacion decimal.

    La diferencia esta en los grupos: los miles van SIEMPRE de tres en tres.
    Sin esto, «CDD: 133.93» salia «ciento treinta y tres.noventa y tres», con
    el punto leido como final de frase en medio de la cifra.
    """
    return bool(_SON_MILES.match(s))


def _es_rango(a: str, b: str) -> bool:
    """Si «a-b» es un rango de verdad o un codigo con un guion dentro.

    SALIO DEL CORPUS, no de pensarlo: al pasar el motor por «El libro de los
    espiritus» aparecio esto en la pagina de creditos:

        ISBN 978-85-98161-66-2  ->  «novecientos setenta y ocho a ochenta y
                                     cinco-noventa y ocho mil ciento...»
        70790-090               ->  «setenta mil setecientos noventa a noventa»

    La regla de rangos —la que convierte «paginas 20-25» en «veinte a
    veinticinco»— se estaba comiendo ISBN, codigos postales y telefonos. Leer
    mal un codigo es peor que leerlo en cifras: es mas largo y sigue sin
    entenderse.

    Un rango de verdad cumple las cuatro:
      - ninguno empieza por cero («090» es un codigo, no el numero noventa);
      - ninguno pasa de cuatro cifras (un ano es el tope razonable);
      - el segundo es mayor que el primero;
      - y no estan dentro de una cadena mas larga, que mira `numeros()`.
    """
    if (a.startswith("0") and len(a) > 1) or (b.startswith("0") and len(b) > 1):
        return False
    if len(a) > 4 or len(b) > 4:
        return False
    return int(b) > int(a)


def _palabra_antes(texto: str, i: int) -> str:
    m = re.search(r"([^\W\d_]+)[^\w]*$", texto[max(0, i - 40):i], re.UNICODE)
    return m.group(1) if m else ""


def _trozo_antes(texto: str, i: int) -> str:
    return texto[max(0, i - 40):i].rstrip()


def romanos(texto: str) -> str:
    """Convierte los romanos que el contexto confirma. Los demas se quedan."""
    def cambia(m):
        valor = desde_romano(m.group(1))
        if valor is None:
            return m.group(0)
        antes = _palabra_antes(texto, m.start())
        if antes.lower() in REFERENCIAS:
            return cardinal(valor)
        # «Felipe II», «Juan XXIII»: nombre propio delante.
        if _NOMBRE_PROPIO.search(_trozo_antes(texto, m.start())):
            return (ordinal(valor) if valor <= ORDINAL_TRAS_NOMBRE
                    else cardinal(valor))
        return m.group(0)          # sin confirmacion, no se toca
    return _ROMANO.sub(cambia, texto)


def _apartar_codigos(texto: str, intocables: dict[str, str]) -> str:
    """Saca de en medio lo que NO es una cantidad y lo cambia por un marcador.

    Se llama ANTES que ninguna otra regla. El motivo lo destapo el corpus:
    `simbolos()` convierte el «+» en «mas» y corre ANTES que `numeros()`, asi
    que cuando la regla del telefono llegaba a mirar ya no quedaba ningun «+»
    que reconocer, y «+ 55 61 3038 8425» salia leido como cuatro cantidades.

    El marcador no lleva digitos a proposito: si los llevara, la propia regla
    de enteros se lo comeria y destrozaria la clave — paso al escribirlo, y
    «ISBN 978-85-98161-66-2» acabo en «ISBN cero». Tampoco lleva mayusculas,
    que se las quedaria la regla de romanos, ni puntos, que se los quedaria la
    de abreviaturas: cruza las cuatro fases sin que ninguna lo toque.
    """
    def apartar(m: "re.Match") -> str:
        clave = "\x00" + "".join(chr(97 + int(d))
                                 for d in str(len(intocables))) + "\x00"
        intocables[clave] = m.group(0)
        return clave

    # Telefonos internacionales, y cadenas de tres o mas grupos con guion:
    # ISBN, codigos postales, referencias.
    texto = _TELEFONO.sub(apartar, texto)
    texto = _CADENA.sub(apartar, texto)
    # Y los puntos entre cifras que no son miles.
    texto = _PUNTO_ENTRE_CIFRAS.sub(
        lambda m: m.group(0) if _son_miles(m.group(0)) else apartar(m), texto)
    # Y los pares con guion que no son un rango de verdad. Apartarlos ENTEROS,
    # no solo dejar el guion: si no, «70790-090» se quedaba en «setenta mil
    # setecientos noventa-noventa», que es peor que el original. Los rangos
    # de verdad se quedan como estan: los convierte `numeros()`.
    return _RANGO.sub(
        lambda m: (m.group(0) if _es_rango(m.group(1), m.group(2))
                   else apartar(m)), texto)


def _devolver_codigos(texto: str, intocables: dict[str, str]) -> str:
    """Devuelve cada codigo a su sitio, tal cual estaba escrito."""
    for clave, original in intocables.items():
        texto = texto.replace(clave, original)
    return texto


def numeros(texto: str) -> str:
    """Cifras a palabras, en el orden en que hay que hacerlo."""
    # Si viene de `normalizar()` los codigos ya estan apartados y esto no
    # encuentra nada; si alguien llama aqui directamente, quedan igual de
    # protegidos.
    intocables: dict[str, str] = {}
    texto = _apartar_codigos(texto, intocables)
    # Los ordinales primero: «3.º» tiene que verse antes que el «3» suelto.
    # Y OJO: «º» y «ª» no pueden estar en la lista de simbolos, porque esa
    # corre antes y los borraria — «3.º» se quedaba en «3.» y salia «tres.».
    texto = _ORDINAL_MARCA.sub(
        lambda m: _genero(ordinal(int(m.group(1))), m.group(2)), texto)
    # Los rangos que sobrevivieron al filtro: «paginas 20-25» se dice «de
    # veinte a veinticinco».
    texto = _RANGO.sub(
        lambda m: (f"{cardinal(int(m.group(1)))} a {cardinal(int(m.group(2)))}"
                   if _es_rango(m.group(1), m.group(2)) else m.group(0)),
        texto)
    # Los miles con punto, antes que nada los rompa.
    texto = _MILES.sub(lambda m: cardinal(int(m.group(0).replace(".", ""))),
                       texto)
    # Los decimales con coma: «3,14» es «tres coma catorce».
    texto = _DECIMAL.sub(
        lambda m: f"{cardinal(int(m.group(1)))} coma "
                  f"{cardinal(int(m.group(2)))}", texto)
    # Y el resto de enteros. Los muy largos se dejan: un numero de veinte
    # cifras no es una cantidad, es un codigo, y leerlo entero es peor.
    def entero(m):
        s = m.group(0)
        return cardinal(int(s)) if len(s) <= 15 else s
    texto = _ENTERO.sub(entero, texto)
    return _devolver_codigos(texto, intocables)


def _genero(palabra: str, marca: str) -> str:
    if marca == "ª" and palabra.endswith("o"):
        return palabra[:-1] + "a"
    return palabra


def abreviaturas(texto: str) -> str:
    def cambia(m):
        pal = m.group(1)
        largo = ABREVIATURAS.get(pal.lower())
        if largo is None:
            return m.group(0)
        # UNA SOLA LETRA ES AMBIGUA: «D. Quijote» es «don Quijote», pero
        # «D. H. Lawrence» son dos iniciales y ahi «don» seria un disparate.
        # Lo que las separa es si detras viene OTRA inicial.
        if len(pal) == 1 and _INICIAL.match(texto[m.end():m.end() + 4]):
            return m.group(0)
        # Se respeta la mayuscula: «Sr.» -> «Señor», «sr.» -> «señor».
        return largo.capitalize() if pal[0].isupper() else largo
    return _ABREV.sub(cambia, texto)


def simbolos(texto: str) -> str:
    for s, palabra in SIMBOLOS.items():
        if s in texto:
            texto = texto.replace(s, palabra)
    return texto


def normalizar(texto: str, *, con_romanos: bool = True,
               con_numeros: bool = True, con_abreviaturas: bool = True,
               con_simbolos: bool = True) -> str:
    """Deja el texto tal como hay que decirlo.

    EL ORDEN IMPORTA y no es el que parece:
      1. abreviaturas, porque «pag.» tiene que volverse «pagina» ANTES de que
         el romano de «pag. XII» busque su palabra de contexto;
      2. romanos, mientras todavia son letras;
      3. simbolos, que pueden dejar cifras sueltas («80%»);
      4. numeros, al final, cuando ya no queda nada que los produzca.
    """
    # Y antes que los cuatro, los codigos se apartan. No es un quinto paso:
    # es la condicion para que el primero no los rompa. `simbolos()` se comia
    # el «+» del telefono dos fases antes de que nadie pudiera reconocerlo.
    intocables: dict[str, str] = {}
    if con_numeros:
        texto = _apartar_codigos(texto, intocables)
    if con_abreviaturas:
        texto = abreviaturas(texto)
    if con_romanos:
        texto = romanos(texto)
    if con_simbolos:
        texto = simbolos(texto)
    if con_numeros:
        texto = numeros(texto)
    # Los espacios se cuadran ANTES de devolver los codigos: un codigo vuelve
    # exactamente como estaba escrito, o el karaoke deja de cuadrar.
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    return _devolver_codigos(texto, intocables)


# ─────────────────────────────────────────────────────────────────────────────
# EL PUENTE ENTRE EL TEXTO QUE SE LEE Y EL QUE SE OYE — 16-09-2026
#
# Normalizar cambia la CUENTA de palabras: «El 3 de mayo de 1605» son seis
# palabras escritas y ocho dichas. Y ahi hay un fallo que no da la cara:
#
#   - el karaoke ilumina sobre el texto ORIGINAL, que es el que se ve;
#   - los tiempos vienen del texto NORMALIZADO, que es el que se sintetiza.
#
# Si nadie los cose, el resaltado se corre dos palabras en cuanto aparece una
# cifra, y el error CRECE con cada una. En un capitulo con fechas acaba
# iluminando renglones enteros por detras de la voz.
#
# `mapear` dice cuantas palabras dichas salieron de cada palabra escrita. Con
# eso, quien tenga los tiempos del audio puede juntarlos: la palabra «1605»
# empieza cuando empieza «mil» y acaba cuando acaba «cinco».
#
# Se alinea con difflib y no a mano: normalizar sustituye en el sitio y no
# reordena nada, asi que una alineacion de secuencias lo resuelve entero,
# incluidos los casos raros —una abreviatura que se vuelve dos palabras justo
# al lado de un romano que se vuelve tres—.
# ─────────────────────────────────────────────────────────────────────────────
def mapear(original: str, normalizado: str) -> list[int]:
    """Cuantas palabras del texto dicho salieron de cada palabra escrita.

    Devuelve una lista tan larga como palabras tenga `original`. La suma da el
    numero de palabras de `normalizado`.

        >>> mapear("En 1605 vino", "En mil seiscientos cinco vino")
        [1, 3, 1]
    """
    import difflib

    escritas, dichas = original.split(), normalizado.split()
    if not escritas:
        return []
    grupos = [0] * len(escritas)

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, escritas, dichas, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                grupos[k] = 1
        elif tag == "insert":
            # Palabras dichas que no salen de ninguna escrita: se pegan a la
            # anterior, que es de donde vienen en la practica.
            if i1 > 0:
                grupos[i1 - 1] += j2 - j1
            elif grupos:
                grupos[0] += j2 - j1
        else:                                   # replace / delete
            cuantas, sale = i2 - i1, j2 - j1
            # Lo normal es una escrita que se vuelve varias dichas. Si el
            # bloque abarca varias escritas, se reparte a partes iguales: es
            # raro, y equivocarse ahi solo mueve el resalte dentro del bloque.
            for k in range(cuantas):
                grupos[i1 + k] = sale // cuantas + (1 if k < sale % cuantas else 0)
    return grupos


def normalizar_mapeado(texto: str, **opciones) -> tuple[str, list[int]]:
    """El texto listo para decir, y el puente de vuelta al escrito."""
    dicho = normalizar(texto, **opciones)
    return dicho, mapear(texto, dicho)


def juntar_tiempos(tiempos: list, grupos: list[int]) -> list:
    """Agrupa los tiempos del texto dicho para que casen con el escrito.

    `tiempos` es una lista de objetos con `inicio_ms` y `fin_ms`, uno por
    palabra dicha. Sale una lista con uno por palabra ESCRITA: la escrita
    empieza donde empieza su primera dicha y acaba donde acaba la ultima.
    """
    salida, cursor = [], 0
    for n in grupos:
        trozo = tiempos[cursor:cursor + n]
        if trozo:
            salida.append((trozo[0], trozo[-1]))
        cursor += max(n, 0)
    return salida
