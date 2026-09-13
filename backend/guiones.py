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

# Salvaguarda contra el caso "septiembre- octubre".
#
# El documento no siempre tiene pistas: si ni "septiembreoctubre" ni
# "septiembre-octubre" aparecen sueltos, la regla antigua pegaba los dos
# trozos y salia "septiembreoctubre". Mal: ahi el guion era un guion de
# verdad (un rango, o un compuesto tipo "politico- social").
#
# La senal que lo distingue es el diccionario: si los DOS lados son palabras
# espanolas completas y el pegote NO lo es, el guion se conserva.
#
# Es una regla casi gratis: solo se activa cuando el resultado de pegar no es
# una palabra espanola, y en ese caso pegar estaba mal de todas formas. Los
# cortes de verdad ("ha-bia", "si-guiente", "inge-nioso") dan palabras validas
# y no la disparan nunca.
MIN_LETRAS_COMPUESTO = 3


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


def decidir_union(izq: str, der: str, vocab: Counter,
                  es_valida=None, cauto: bool = False) -> str | None:
    """Devuelve la palabra ya reunida, o None si no hay que unir.

    `es_valida(palabra) -> bool` es opcional: un diccionario de espanol de
    verdad. Sin el, se decide solo con el vocabulario del documento (que es
    como funcionaba antes). Con el, se salvan los compuestos y los rangos.

    `cauto=True` apaga la ultima regla, la de "sin pistas, une". Es para
    cuando el texto NO ESTA EN ESPANOL y por tanto el diccionario no puede
    opinar: ahi "sin pistas" no significa "seguramente sea un corte", significa
    "no tengo ni idea". Medido sobre una antologia bilingue espanol-azeri:
    sin esto se pegaban 10 guiones que eran de verdad, entre ellos la
    reduplicacion "kisneye-kisneye". Quien lo enciende es `revision.py`, y
    solo cuando el diccionario rechaza mas de la mitad del libro.
    """
    junto    = izq + der
    guionado = izq + "-" + der
    hay_junto    = junto.lower() in vocab
    hay_guionado = guionado.lower() in vocab

    if hay_junto and not hay_guionado:
        return junto
    if hay_guionado and not hay_junto:
        return guionado

    # Los dos lados son palabras completas y el pegote no lo es: el guion no
    # era un corte. Cubre tres casos que antes se pegaban mal:
    #   rango       "septiembre- octubre"  -> septiembre-octubre
    #   compuesto   "politico- social"     -> politico-social
    #   inciso      "parece- que"          -> parece- que  (era una raya)
    # Un corte de verdad deja un TROZO a la izquierda ("espo-", "cor-",
    # "inge-"), no una palabra entera; y cuando deja dos palabras enteras
    # ("ha-bia", "por-que", "mira-da") el pegote SI es una palabra valida y
    # esta regla no se activa.
    if (es_valida is not None
            and not hay_junto
            and not es_valida(junto)):
        # Muchos libros viejos perdieron las tildes en el OCR, y entonces
        # "politico" no esta en el diccionario aunque sea una palabra. Vale
        # tambien que el propio documento la use suelta varias veces.
        def _palabra(w: str) -> bool:
            return es_valida(w) or vocab.get(w.lower(), 0) >= MIN_USOS_SOSPECHA
        # Basta con que UN lado sea palabra completa. Con los dos se perdian
        # los nombres propios y los extranjerismos que no estan en ningun
        # diccionario espanol: "Terencio- el", "walkie- talkie", "auto- stop".
        if _palabra(izq) or _palabra(der):
            # None = NO TOCAR, en vez de pegar con guion. En un texto ya
            # aplanado no se sabe si era un rango ("septiembre- octubre"),
            # un compuesto ("causa- efecto") o una raya de dialogo mal
            # codificada ("parece- que"). El TTS lee los tres bien tal como
            # estan — dos palabras separadas — y lo ambiguo no se toca.
            return None

    if (not hay_junto
            and len(der) >= MIN_LETRAS_SOSPECHA
            and vocab.get(der.lower(), 0) >= MIN_USOS_SOSPECHA):
        return None      # continuacion sospechosa: mejor no tocar

    # Sin pistas: los cortes de linea son mucho mas frecuentes que los
    # compuestos con guion, asi que se une... salvo que ni siquiera sepamos
    # en que idioma esta el texto, y entonces no se toca.
    return None if cauto else junto


