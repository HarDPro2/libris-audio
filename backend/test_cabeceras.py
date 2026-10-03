"""Las cabeceras de página — con los casos reales de los libros de prueba.

LO QUE MÁS IMPORTA DE ESTE ARCHIVO son las pruebas de que NO se toca nada. El
primer intento —borrar la línea corta que se repite— borraba los nombres de los
personajes de «Medea» y dejaba al oyente sin saber quién habla. Esa es la
prueba que hay que mirar cuando alguien quiera aflojar un umbral.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from cabeceras import (detectar, limpiar, BORDE_MINIMO,
                                    MIN_PAGINAS, ZONA)

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


# El cuerpo tiene que ser DISTINTO en cada página, como en un libro de verdad.
# Con el mismo texto repetido en las 20 páginas, el propio cuerpo se comporta
# igual que un pie de página — y eso hundió la primera versión de estas
# pruebas, que no es culpa del detector sino de un fixture irreal.
def cuerpo(p, cuantas=12):
    return [f"Línea {i} de la página {p}: el Espíritu errante espera una "
            f"nueva encarnación para mejorar." for i in range(cuantas)]


def libro_con_cabeceras(paginas=20):
    """Como Kardec: cabeceras que alternan par/impar y número debajo."""
    return [[("Libro Segundo – Capítulo VI" if p % 2 == 0 else "Vida Espírita"),
             str(180 + p)] + cuerpo(p) for p in range(paginas)]


def obra_de_teatro(paginas=20):
    """Como Medea: los nombres de los personajes, a media página y repetidos."""
    salida = []
    for p in range(paginas):
        pagina = []
        for turno, linea in enumerate(cuerpo(p, 8)):
            pagina.append("MEDEA" if turno % 2 == 0 else "JASÓN")
            pagina.append(linea)
        salida.append(pagina)
    return salida


print("Lo que SÍ se quita:")
paginas = libro_con_cabeceras()
halladas = detectar(paginas)
prueba("las dos cabeceras que alternan",
       {"Libro Segundo – Capítulo VI", "Vida Espírita"} <= set(halladas),
       sorted(halladas))
limpias, informe = limpiar(paginas)
prueba("y desaparecen del texto",
       not any("Vida Espírita" in l for p in limpias for l in p))
prueba("los números de página también", informe.numeros == 20, informe.numeros)
prueba("el cuerpo del libro queda intacto",
       all(limpias[p] == cuerpo(p) for p in range(20)), limpias[0][:2])
prueba("el parte dice qué se quitó, no solo cuánto",
       "Vida Espírita" in informe.resumen(), informe.resumen())

print("\nLo que NO se toca — la prueba que importa:")
teatro = obra_de_teatro()
prueba("los nombres de los personajes de una obra se quedan",
       detectar(teatro) == {}, detectar(teatro))
limpias, informe = limpiar(teatro)
prueba("y la obra sale entera", limpias == teatro)
prueba("sin quitar ni una línea", informe.total == 0, informe.total)

# «—Sí.» sale 17 veces en «1984», a media página y varias por página.
dialogo = []
for p in range(20):
    pagina = []
    for linea in cuerpo(p, 8):
        pagina += [linea, "—Sí."]
    dialogo.append(pagina)
prueba("el diálogo repetido de una novela tampoco", detectar(dialogo) == {},
       detectar(dialogo))

corto = libro_con_cabeceras(paginas=MIN_PAGINAS - 1)
prueba("un libro de pocas páginas no da evidencia suficiente",
       detectar(corto) == {}, detectar(corto))

# Una línea que se repite pero EN MEDIO de la página es contenido.
enmedio = [cuerpo(p, 6) + ["Vida Espírita"] + cuerpo(p + 100, 6)
           for p in range(20)]
prueba("una línea repetida a media página se queda",
       detectar(enmedio) == {}, detectar(enmedio))

print("\nLa capitular, que es el caso peligroso:")
# «M» + «uchos hombres…» es una capitular: quitarla deja «uchos hombres».
capitular = [["M", "uchos hombres creyeron que la muerte era el final"]
             + cuerpo(p) for p in range(20)]
limpias, _ = limpiar(capitular)
prueba("una letra suelta seguida de minúscula NO se quita",
       limpias[0][0] == "M", limpias[0][:2])
# En Kardec la «M» es un ornamento y detrás va «Dios», con mayúscula.
# En Kardec el patrón real es «Capítulo Primero / M / Dios»: la «M» es un
# ornamento tipográfico y detrás va el título, con mayúscula. El título cambia
# en cada capítulo, así que aquí también.
ornamento = [["M", f"Capítulo {p}"] + cuerpo(p) for p in range(20)]
limpias, _ = limpiar(ornamento)
prueba("pero un ornamento seguido de mayúscula sí",
       limpias[0][0] == "Capítulo 0", limpias[0][:2])

print("\nLos umbrales, que se midieron:")
# cabeceras 95-100% en el borde · personajes 15-33% · umbral 0,85
prueba("el umbral del borde deja margen por los dos lados",
       0.40 < BORDE_MINIMO < 0.95, BORDE_MINIMO)
prueba("la zona del borde son pocas líneas", ZONA <= 5, ZONA)

print("\nNada de esto revienta con lo raro:")
for nombre, entrada in (("sin páginas", []),
                        ("páginas vacías", [[] for _ in range(20)]),
                        ("una sola página", [cuerpo(0)]),
                        ("páginas de una línea", [["x"] for _ in range(20)])):
    try:
        limpiar(entrada)
        prueba(nombre, True)
    except Exception as e:
        prueba(nombre, False, repr(e))

# ── La cabecera de un capítulo corto, medida en Kardec ──────────────────────
#
# «Creación» es el título del capítulo III y hace de cabecera en sus páginas
# impares: cinco veces, no ocho. Con el mínimo de ocho páginas se perdía. Lo
# que la salva es el número de página justo detrás, que ni la portadilla, ni el
# sumario, ni la entrada del índice tienen.
print("\nLa cabecera de un capitulo corto (medido en Kardec):")


def _pagina(cab, numero):
    return [cab, str(numero)] + [f"texto corriente de la pagina {i}"
                                 for i in range(8)]


paginas_kardec = [
    # Índice: «Creación» va dentro de otra línea, no es la línea entera.
    ["Capitulo III - Creacion"] + [f"entrada {i} ........" for i in range(10)],
    # Sumario: suelta, pero en medio de la página y sin número detrás.
    ["Sumario"] + [f"linea {i}" for i in range(5)]
    + ["* Capitulo III", "Creacion", "* Capitulo IV", "Principio vital"],
    # Portadilla del capítulo: detrás va el subtítulo, no un número.
    ["M", "Creacion", "Formacion de los mundos y de los seres vivos"]
    + [f"relleno {i}" for i in range(8)],
]
for _n in (91, 93, 95, 97, 99):
    paginas_kardec.append(_pagina("Creacion", _n))

_hallado = detectar(paginas_kardec)
prueba("capitulo corto: la encuentra con 5 apariciones",
       "Creacion" in _hallado, _hallado)
prueba("la portadilla no se cuela como cabecera",
       "Formacion de los mundos y de los seres vivos" not in _hallado, _hallado)
prueba("la capitular suelta no es cabecera", "M" not in _hallado, _hallado)

# Sin número detrás, cinco apariciones NO bastan: ahí manda la regla de siempre.
_sin_numero = [["Creacion"] + [f"texto {i}" for i in range(9)] for _ in range(5)]
prueba("sin numero detras, cinco apariciones no bastan",
       "Creacion" not in detectar(_sin_numero), detectar(_sin_numero))

# Los números en romanos de las primeras páginas también cuentan.
# Con páginas de relleno hasta el mínimo del documento: por debajo de
# MIN_PAGINAS no se mira nada, y eso se comprueba aparte.
_romanos = ([_pagina("Prologo", r) for r in ("ix", "xi", "xiii", "xv", "xvii")]
            + [[f"pagina suelta {k} linea {i}" for i in range(9)]
               for k in range(3)])
prueba("el numero en romanos tambien vale",
       "Prologo" in detectar(_romanos), detectar(_romanos))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
