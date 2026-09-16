"""Las secciones que nadie quiere oír — «Saltar índice», como Netflix.

EL PRINCIPIO, heredado de `decir.py`: ante la duda, NO se marca. Un falso
negativo cuesta unos minutos de audio aburrido. Un falso positivo se come un
capítulo de verdad, y el lector no se entera de que le falta algo hasta que la
historia deja de tener sentido. Los umbrales de este archivo están puestos del
lado de no marcar.

QUÉ SE MARCA Y QUÉ NO. La comparación es la de Netflix: no borra la intro,
ofrece saltarla. Aquí igual — el texto SIGUE ESTANDO, se ve entero en pantalla
y se puede leer con los ojos. Lo único que cambia es que:

  - se sabe dónde empieza y dónde acaba, para pintar el botón;
  - y si no vale la pena decirlo en voz alta, no se sintetiza (`sintetizar`).

Esa segunda parte no es cosmética. El índice alfabético de «El libro de los
espíritus» son 1.514 líneas de cifras seguidas: minutos de audio que nadie va a
escuchar, y que cuestan síntesis cada vez que alguien abre el libro.

LA DISTINCIÓN QUE IMPORTA, y que salió de mirar los libros de verdad: no todo
lo que va al final es ilegible en voz alta.

    Kardec, índice alfabético  «Asesinato: 709, 746-749, 757-758a, 765.»
    Eurípides, notas           «[1] La obra de M. Victor Duruy, titulada
                                Histoire Grecque, que hemos tenido a la
                                vista, es algo parcial por la democracia…»

Las dos son secciones que la mayoría se salta. Pero la primera es una lista de
referencias que no se puede decir, y la segunda es prosa que se entiende
perfectamente. Por eso `Seccion` lleva DOS campos: `saltable` (se ofrece el
botón) y `sintetizar` (vale la pena tener el audio). La prosa se salta pero se
sintetiza; la lista de cifras se salta y no se sintetiza.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# LO QUE SE MIDE EN CADA LÍNEA
#
# Nada de esto se invento: salio de pasar el motor por los siete libros de
# prueba y mirar en que se diferencian las paginas de indice de las de novela.

# «Seres organicos e inorganicos .................... 101»
# Los puntos de relleno son la firma del indice de contenidos, y no aparecen
# en prosa jamas. Es la senal mas limpia que hay en todo este archivo.
_RELLENO = re.compile(r"\.{3,}\s*\d*\s*$")

# «Capitulo 3       47»  — indice sin puntos, solo el numero al final pegado
# a un titulo corto. Se exige que la linea sea CORTA: una frase larga que
# acabe en una cifra es prosa normal («…y eso paso en 1936»).
_TITULO_Y_PAGINA = re.compile(r"^.{1,60}?\s{2,}\d{1,4}\s*$")

# «Asesinato: 709, 746-749, 757-758a, 765, 861, 946a.»
# La entrada de un indice alfabetico: palabra, dos puntos, y a partir de ahi
# casi todo cifras.
_ENTRADA_ALFABETICA = re.compile(r"^\s*[^\W\d_][^:\n]{0,60}:\s*\S")

_CIFRA = re.compile(r"\d")
_NO_ESPACIO = re.compile(r"\S")

# La senal mas limpia de todo el archivo, y la unica que se MIDIO antes de
# elegir el umbral. Una linea de indice no solo lleva cifras: lleva punto y
# coma y parentesis, porque cada entrada es «(matiz) 123, 456; (otro) 789».
# La prosa no hace eso nunca.
#
#   linea de indice alfabetico   p05=0,202   mediana=0,434   p95=0,730
#   cuerpo del mismo libro       p95=0,056
#   prosa de cuatro novelas      p95=0,024
#
# (1.132 lineas de indice, 4.814 de cuerpo y 15.621 de novela, medidas sobre
# los libros de prueba.) El umbral va en 0,15: deja un factor de casi cuatro
# de margen a cada lado, que es lo que hace falta para no tener que volver a
# tocarlo cuando llegue un libro raro.
_REFERENCIA = re.compile(r"[\d;()]")

# Palabras que solo salen en la pagina de creditos. Se exige MAS DE UNA para
# no marcar un capitulo que mencione de pasada un ISBN.
_SENAS_CREDITOS = (
    "isbn", "issn", "copyright", "©", "todos los derechos reservados",
    "deposito legal", "depósito legal", "printed in", "impreso en",
    "reservados todos los derechos", "queda prohibida la reproduccion",
    "queda prohibida la reproducción", "primera edicion", "primera edición",
)

# Cabeceras. NO bastan por si solas —en «Medea» la palabra ÍNDICE aparece
# DENTRO del indice, como una entrada mas— pero suben la confianza cuando el
# contenido que viene detras ya apuntaba en esa direccion.
_CABECERAS = (
    ("alfabetico", re.compile(r"^\W*[íi]ndice\s+(alfab[eé]tic|anal[íi]tic|"
                              r"de\s+materias|tem[aá]tic)", re.I)),
    ("bibliografia", re.compile(r"^\W*(bibliograf[íi]a|referencias|"
                                r"obras\s+citadas|fuentes)\b", re.I)),
    ("notas", re.compile(r"^\W*(notas|notas\s+del?\s+\w+)\s*$", re.I)),
    ("contenidos", re.compile(r"^\W*([íi]ndice|contenidos?|sumario|"
                              r"tabla\s+de\s+contenidos?)\s*\d*\s*$", re.I)),
)

# ─────────────────────────────────────────────────────────────────────────────
# LOS UMBRALES, y por que cada uno vale lo que vale

# Por debajo de esto no es una seccion, es una tabla dentro de un capitulo.
# Doce lineas es aproximadamente media pagina: un indice de verdad nunca es
# mas corto, y una tabla suelta casi nunca es mas larga.
RACHA_MINIMA = 12

# Dentro de un indice hay lineas que no cumplen el patron (la letra «A» que
# encabeza su grupo, una linea en blanco, un numero de pagina suelto). Se
# permiten hasta tres seguidas sin romper la racha.
HUECO_MAXIMO = 3

# Una linea con mas de este porcentaje de cifras no es prosa. La prosa
# normal, incluso hablando de fechas, no pasa del 4%; las entradas del indice
# de Kardec estan entre el 30% y el 60%.
CIFRAS_MINIMAS = 0.15

# Ver la nota de `_REFERENCIA`: este umbral no se eligio a ojo, se midio.
REFERENCIAS_MINIMAS = 0.15

# Los creditos solo se buscan al principio del libro, y las secciones de
# cierre solo en el ultimo tercio. La posicion es una comprobacion barata que
# evita casi todos los falsos positivos que quedan.
ZONA_CREDITOS = 0.08
ZONA_CIERRE = 0.55

# Las notas al final de un libro pueden ocupar MEDIO libro —en «Medea» son las
# paginas 67 a 141 de 141— asi que su cabecera cae mucho antes del 55%. Para
# ellas el listón es mas bajo, pero a cambio se exige que la seccion llegue
# HASTA EL FINAL: eso es lo que distingue una seccion de cierre de un capitulo
# que se llame «Notas».
ZONA_NOTAS = 0.30

# Los creditos caben en una pagina. Si el racimo de senas se estira mas que
# esto, es que se estan juntando cosas que no van juntas.
CREDITOS_HUECO = 15
CREDITOS_MAXIMO = 40

# Un indice llega partido en trozos: los numeros de pagina y las lineas en
# blanco rompen la racha cada pocas decenas de lineas. En Kardec salieron 17
# pedazos de lo que es UN indice, y el lector quiere UN boton, no diecisiete.
# Se vuelven a juntar si el hueco entre ellos es pequeno y no hay prosa en
# medio.
COSER_HUECO = 30
COSER_PROSA_MAXIMA = 4

# Para el indice sin puntos de relleno: cuanto se mira hacia delante desde la
# cabecera, cuantas lineas seguidas sin numero de pagina lo dan por terminado,
# y que proporcion hay que superar para creerselo.
INDICE_VENTANA = 400
INDICE_SECO = 15
INDICE_CON_PAGINA = 0.35


@dataclass
class Seccion:
    """Un tramo que la mayoría de la gente se salta.

    `saltable` es si se ofrece el botón. `sintetizar` es si vale la pena tener
    el audio: la prosa sí, una lista de cifras no. Los dos son independientes
    a propósito — ver el encabezado del archivo.
    """
    clase: str          # creditos | contenidos | alfabetico | bibliografia | notas
    titulo: str         # lo que se le enseña al lector: «Saltar índice»
    primera: int        # primera línea, índice en texto.splitlines()
    ultima: int         # última línea, INCLUSIVE
    inicio: int         # primer carácter, para quien trabaje con posiciones
    fin: int            # último carácter, exclusive
    saltable: bool
    sintetizar: bool
    razon: str          # por qué se marcó; sale en los informes


TITULOS = {
    "creditos": "Saltar créditos",
    "contenidos": "Saltar índice",
    "alfabetico": "Saltar índice alfabético",
    "bibliografia": "Saltar bibliografía",
    "notas": "Saltar notas",
}


def _densidad_cifras(linea: str) -> float:
    cuerpo = _NO_ESPACIO.findall(linea)
    if not cuerpo:
        return 0.0
    return len(_CIFRA.findall(linea)) / len(cuerpo)


def _densidad_referencias(linea: str) -> float:
    """Cuánto de esta línea son cifras, puntos y coma y paréntesis."""
    cuerpo = _NO_ESPACIO.findall(linea)
    if not cuerpo:
        return 0.0
    return len(_REFERENCIA.findall(linea)) / len(cuerpo)


def _es_linea_de_lista(linea: str) -> bool:
    """Si esta línea tiene pinta de índice y no de prosa."""
    l = linea.strip()
    if not l:
        return False
    if _RELLENO.search(l):
        return True
    if _TITULO_Y_PAGINA.match(l) and len(l) <= 70:
        return True
    if _densidad_cifras(l) >= CIFRAS_MINIMAS and _ENTRADA_ALFABETICA.match(l):
        return True
    # Las lineas de continuacion del indice no llevan los dos puntos: siguen
    # la entrada anterior. Lo que las delata es la densidad de referencias.
    return _densidad_referencias(l) >= REFERENCIAS_MINIMAS


def _rachas(lineas: list[str]) -> list[tuple[int, int]]:
    """Tramos de líneas con forma de lista, tolerando huecos pequeños."""
    salida: list[tuple[int, int]] = []
    inicio = ultima_buena = None
    hueco = 0
    for i, l in enumerate(lineas):
        if _es_linea_de_lista(l):
            if inicio is None:
                inicio = i
            ultima_buena = i
            hueco = 0
        elif inicio is not None:
            hueco += 1
            if hueco > HUECO_MAXIMO:
                salida.append((inicio, ultima_buena))
                inicio = ultima_buena = None
                hueco = 0
    if inicio is not None:
        salida.append((inicio, ultima_buena))
    return [(a, b) for a, b in salida if b - a + 1 >= RACHA_MINIMA]


def _cabecera_cerca(lineas: list[str], i: int, cuantas: int = 6) -> str | None:
    """Busca hacia atrás una cabecera que diga qué es este tramo."""
    for j in range(max(0, i - cuantas), i + 1):
        for clase, patron in _CABECERAS:
            if patron.match(lineas[j].strip()):
                return clase
    return None


def _creditos(lineas: list[str], offsets: list[int]) -> Seccion | None:
    """La página de créditos: ISBN, editorial, depósito legal, teléfonos.

    OJO CON LO OBVIO, que aquí falla: no se puede coger «de la primera seña a
    la última». En Kardec las señas aparecen salpicadas por las 1.295 primeras
    líneas, y de la primera a la última hay 334 — que se tragaban el índice de
    contenidos entero. Hay que quedarse con el RACIMO más apretado.
    """
    tope = max(6, int(len(lineas) * ZONA_CREDITOS))
    marcadas = [i for i, l in enumerate(lineas[:tope])
                if any(s in l.lower() for s in _SENAS_CREDITOS)]
    if len(marcadas) < 2:
        return None

    racimos: list[list[int]] = [[marcadas[0]]]
    for i in marcadas[1:]:
        if i - racimos[-1][-1] <= CREDITOS_HUECO:
            racimos[-1].append(i)
        else:
            racimos.append([i])
    mejor = max(racimos, key=len)
    if len(mejor) < 2:
        return None

    a, b = max(0, mejor[0] - 4), min(len(lineas) - 1, mejor[-1] + 4)
    if b - a + 1 > CREDITOS_MAXIMO:
        b = a + CREDITOS_MAXIMO - 1
    return Seccion(
        clase="creditos", titulo=TITULOS["creditos"],
        primera=a, ultima=b,
        inicio=offsets[a], fin=offsets[b] + len(lineas[b]),
        saltable=True, sintetizar=False,
        razon=f"{len(mejor)} señas de créditos juntas")


_ACABA_EN_PAGINA = re.compile(r"\d{1,4}\s*$")


def _indice_bajo_cabecera(lineas: list[str],
                          offsets: list[int]) -> list[Seccion]:
    """El índice de contenidos que NO lleva puntos de relleno.

    «El libro de los médiums» tiene un índice perfectamente normal que ninguna
    medida por línea encuentra: sin puntos, con las entradas partidas en varias
    líneas y el número de página al final de la última.

        CAPÍTULO I - ¿Hay Espíritus? 12
        CAPÍTULO II - Lo Maravilloso y lo sobrenatural. 19
        SEGUNDA PARTE
        De las manifestaciones espiritistas

    Cada línea por separado no dice nada —densidad de referencias entre 0,04 y
    0,10, igual que la prosa—. Lo que lo delata es el BLOQUE: bajo una cabecera
    que pone «ÍNDICE», dos de cada tres líneas acaban en un número de página.
    La prosa no hace eso ni por casualidad.
    """
    salida: list[Seccion] = []
    for i, linea in enumerate(lineas):
        clase = None
        for c, patron in _CABECERAS:
            if c == "contenidos" and patron.match(linea.strip()):
                clase = c
                break
        if clase is None:
            continue
        fin, seco, con_pagina, cuantas = i, 0, 0, 0
        for j in range(i + 1, min(len(lineas), i + INDICE_VENTANA)):
            if not lineas[j].strip():
                continue
            cuantas += 1
            if _ACABA_EN_PAGINA.search(lineas[j]):
                con_pagina += 1
                seco = 0
                fin = j
            else:
                seco += 1
                if seco > INDICE_SECO:
                    break
        if cuantas < RACHA_MINIMA or con_pagina / cuantas < INDICE_CON_PAGINA:
            continue
        salida.append(Seccion(
            clase="contenidos", titulo=TITULOS["contenidos"],
            primera=i, ultima=fin,
            inicio=offsets[i], fin=offsets[fin] + len(lineas[fin]),
            saltable=True, sintetizar=False,
            razon=f"bajo la cabecera «{linea.strip()[:20]}», "
                  f"{con_pagina}/{cuantas} líneas acaban en número de página"))
    return salida


def _por_cabecera(lineas: list[str], offsets: list[int]) -> list[Seccion]:
    """Secciones que NO tienen forma de lista, pero se anuncian con su nombre.

    Las notas de Eurípides son medio libro de prosa corrida: ninguna medida de
    cifras o de puntos de relleno las encuentra jamás. Lo único que las delata
    es que hay una línea que pone «Notas» y que a partir de ahí no vuelve a
    empezar nada. Se exige que esté en el último tramo del libro, porque
    «NOTAS» al 3% es una entrada del índice, no la sección.
    """
    total = len(lineas)
    salida: list[Seccion] = []
    for i, linea in enumerate(lineas):
        if i / total <= ZONA_NOTAS:
            continue
        for clase, patron in _CABECERAS:
            if clase not in ("notas", "bibliografia"):
                continue
            if not patron.match(linea.strip()):
                continue
            # Hasta el final, o hasta la siguiente cabecera de este tipo.
            fin = total - 1
            for j in range(i + 1, total):
                if any(p.match(lineas[j].strip())
                       for c, p in _CABECERAS if c in ("notas", "bibliografia")):
                    fin = j - 1
                    break
            if fin - i + 1 < RACHA_MINIMA:
                continue
            # Tiene que llegar al final. Si detras vuelve a haber libro, esto
            # era un capitulo llamado «Notas», no la seccion de notas.
            if total - 1 - fin > RACHA_MINIMA:
                continue
            salida.append(Seccion(
                clase=clase, titulo=TITULOS[clase],
                primera=i, ultima=fin,
                inicio=offsets[i], fin=offsets[fin] + len(lineas[fin]),
                saltable=True, sintetizar=False,
                razon=f"cabecera «{linea.strip()[:24]}» al {i/total:.0%} "
                      f"del libro, {fin - i + 1} líneas hasta el final"))
            break
    return salida


def detectar(texto: str) -> list[Seccion]:
    """Todas las secciones saltables de un libro, en orden de aparición."""
    lineas = texto.splitlines()
    if len(lineas) < RACHA_MINIMA * 2:
        return []

    offsets, pos = [], 0
    for l in lineas:
        offsets.append(pos)
        pos += len(l) + 1

    encontradas: list[Seccion] = []
    cred = _creditos(lineas, offsets)
    if cred:
        encontradas.append(cred)

    total = len(lineas)
    for a, b in _rachas(lineas):
        clase = _cabecera_cerca(lineas, a)
        sitio = a / total
        if clase is None:
            # Sin cabecera, solo la posicion puede decidir, y solo en los dos
            # extremos del libro. En medio, una racha de cifras es una tabla
            # de un capitulo y NO se toca.
            if sitio < ZONA_CREDITOS:
                clase = "contenidos"
            elif sitio > ZONA_CIERRE:
                clase = "alfabetico"
            else:
                continue
        # Una cabecera de «contenidos» en el ultimo tercio del libro es casi
        # siempre un indice alfabetico mal etiquetado.
        if clase == "contenidos" and sitio > ZONA_CIERRE:
            clase = "alfabetico"
        encontradas.append(Seccion(
            clase=clase, titulo=TITULOS[clase],
            primera=a, ultima=b,
            inicio=offsets[a], fin=offsets[b] + len(lineas[b]),
            saltable=True, sintetizar=False,
            razon=f"{b - a + 1} líneas con forma de lista"
                  + (f", bajo la cabecera «{clase}»" if _cabecera_cerca(lineas, a)
                     else f", al {sitio:.0%} del libro")))

    encontradas.extend(_indice_bajo_cabecera(lineas, offsets))
    encontradas.extend(_por_cabecera(lineas, offsets))
    encontradas.sort(key=lambda s: s.primera)
    return _coser(_sin_solapes(encontradas), lineas)


def _sin_solapes(secciones: list[Seccion]) -> list[Seccion]:
    """Si dos tramos se pisan, se quedan como uno solo."""
    salida: list[Seccion] = []
    for s in secciones:
        if salida and s.primera <= salida[-1].ultima + HUECO_MAXIMO:
            previa = salida[-1]
            previa.ultima = max(previa.ultima, s.ultima)
            previa.fin = max(previa.fin, s.fin)
            continue
        salida.append(s)
    return salida


def _coser(secciones: list[Seccion], lineas: list[str]) -> list[Seccion]:
    """Junta los pedazos de una misma sección en uno solo.

    El índice alfabético de Kardec llegaba aquí en DIECISIETE trozos, partido
    por los números de página y las líneas en blanco. Al lector hay que
    ofrecerle un botón, no diecisiete. Se cosen dos trozos de la misma clase
    si el hueco es pequeño y si en ese hueco no hay prosa de verdad — esa
    última condición es la que impide coser por encima de un capítulo.
    """
    salida: list[Seccion] = []
    for s in secciones:
        if not salida:
            salida.append(s)
            continue
        previa = salida[-1]
        hueco = s.primera - previa.ultima - 1
        if previa.clase == s.clase and 0 <= hueco <= COSER_HUECO:
            # «Larga» no basta: las entradas del índice alfabético pasan de
            # sobra los 60 caracteres. Prosa es larga Y con pocas cifras.
            enmedio = [l for l in lineas[previa.ultima + 1:s.primera]
                       if len(l.strip()) > 60
                       and _densidad_referencias(l) < REFERENCIAS_MINIMAS]
            if len(enmedio) <= COSER_PROSA_MAXIMA:
                previa.ultima = s.ultima
                previa.fin = s.fin
                previa.razon = (f"{previa.ultima - previa.primera + 1} líneas "
                                f"con forma de lista (cosidas de varios trozos)")
                continue
        salida.append(s)
    return salida


def marcar_prosa(secciones: list[Seccion], texto: str) -> list[Seccion]:
    """Reconsidera: lo que resultó ser prosa se salta, pero SÍ se sintetiza.

    Las notas de Eurípides se parecen a una bibliografía por dónde están y por
    la cabecera, pero son párrafos que se entienden dichos en voz alta. Quien
    quiera oírlas, puede; el botón sigue ahí para quien no.
    """
    lineas = texto.splitlines()
    for s in secciones:
        # Los creditos y los indices no se reconsideran: un ISBN y una lista
        # de referencias no mejoran por estar rodeados de lineas largas.
        if s.clase in ("creditos", "contenidos", "alfabetico"):
            continue
        cuerpo = [l for l in lineas[s.primera:s.ultima + 1] if l.strip()]
        if not cuerpo:
            continue
        largas = sum(1 for l in cuerpo if len(l.strip()) > 60)
        pocas_cifras = sum(1 for l in cuerpo
                           if _densidad_cifras(l) < CIFRAS_MINIMAS)
        if largas / len(cuerpo) > 0.6 and pocas_cifras / len(cuerpo) > 0.6:
            s.sintetizar = True
            s.razon += " — pero es prosa: se salta, no se borra"
    return secciones


# ─────────────────────────────────────────────────────────────────────────────
# DE SECCIONES A PARTES
#
# El detector habla de lineas y de caracteres del libro entero. Los dos
# proyectos trabajan por PARTES —trozos de unos pocos miles de caracteres, que
# es lo que se sintetiza y lo que se pagina—, asi que hay que traducir.
#
# La traduccion no es exacta a proposito: una parte casi nunca cae entera
# dentro de una seccion, porque los cortes se hacen por frases y no por
# secciones. Se marca la parte cuando la seccion se lleva LA MAYORIA de ella.
# Marcar de menos deja unos segundos de indice al principio o al final; marcar
# de mas se come el principio de un capitulo.

CUBRE_PARTE = 0.60


@dataclass
class ParteMarcada:
    """Una parte del libro, con lo que hay que saber para pintar el botón."""
    indice: int
    clase: str | None = None
    titulo: str | None = None
    sintetizar: bool = True
    salta_a: int | None = None      # a qué parte lleva el botón


def _limites(texto: str, trozos: list[str]) -> list[tuple[int, int]]:
    """Dónde empieza y acaba cada trozo dentro del texto original.

    No se puede ir sumando longitudes: quien parte el libro hace `.strip()` en
    cada trozo, así que los espacios de los bordes desaparecen y la cuenta se
    desvía un poco más en cada corte. Se busca cada trozo por su principio.
    """
    salida, cursor = [], 0
    for t in trozos:
        cabeza = t[:60]
        i = texto.find(cabeza, cursor) if cabeza else -1
        if i < 0:
            i = cursor
        salida.append((i, i + len(t)))
        cursor = i + len(t)
    return salida


def repartir(texto: str, trozos: list[str],
             secciones: list[Seccion]) -> list[ParteMarcada]:
    """Qué parte cae dentro de qué sección, y adónde lleva el botón."""
    limites = _limites(texto, trozos)
    partes = [ParteMarcada(indice=i) for i in range(len(trozos))]
    for s in secciones:
        dentro = []
        for i, (a, b) in enumerate(limites):
            largo = b - a
            if largo <= 0:
                continue
            solape = max(0, min(b, s.fin) - max(a, s.inicio))
            if solape / largo >= CUBRE_PARTE:
                dentro.append(i)
        if not dentro:
            continue
        siguiente = dentro[-1] + 1
        for i in dentro:
            partes[i].clase = s.clase
            partes[i].titulo = s.titulo
            partes[i].sintetizar = s.sintetizar
            partes[i].salta_a = siguiente if siguiente < len(trozos) else None
    return partes


def como_json(secciones: list[Seccion],
              partes: list[ParteMarcada]) -> dict:
    """Lo que se guarda junto al libro y lee el cliente."""
    return {
        "secciones": [
            {"clase": s.clase, "titulo": s.titulo,
             "inicio": s.inicio, "fin": s.fin,
             "sintetizar": s.sintetizar, "razon": s.razon}
            for s in secciones
        ],
        "partes": {
            str(p.indice): {"clase": p.clase, "titulo": p.titulo,
                            "sintetizar": p.sintetizar, "saltaA": p.salta_a}
            for p in partes if p.clase
        },
    }