def unir_palabras_cortadas(lineas: list[str], vocab: Counter,
                           es_valida=None, cauto: bool = False) -> list[str]:
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
            unida = decidir_union(izq, der, vocab, es_valida, cauto)
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

CORTE_EN_TEXTO = re.compile(
    rf"([^\W\d_]+)[{_GUIONES}][ \t]+([a-záéíóúüñ][^\W\d_]*)", re.UNICODE
)


def reparar_texto_plano(texto: str, vocab: Counter, es_valida=None,
                       registro: list | None = None,
                       cauto: bool = False) -> tuple[str, int]:
    """Repara cortes dentro de un texto ya unido. Devuelve (texto, arreglos).

    `registro`, si se pasa, recibe tuplas (antes, despues) de los cambios
    REALES. Es la unica forma honesta de ensenar ejemplos: reconstruirlos
    buscando la palabra en el texto ya reparado da resultados falsos.
    """
    arreglos = 0

    def _sustituir(m):
        nonlocal arreglos
        unida = decidir_union(m.group(1), m.group(2), vocab,
                              es_valida, cauto)
        if unida is None:
            return m.group(0)          # se deja tal cual
        arreglos += 1
        if registro is not None:
            registro.append((m.group(0), unida))
        return unida

    return CORTE_EN_TEXTO.sub(_sustituir, texto), arreglos


def vocabulario_de_textos(textos: list[str]) -> Counter:
    """Vocabulario a partir de textos ya unidos (una sola linea cada uno).

    Se ignoran los fragmentos pegados a un guion, que son justo los rotos.
    """
    vocab: Counter = Counter()
    for t in textos:
        limpio = CORTE_EN_TEXTO.sub(" ", t)
        for w in _PALABRA.findall(limpio):
            if len(w) > 2:
                vocab[w.lower()] += 1
    return vocab

# ---------------------------------------------------------------------------
# Deshacer pegotes
#
# La primera version de este modulo no tenia diccionario y pegaba cualquier
# "palabra- palabra", incluidos los rangos, los compuestos y las rayas de
# dialogo: de ahi salieron "septiembreoctubre", "pareceque" y "locurairrumpe".
#
# Esos pegotes se pueden deshacer sin respaldo, porque dejan una huella muy
# clara: una palabra que NO es espanola, que el libro usa una o dos veces, y
# que se parte en dos palabras que el libro SI usa por separado.
# ---------------------------------------------------------------------------

# Un pegote tiene al menos dos palabras dentro; por debajo de esto solo hay
# ruido ("mis"+"ion" de "mision" sin tilde).
MIN_LARGO_PEGOTE = 6
# Y es raro: si la palabra sale muchas veces es que es una palabra de verdad
# (una sin tilde que el diccionario no reconoce, por ejemplo "tambien").
MAX_USOS_PEGOTE = 3

# LO QUE NUNCA SE PARTE
# ---------------------
# El diccionario de hunspell no lleva las formas con pronombre enclitico
# ("persuadirlo") ni todos los derivados con prefijo ("desaprendemos"), asi
# que las marca como invalidas y se parten en dos palabras que SI conoce.
# Medido en Zaratustra: de 142 cortes propuestos, 6 eran de esta clase y
# habrian destrozado palabras correctas. Estas listas los paran.

# Pronombres que se pegan al verbo. Solo cuentan si la izquierda ACABA como
# un verbo que los admite: infinitivo, gerundio o imperativo de vosotros.
ENCLITICOS = {"lo", "la", "le", "los", "las", "les", "me", "te", "se",
              "nos", "os", "selo", "sela", "melo", "mela", "telo", "tela"}
# Terminaciones de verbo que admiten enclitico. Las acentuadas son las que
# faltaban: "Limitose", "Sentose", "habriase", "Distinguianse", "hacianlo".
FIN_VERBAL = ("ar", "er", "ir", "ndo", "ad", "ed", "id",
              "arse", "erse", "irse", "se", "rse",
              "ó", "á", "é", "í", "ío", "ía", "ían", "íase",
              "aba", "aban", "ara", "iera", "ase", "ese")

