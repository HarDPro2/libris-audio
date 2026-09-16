"""Las secciones saltables — con los fragmentos REALES de los libros de prueba.

Todo lo que se comprueba aquí salió de pasar el detector por los siete libros
de la carpeta LIBROS, no de imaginar cómo sería un índice. Los fragmentos van
pegados como literales para que la prueba no dependa de tener los PDF a mano.

LO QUE MÁS IMPORTA DE ESTE ARCHIVO son las pruebas de que NO se marca nada.
Un falso negativo cuesta unos minutos de audio aburrido; un falso positivo se
come un capítulo, y el lector no se entera hasta que la historia deja de tener
sentido.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from secciones import (detectar, marcar_prosa, repartir, como_json,
                              _densidad_referencias, _densidad_aparato,
                              RACHA_MINIMA, REFERENCIAS_MINIMAS,
                              APARATO_MINIMO)

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


# ── Fragmentos reales ────────────────────────────────────────────────────────

ALFABETICO = [
    'Civilización: Int. II, 59, 102, 271, 272, 674, 707, 717, 755, 757, 762,',
    '795, 822a, 837, 916, 926, 928a, 933, 955, Conc. IV.',
    'Clarividencia: Int. XVI, 402, 428-433, 455.',
    'Clasificación: (de la ley de Dios) 648; (de los adversarios) Conc. II.',
    'Cobardía: 332, 759a, 866, 956.',
    'Combates: 483, 541-548, 757, 857.',
    'Cometas: 40.',
    '579',
    'Compasión: 222, 304, 749, 918, 1001.',
    'Comportamiento (v.t. conducta): (de los niños) Int. XV; (del hombre) 629,',
    'Comprensión: (de la justicia) 743, 762, 795, 885, 1009; (de la ley) 61,',
    '776, 794, 805, 828, Conc. IV; (de la verdad) 111, 145, 165, 923;',
    '637, 638, 670, 756, 780, 784, 817, 830, 977a, 990.',
    'Comunicaciones: (con el Espíritu familiar) 495; (durante el dormir) 402,',
    'Conciencia: (voz de la) 621, 835, 919a; (libertad de) 837, 838, 876.',
    'Cuerpo: (y alma) 135, 136a, 344-360; (perispíritu y) 93, 94, 135a.',
]

CONTENIDOS_CON_PUNTOS = [
    'Introducción al estudio de la doctrina espírita .........................19',
    'Prolegómenos..................................................................',
    'Libro Primero',
    'Las Causas Primeras',
    'Capítulo I – Dios',
    'Dios y lo infinito............................................................',
    'Pruebas de la existencia de Dios .............................................',
    'Atributos de la Divinidad.....................................................',
    'Panteísmo ....................................................................',
    'Capítulo II – Elementos Generales del Universo',
    'Conocimiento del principio de las cosas.................................... 81',
    'Espíritu y materia ...........................................................',
    'Propiedades de la materia ....................................................',
    'Espacio universal ............................................................',
    'Capítulo III – Creación',
    'Formación de los mundos ......................................................',
]

# El de «El libro de los médiums»: SIN puntos de relleno. Ninguna medida por
# linea lo encuentra —cada una parece prosa— y sin embargo dos de cada tres
# acaban en un numero de pagina.
CONTENIDOS_SIN_PUNTOS = [
    'ÍNDICE',
    'Introducción 7',
    'PRIMERA PARTE',
    'Nociones preliminares',
    'CAPÍTULO I - ¿Hay Espíritus? 12',
    'CAPÍTULO II - Lo Maravilloso y lo sobrenatural. 19',
    'CAPÍTULO III - Método. 29',
    'CAPÍTULO IV - Sistemas. 42',
    'SEGUNDA PARTE',
    'De las manifestaciones espiritistas',
    'CAPÍTULO I - Acción de los Espíritus sobre la materia. 61',
    'CAPÍTULO II - Manifestaciones físicas. - Mesas giratorias. 68',
    'CAPÍTULO III - Manifestaciones inteligentes. 72',
    'CAPÍTULO IV - Teoría de las manifestaciones físicas. 80',
    'CAPÍTULO V - De los médiums. 95',
    'CAPÍTULO VI - De las apariciones. 120',
    'CAPÍTULO VII - Bi-corporeidad y transfiguración. 135',
    'CAPÍTULO VIII - Laboratorio del mundo invisible. 145',
]

CREDITOS = [
    'DATOS INTERNACIONALES PARA CATALOGACIÓN EN LA FUENTE – CIP',
    'Copyright © 2008 by',
    'CONSEJO ESPÍRITA INTERNACIONAL',
    'SGAN Q. 909 – Conjunto F',
    '70790-090 – Brasilia (DF) – Brasil',
    'Todos los derechos reservados. Ninguna parte de esta publicación puede',
    'almacenada o transmitida, total o parcialmente, por cualquier método o',
    'autorización del poseedor del copyright.',
    'ISBN edición impresa: 978-85-98161-66-2',
    'Título del original en francés:',
    'LE LIVRE DES ESPRITS',
    '(Paris, 1857)',
]

PROSA = [
    'eléctrica convirtiéndole a uno, incluso contra su voluntad, en un loco',
    'y vociferante. Y sin embargo, la rabia que se sentía era una emoción',
    'indirecta que podía aplicarse a uno u otro objeto como la llama de una',
    'soldadura autógena. Así, en un momento determinado, el odio de Winston',
    'dirigía contra Goldstein, sino contra el propio Gran Hermano, contra el',
    'contra la Policía del Pensamiento; y entonces su corazón estaba de parte',
    'solitario e insultado hereje de la pantalla, único guardián de la verdad',
    'en un mundo de mentiras. Pero al instante siguiente, se hallaba',
    'completo con la gente que le rodeaba y le parecía verdad todo lo que',
    'Goldstein. Entonces, su odio contra el Gran Hermano se transformaba en',
    'adoración, y el Gran Hermano se elevaba como una invencible torre, como',
    'valiente roca capaz de resistir los ataques de las hordas asiáticas, y',
]

# El falso positivo que mas miedo da: un capitulo de historia, lleno de
# fechas y de cifras, que NO es un indice y que no se puede tocar.
CAPITULO_CON_CIFRAS = [
    'En 1914 estalló la guerra y en 1918 se firmó el armisticio de Compiègne.',
    'Los 37 batallones que salieron de Verdún en febrero de 1916 no volvieron',
    'nunca: de los 12.000 hombres apenas regresaron 800, y de esos 800 más de',
    'la mitad quedó inútil para el servicio. El 11 de noviembre, a las 11 de',
    'la mañana, los cañones callaron por primera vez en 1.560 días seguidos.',
    'El tratado se firmó en 1919, en el salón de los espejos, ante 70 testigos',
    'y con 440 artículos que nadie llegó a leer entero. Keynes calculó que las',
    'reparaciones —132.000 millones de marcos oro— eran imposibles de pagar,',
    'y publicó en 1919 un libro de 298 páginas explicando por qué. Tardaron 20',
    'años en darle la razón, y para entonces ya había empezado la siguiente.',
]

# Las notas de Euripides: van al final, se llaman «Notas», la gente se las
# salta... pero son PROSA, y dichas en voz alta se entienden perfectamente.
NOTAS_EN_PROSA = [
    'Notas',
    '[1] La obra de M. Victor Duruy, titulada Histoire Grecque, que hemos',
    'tenido a la vista, es algo parcial por la democracia, cuya defensa',
    'parece ser uno de sus principales objetos. Habla siempre de',
    'Aristófanes con pasión y con odio, acaso porque no ha sabido',
    'apreciar sus relevantes dotes como poeta y como ciudadano, y',
    'porque combate los excesos de la demagogia. Fuera de esto, es',
    'obra recomendable, si bien no debemos olvidarlo, porque anda en',
    'manos de todos. Al leerla, dentro de algunos años, dirá, sin duda, la',
    'posteridad que aquel autor escribía la historia de su propio tiempo',
    'con la pasión de quien la ha vivido y no con la calma de quien la',
    'estudia, que es defecto común a cuantos narran lo que han visto.',
    '[2] El texto que seguimos es el de la edición de Oxford, cotejado',
    'con la de Leipzig, que en algunos pasajes nos ha parecido preferible.',
    'No hemos querido cargar de notas eruditas una traducción que aspira',
    'sobre todo a ser leída, y que por eso se detiene donde el lector común',
    'dejaría de seguirnos con gusto.',
]


def _partir(texto: str, tope: int) -> list[str]:
    """Un partidor de mentira, igual de tosco que el de verdad: corta por la
    frase más cercana y hace `.strip()` — que es justo lo que descuadra las
    cuentas si alguien intenta seguir las posiciones sumando longitudes."""
    trozos, resto = [], texto
    while len(resto) > tope:
        corte = resto.rfind("\n", 0, tope) or tope
        trozos.append(resto[:corte].strip())
        resto = resto[corte:].strip()
    if resto:
        trozos.append(resto)
    return trozos


def libro(*, antes=0, bloque=(), despues=0, relleno=None):
    """Monta un libro de mentira con el bloque en su sitio.

    La posición importa: el detector no marca una racha de cifras que esté en
    mitad del libro, porque ahí una tabla es una tabla.
    """
    relleno = relleno or PROSA
    def paja(n):
        return [relleno[i % len(relleno)] for i in range(n)]
    return "\n".join(paja(antes) + list(bloque) + paja(despues))


print("La señal que se MIDIÓ, no se estimó:")
# Medido sobre los libros de prueba (1.132 líneas de índice, 4.814 de cuerpo
# y 15.621 de novela):
#     índice alfabético   p05=0,202  mediana=0,434  p95=0,730
#     cuerpo del libro    p95=0,056
#     prosa de novela     p95=0,024
#
# PERO LAS COLAS SE SOLAPAN, y eso hay que decirlo en vez de esconderlo.
# Midiendo línea a línea los fragmentos de abajo:
#     entradas de índice      de 0,136 a 0,492  (dos de ocho por DEBAJO de 0,15)
#     prosa cargada de fechas de 0,000 a 0,186  (dos de diez por ENCIMA)
#
# O sea: ninguna línea suelta decide nada. Lo que salva al detector no es el
# umbral, son las otras dos reglas — que hagan falta DOCE líneas seguidas y
# que estén en un extremo del libro. Las tres pruebas de aquí abajo miden
# justo eso, y no lo que a uno le gustaría que pasara.
pasan = [l for l in ALFABETICO if len(l) > 40 and ':' in l
         and _densidad_referencias(l) >= REFERENCIAS_MINIMAS]
total = [l for l in ALFABETICO if len(l) > 40 and ':' in l]
prueba("la mayoría de las entradas de índice pasan el umbral",
       len(pasan) / len(total) >= 0.70, f"{len(pasan)}/{len(total)}")
prueba("la prosa de una novela no lo pasa, ni de lejos",
       max(_densidad_referencias(l) for l in PROSA) < REFERENCIAS_MINIMAS / 2,
       max(_densidad_referencias(l) for l in PROSA))
sueltas = sum(1 for l in CAPITULO_CON_CIFRAS
              if _densidad_referencias(l) >= REFERENCIAS_MINIMAS)
prueba("la prosa con fechas asoma por encima, pero solo a ratos",
       sueltas <= len(CAPITULO_CON_CIFRAS) // 4, f"{sueltas} líneas")
prueba("y NUNCA doce seguidas, que es lo que hace falta para marcar",
       max((sum(1 for _ in g) for g in __import__("itertools").groupby(
           _densidad_referencias(l) >= REFERENCIAS_MINIMAS
           for l in CAPITULO_CON_CIFRAS) if g[0]), default=0) < RACHA_MINIMA)

print("\nLo que SÍ se marca:")
s = detectar(libro(antes=40, bloque=ALFABETICO, despues=4))
prueba("el índice alfabético del final",
       len(s) == 1 and s[0].clase == "alfabetico", [(x.clase) for x in s])
prueba("y no se sintetiza", s and not s[0].sintetizar)

s = detectar(libro(antes=3, bloque=CONTENIDOS_CON_PUNTOS, despues=200))
prueba("el índice con puntos de relleno",
       any(x.clase == "contenidos" for x in s), [(x.clase) for x in s])

s = detectar(libro(antes=3, bloque=CONTENIDOS_SIN_PUNTOS, despues=200))
prueba("el índice SIN puntos, por el bloque entero",
       any(x.clase == "contenidos" for x in s), [(x.clase) for x in s])

s = detectar(libro(antes=2, bloque=CREDITOS, despues=300))
cred = [x for x in s if x.clase == "creditos"]
prueba("la página de créditos", len(cred) == 1, [(x.clase) for x in s])
prueba("y cabe en una página, no se estira",
       cred and cred[0].ultima - cred[0].primera + 1 <= 40,
       cred and cred[0].ultima - cred[0].primera + 1)

print("\nLo que NO se marca — lo importante de este archivo:")
prueba("una novela entera, sin secciones",
       detectar("\n".join(PROSA * 30)) == [], detectar("\n".join(PROSA * 30)))
prueba("un capítulo lleno de fechas NO es un índice",
       detectar(libro(antes=60, bloque=CAPITULO_CON_CIFRAS, despues=60)) == [],
       [x.clase for x in
        detectar(libro(antes=60, bloque=CAPITULO_CON_CIFRAS, despues=60))])
corta = ALFABETICO[:RACHA_MINIMA - 4]
prueba("una tabla corta dentro de un capítulo se deja en paz",
       detectar(libro(antes=60, bloque=corta, despues=60)) == [],
       [x.clase for x in detectar(libro(antes=60, bloque=corta, despues=60))])
prueba("una racha de cifras EN MITAD del libro no se toca",
       detectar(libro(antes=100, bloque=ALFABETICO, despues=100)) == [],
       [x.clase for x in
        detectar(libro(antes=100, bloque=ALFABETICO, despues=100))])
prueba("una sola seña de créditos no basta",
       detectar(libro(antes=2, bloque=['ISBN 978-84-376-0494-7'],
                      despues=300)) == [])

print("\nProsa que se salta pero SÍ se dice — la distinción que importa:")
texto = libro(antes=60, bloque=NOTAS_EN_PROSA, despues=0)
s = marcar_prosa(detectar(texto), texto)
notas = [x for x in s if x.clase == "notas"]
prueba("las notas del final se detectan", len(notas) == 1,
       [(x.clase) for x in s])
prueba("pero se sintetizan: son párrafos, no una lista de cifras",
       notas and notas[0].sintetizar)
prueba("y aun así llevan su botón", notas and notas[0].saltable)
texto = libro(antes=40, bloque=ALFABETICO, despues=4)
s = marcar_prosa(detectar(texto), texto)
prueba("el índice NO se reconsidera por muchas líneas largas que tenga",
       s and not s[0].sintetizar)

print("\nCada sección sabe dónde está, en líneas y en caracteres:")
texto = libro(antes=40, bloque=ALFABETICO, despues=4)
s = detectar(texto)[0]
prueba("los caracteres cuadran con las líneas",
       texto[s.inicio:s.fin].splitlines()[0]
       == texto.splitlines()[s.primera],
       texto[s.inicio:s.fin][:40])
prueba("el título es el que ve el lector",
       s.titulo == "Saltar índice alfabético", s.titulo)
prueba("y la razón queda escrita, para poder discutirla",
       bool(s.razon), s.razon)

print("\nUna cabecera NO basta — salió de los 98 libros de verdad:")
# Una linea que ponia «Bibliografia» pasado el 30% del libro se llevaba TODO
# lo que venia detras, y aparecieron «bibliografias» que ocupaban el 58% de su
# libro. El audio no se perdia (son prosa), pero el boton habria hecho que el
# lector se saltara 38 capitulos de verdad. Eso es peor que no tener boton.
prueba("las notas de verdad tienen llamadas de nota",
       _densidad_aparato("\n".join(NOTAS_EN_PROSA)) >= APARATO_MINIMO,
       _densidad_aparato("\n".join(NOTAS_EN_PROSA)))
prueba("la prosa de una novela no tiene ninguna",
       _densidad_aparato("\n".join(PROSA * 10)) == 0,
       _densidad_aparato("\n".join(PROSA * 10)))
# Una novela cuyo ultimo capitulo se titule «Notas» no puede llevarse el final
# del libro solo por el titulo.
falsa = ["Notas"] + PROSA * 8
texto = libro(antes=100, bloque=falsa, despues=0)
prueba("una cabecera sin aparato crítico NO marca nada",
       detectar(texto) == [], [x.clase for x in detectar(texto)])
texto = libro(antes=100, bloque=NOTAS_EN_PROSA * 3, despues=0)
prueba("pero con llamadas de nota sí", 
       any(x.clase == "notas" for x in detectar(texto)),
       [x.clase for x in detectar(texto)])

print("\nDe secciones a partes, que es lo que ve la app:")
# Los dos proyectos trabajan por partes de unos miles de caracteres. Una parte
# casi nunca cae ENTERA dentro de una seccion, asi que se marca cuando la
# seccion se lleva la mayoria de ella.
# OJO con el «antes»: el detector no marca una racha que esté en mitad del
# libro, así que el bloque tiene que caer de verdad en el último tramo.
texto = libro(antes=200, bloque=ALFABETICO * 6, despues=2)
secs = detectar(texto)
trozos = [t for t in _partir(texto, 400) if t]
partes = repartir(texto, trozos, secs)
marcadas = [p for p in partes if p.clase]
prueba("las partes del índice quedan marcadas", len(marcadas) >= 1,
       f"{len(marcadas)} de {len(trozos)}")
prueba("y las del principio NO", partes[0].clase is None, partes[0].clase)
prueba("ninguna marcada se sintetiza",
       all(not p.sintetizar for p in marcadas))
prueba("el botón lleva a una parte posterior, o al final",
       all(p.salta_a is None or p.salta_a > p.indice for p in marcadas))
prueba("las partes marcadas van seguidas",
       [p.indice for p in marcadas]
       == list(range(marcadas[0].indice, marcadas[-1].indice + 1)),
       [p.indice for p in marcadas])

j = como_json(secs, partes)
prueba("el JSON lleva las secciones y solo las partes marcadas",
       len(j["secciones"]) == len(secs) and len(j["partes"]) == len(marcadas))
prueba("y cada parte del JSON dice a dónde va el botón",
       all("saltaA" in v and "titulo" in v for v in j["partes"].values()))

texto = libro(antes=60, bloque=(), despues=60)
prueba("un libro sin secciones no marca ninguna parte",
       not [p for p in repartir(texto, _partir(texto, 400), []) if p.clase])

print("\nY lo mismo si el libro se reconstruye desde sus partes:")
# Los libros que ya estaban subidos se arreglan leyendo sus partes de R2 y
# juntandolas otra vez. El texto reconstruido NO es byte a byte el original
# —quien partio el libro hizo `.strip()` en cada trozo— asi que hay que
# comprobar que aun asi sale lo mismo. Si no saliera, un libro arreglado y
# uno recien subido tendrian secciones distintas, y nadie se enteraria.
texto = libro(antes=200, bloque=ALFABETICO * 6, despues=2)
trozos = [t for t in _partir(texto, 400) if t]
rehecho = "\n".join(trozos)
a = [(x.clase, x.sintetizar) for x in marcar_prosa(detectar(texto), texto)]
b = [(x.clase, x.sintetizar) for x in marcar_prosa(detectar(rehecho), rehecho)]
prueba("las mismas secciones que subiendo el libro de cero", a == b, f"{a} vs {b}")
pa = [p.indice for p in repartir(texto, trozos, detectar(texto)) if p.clase]
pb = [p.indice for p in repartir(rehecho, trozos, detectar(rehecho)) if p.clase]
prueba("y las mismas partes marcadas", pa == pb, f"{pa} vs {pb}")

print("\nY con el texto guardado en PÁRRAFOS, que es como llega medio catálogo:")
# EL SESGO QUE TENÍA ESTE ARCHIVO, y que solo se vio al correr el detector
# contra los 98 libros de verdad: los siete PDF de prueba están todos entre 62
# y 85 caracteres por línea, porque vienen del mismo camino de extracción. Los
# que entran por EPUB se guardan en párrafos corridos de MÁS DE MIL
# caracteres, y ahí toda medida por línea es ciega: una entrada de índice
# queda diluida en un párrafo enorme y «doce líneas seguidas» no significa
# nada. De 98 libros, 78 no daban ni una sección por esto.
#
# Por eso los umbrales de solape y de cosido se miden en CARACTERES: una línea
# vale 70 en un libro y 1.360 en otro, un carácter vale lo mismo en los dos.
def en_parrafos(texto, cuantas=18):
    """Junta las líneas de 18 en 18, como queda el texto sin saltos."""
    salida, monton = [], []
    for l in texto.splitlines():
        if not l.strip():
            continue
        monton.append(l.strip())
        if len(monton) >= cuantas:
            salida.append(" ".join(monton))
            monton = []
    if monton:
        salida.append(" ".join(monton))
    return "\n".join(salida)

texto = libro(antes=200, bloque=ALFABETICO * 6, despues=2)
apretado = en_parrafos(texto)
largo = max(len(l) for l in apretado.splitlines())
prueba("el texto de prueba queda de verdad en párrafos largos", largo > 700, largo)
clases = {x.clase for x in detectar(apretado)}
prueba("el índice alfabético se encuentra igual", "alfabetico" in clases, clases)

novela = en_parrafos("\n".join(PROSA * 40))
prueba("y una novela en párrafos sigue sin marcar nada",
       detectar(novela) == [], [x.clase for x in detectar(novela)])

fechas = en_parrafos(libro(antes=100, bloque=CAPITULO_CON_CIFRAS * 3, despues=100))
prueba("ni un capítulo de fechas en párrafos",
       detectar(fechas) == [], [x.clase for x in detectar(fechas)])

# Los puntos de relleno aguantan el aplastado, pero OJO con confundirlos con
# los puntos suspensivos: con el umbral en tres, Hamlet entero salia marcado
# como indice por el dialogo. Son cinco.
conpuntos = en_parrafos(libro(antes=3, bloque=CONTENIDOS_CON_PUNTOS * 3,
                              despues=200))
prueba("el índice con puntos se encuentra aplastado en párrafos",
       any(x.clase == "contenidos" for x in detectar(conpuntos)),
       [x.clase for x in detectar(conpuntos)])
suspensivos = ["—No sé... nunca lo supe... y ya no importa —dijo en voz baja."] * 60
prueba("pero los puntos suspensivos del diálogo NO son un índice",
       detectar(en_parrafos("\n".join(suspensivos))) == [],
       [x.clase for x in detectar(en_parrafos("\n".join(suspensivos)))])

print("\nNada de esto revienta con lo raro:")
for nombre, t in (("texto vacío", ""), ("una línea", "hola"),
                  ("solo saltos", "\n\n\n\n"),
                  ("sin saltos de línea", "palabra " * 500)):
    try:
        detectar(t)
        prueba(nombre, True)
    except Exception as e:
        prueba(nombre, False, repr(e))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