# Prefijos. No estan aqui "para", "bien", "medio", "sin" ni "no", que son
# tambien palabras corrientes y aparecen como primera mitad de pegotes de
# verdad ("parael" -> "para- el").
PREFIJOS = {"des", "in", "im", "ir", "re", "pre", "pro", "anti", "auto",
            "co", "con", "contra", "entre", "extra", "inter", "intra",
            "micro", "mono", "multi", "neo", "post", "pos", "pseudo",
            "seudo", "semi", "sobre", "sub", "super", "supra", "tele",
            "trans", "tras", "ultra", "vice", "bi", "tri", "mal", "pluri",
            "archi", "hiper", "hipo", "mega", "retro"}

# Palabras de funcion: articulos, preposiciones, conjunciones, pronombres.
# Nunca son la segunda mitad de un derivado con prefijo, asi que cuando
# aparecen ahi el corte es bueno aunque la izquierda sea un prefijo.
FUNCIONALES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo",
               "al", "del", "de", "en", "con", "por", "para", "sin", "sobre",
               "y", "e", "o", "u", "que", "qué", "se", "si", "sí", "no",
               "es", "era", "ser", "su", "sus", "mi", "mis", "tu", "tus",
               "me", "te", "le", "les", "nos", "como", "cuando", "pero",
               "mas", "más", "muy", "ya", "aun", "aún", "asi", "así",
               "todo", "toda", "todos", "todas", "este", "esta", "esto",
               "ese", "esa", "eso", "aquel", "hay", "ha", "he", "han",
               "son", "fue", "fueron", "eran", "sea", "está", "están"}


# Terminaciones que son palabras por su cuenta y por eso enganaban:
#   "mente" -> "insondablemente" se partia en "insondable"+"mente"
#   "cita"  -> "mujercita" se partia en "mujer"+"cita"
# Ninguna palabra que acabe asi se parte nunca.
SUFIJOS = ("mente", "cita", "cito", "citas", "citos",
           "illa", "illo", "illas", "illos",
           # derivaciones que tambien son palabras por su cuenta y por eso
           # partian "ocultamiento", "barrancada", "irrealizado"
           "miento", "mientos", "ada", "adas", "ado", "ados",
           "izado", "izada", "izados", "izadas", "cada", "cado")


def _no_partir(izq: str, der: str) -> bool:
    """True si el pegote es en realidad UNA palabra correcta."""
    i, d = izq.lower(), der.lower()
    if d in SUFIJOS:
        return True                      # insondable+mente, pensativa+mente
    if d in ENCLITICOS and i.endswith(FIN_VERBAL):
        return True                      # persuadir+lo, escuchad+lo
    if i in PREFIJOS and d not in FUNCIONALES:
        return True                      # des+aprendemos, ir+realizado
    return False


# Las ligaduras tipograficas de los PDF viejos: "ﬁ" es UN caracter, no dos.
# Por eso "Desconﬁado" no esta en el diccionario y parecia un pegote. Se
# deshacen solo para PREGUNTAR al diccionario; el texto no se toca.
LIGADURAS = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
             "ﬅ": "ft", "ﬆ": "st"}


def sin_ligaduras(palabra: str) -> str:
    for a, b in LIGADURAS.items():
        if a in palabra:
            palabra = palabra.replace(a, b)
    return palabra


# CUANTO HAY QUE EXIGIR PARA PARTIR
# ---------------------------------
# Medido en tres libros mas: sin exigir nada, "despegar" destroza plurales
# ("recodo- s"), diminutivos ("mujer- cita"), nombres propios ("P- rusia",
# "Fang- shu"), latin ("haber- e", "ni- hilo") y encliticos ("Limito- se").
# El problema es que en Schopenhauer se reescribieron 62 de 62 partes: sin
# partes intactas no hay coartada, y "no esta en el diccionario" solo no basta.
#
# En MODO ESTRICTO (el de por defecto) solo se parte cuando la mitad derecha
# es una PALABRA DE FUNCION: es la firma de la raya de inciso mal codificada
# ("conciencia- es", "humanidad- que", "hogar- son"), que es el unico dano
# que la version vieja pudo causar. Un plural, un diminutivo o un nombre
# propio nunca tienen un articulo o una conjuncion en la segunda mitad.
MIN_IZQ_ESTRICTO = 4
MIN_DER_ESTRICTO = 2


def _corte_creible(izq: str, der: str, frec: Counter, es_valida,
                   estricto: bool) -> bool:
    if not estricto:
        return True
    if der.lower() not in FUNCIONALES:
        return False
    if len(der) < MIN_DER_ESTRICTO or len(izq) < MIN_IZQ_ESTRICTO:
        return False
    return es_valida(izq) or frec.get(izq.lower(), 0) >= MIN_USOS_SOSPECHA


def _mejor_corte(palabra: str, frec: Counter, es_valida,
                 estricto: bool = True) -> tuple[str, str] | None:
    """El corte mas creible, o None. Se elige por el uso en el propio libro.

    Se puntua con el PRODUCTO de las dos frecuencias, no con el minimo: en
    "buenay" el minimo se llevaba "buen"+"ay" (las dos salen en Nietzsche) y
    el producto se lleva "buena"+"y", que es el corte de verdad porque "y"
    sale cientos de veces.
    """
    mejor, mejor_puntos = None, 0
    for i in range(1, len(palabra)):
        izq, der = palabra[:i], palabra[i:]
        f_izq = frec.get(izq.lower(), 0)
        f_der = frec.get(der.lower(), 0)
        if f_izq < 1 or f_der < 1:
            continue            # los dos trozos han de existir sueltos
        if not (es_valida(izq) or f_izq >= MIN_USOS_SOSPECHA):
            continue
        if not (es_valida(der) or f_der >= MIN_USOS_SOSPECHA):
            continue
        if not _corte_creible(izq, der, frec, es_valida, estricto):
            continue
        puntos = f_izq * f_der
        if puntos > mejor_puntos:
            mejor, mejor_puntos = (izq, der), puntos

    # Las guardas se aplican SOLO al corte ganador. Aplicarlas dentro del
    # bucle abortaba la palabra entera por un corte intermedio absurdo:
    # "Concienzudoasi" moria en "Con"+"cienzudoasi" porque "con" es prefijo.
    if mejor is not None and _no_partir(*mejor):
        return None
    return mejor


def despegar_texto(texto: str, frec: Counter, es_valida,
                   registro: list | None = None,
                   evitar: set | None = None,
                   estricto: bool = True) -> tuple[str, int]:
    """Devuelve (texto, deshechos). Restaura el "guion + espacio" original.

    `evitar` es la prueba mas fuerte de todas: palabras que aparecen en partes
    del libro que NUNCA se tocaron. Si una supuesta "pegote" sale tambien ahi,
    entonces venia del libro original y no la creo la reparacion — asi que no
    se toca. Es lo que distingue "adivinose" (que puede ser "adivinose" con
    enclitico) de "pareceque" (que solo existe porque pegamos mal).
    """
    deshechos = 0
    evitar = evitar or set()

    def _sustituir(m):
        nonlocal deshechos
        w = m.group(0)
        plano = sin_ligaduras(w)
        if (len(w) < MIN_LARGO_PEGOTE
                or w.lower() in evitar
                or es_valida(w)
                or (plano != w and es_valida(plano))
                or frec.get(w.lower(), 0) > MAX_USOS_PEGOTE):
            return w
        corte = _mejor_corte(w, frec, es_valida, estricto)
        if corte is None:
            return w
        deshechos += 1
        nuevo = f"{corte[0]}- {corte[1]}"
        if registro is not None:
            registro.append((w, nuevo))
        return nuevo

    return _PALABRA_SUELTA.sub(_sustituir, texto), deshechos


_PALABRA_SUELTA = re.compile(r"[^\W\d_]{%d,}" % MIN_LARGO_PEGOTE, re.UNICODE)

# ---------------------------------------------------------------------------
# Espacios que faltan
#
# El otro mal de los libros escaneados, y en "El libro de los espiritus"
# (Kardec) el que de verdad estropea la lectura: el extractor pega dos
# palabras. Medido en su parte 100, 3.759 caracteres:
#
#   "les ha dadoeste aspecto"          -> dado este
#   "rodean delos mas exquisitos"      -> de los
#   "que seuniese a vuestras filas"    -> se uniese
#   "tiene ademasotra utilidad"        -> ademas otra
#   "accesiblesa los consejos"         -> accesibles a
#   "Estaes el deber"                  -> Esta es
#
# El TTS los lee como palabras inventadas. Se detectan igual que los pegotes
# de guion — palabra que no es espanola y se parte en dos que si lo son — con
# las mismas guardas y una mas: las palabras de UNA letra estan en lista
# cerrada, porque el diccionario acepta "d" y eso partia "Durand".
# ---------------------------------------------------------------------------

UNA_LETRA = {"a", "y", "e", "o", "u"}
MIN_LARGO_PEGADA = 5
# Solo palabras RARAS. Medido en "El libro de Los Mediums": "Erasto" (el
# nombre de un Espiritu) sale 15 veces, no esta en el diccionario, y se partia
# en "Eras to". Lo mismo "mixtificadores" -> "mixtificado res". Si una palabra
# se repite, es del libro aunque el diccionario no la conozca.
MAX_USOS_PEGADA = 3

# AVISO: este motor NO se aplica solo en ningun sitio, y es a proposito.
# En el libro de los Mediums acierta 10 de sus 51 propuestas. Vale como
# diagnostico; para arreglar de verdad hace falta que una IA lea la frase.


def _es_palabra(w: str, es_valida) -> bool:
    if len(w) == 1:
        return w.lower() in UNA_LETRA
    return bool(es_valida(w))


# Palabras de funcion que cuentan como "usadas en el libro" aunque no se
# hayan contado: en cualquier texto espanol salen si o si.
SIEMPRE_PRESENTES = UNA_LETRA | {"de", "la", "el", "en", "se", "es", "los",
                                 "las", "un", "una", "que", "no", "su", "al"}


def mejor_separacion(palabra: str, frec: Counter, es_valida):
    """Donde va el espacio, o None.

    Tres exigencias, y las tres salieron de romper cosas:
      - Las DOS mitades tienen que usarse sueltas en el propio libro. Sin
        esto, el latin y los nombres propios se parten: "habere" -> "hab ere",
        "Milton" -> "Mil ton".
      - Si ALGUN corte de la palabra es un verbo con enclitico o una
        derivacion, no se toca la palabra entera. "habiase" tiene el corte
        bueno "habia"+"se" (enclitico) y otro absurdo "habias"+"e": mirando
        solo el ganador se colaba el absurdo.
      - El corte se elige por el uso de las mitades en el libro, no por el
        primero que valga: "dadoeste" da "dad oeste" antes que "dado este".
    """
    # Guardas que anulan la palabra completa, mire donde mire.
    for i in range(1, len(palabra)):
        izq, der = palabra[:i], palabra[i:]
        d = der.lower()
        if d in SUFIJOS:
            return None
        if d in ENCLITICOS and izq.lower().endswith(FIN_VERBAL):
            return None

    mejor, puntos_mejor = None, -1
    for i in range(1, len(palabra)):
        izq, der = palabra[:i], palabra[i:]
        if not (_es_palabra(izq, es_valida) and _es_palabra(der, es_valida)):
            continue
        f_izq = frec.get(izq.lower(), 0)
        f_der = frec.get(der.lower(), 0)
        if not (f_izq or izq.lower() in SIEMPRE_PRESENTES):
            continue
        if not (f_der or der.lower() in SIEMPRE_PRESENTES):
            continue
        if _no_partir(izq, der):
            continue
        puntos = (f_izq + 1) * (f_der + 1)
        if puntos > puntos_mejor:
            mejor, puntos_mejor = (izq, der), puntos
    if mejor and _no_partir(*mejor):
        return None
    return mejor


def separar_pegadas(texto: str, frec: Counter, es_valida,
                    registro: list | None = None,
                    evitar: set | None = None) -> tuple[str, int]:
    """Mete los espacios que faltan. Devuelve (texto, arreglos)."""
    arreglos = 0
    evitar = evitar or set()

    def _sustituir(m):
        nonlocal arreglos
        w = m.group(0)
        plano = sin_ligaduras(w)
        if (len(w) < MIN_LARGO_PEGADA
                or w.lower() in evitar
                or frec.get(w.lower(), 0) > MAX_USOS_PEGADA
                or es_valida(w)
                or (plano != w and es_valida(plano))):
            return w
        corte = mejor_separacion(w, frec, es_valida)
        if corte is None:
            return w
        arreglos += 1
        nuevo = f"{corte[0]} {corte[1]}"
        if registro is not None:
            registro.append((w, nuevo))
        return nuevo

    return _PALABRA_LARGA.sub(_sustituir, texto), arreglos


_PALABRA_LARGA = re.compile(r"[^\W\d_]{%d,}" % MIN_LARGO_PEGADA, re.UNICODE)
