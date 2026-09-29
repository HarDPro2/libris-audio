"""La reparación de cabeceras en el texto ya guardado.

ESTE ES EL SCRIPT QUE MÁS PUEDE ROMPER: escribe sobre las partes de un libro
que ya está en producción. Las pruebas de aquí abajo son todas casos que
FALLARON de verdad mientras se escribía, no casos imaginados.
"""
import importlib.util
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
_spec = importlib.util.spec_from_file_location(
    "reparar_cabeceras", AQUI / "reparar_cabeceras.py")
rep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rep)

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


CABS = sorted(["Libro Segundo – Capítulo VI", "Vida Espírita",
               "Introducción", "Conclusión", "M"], key=len, reverse=True)


def limpia(texto, leg=frozenset(), tit=frozenset()):
    return rep.limpiar_parte(texto, CABS, leg, tit)[0]


print("La cabecera cosida al principio del párrafo — el caso real:")
# Las tres líneas de la parte 100 de Kardec, tal como las devolvió R2.
prueba("se quita y el texto sigue",
       limpia("Libro Segundo – Capítulo VI que un día habrán de reunirse")
       == "que un día habrán de reunirse")
prueba("también cuando detrás vienen comillas",
       limpia("Vida Espírita “De seguro lo ve y lo comprende mucho mejor")
       == "“De seguro lo ve y lo comprende mucho mejor")
prueba("y el ornamento suelto",
       limpia("M Dios y lo infinito, que es el título del capítulo")
       == "Dios y lo infinito, que es el título del capítulo")

print("\nEL LÍMITE DE PALABRA — casi destroza el libro:")
# «M» sale 34 veces y es cabecera. Sin exigir que ahí acabe la palabra, se
# llevaba la primera letra de CUALQUIER línea que empezara por M. En la
# simulación no se veía: los ejemplos salen por orden de parte.
for nombre, texto in (
        ("«Muchos hombres…» conserva su M",
         "Muchos hombres creyeron que la muerte era el final de todo"),
        ("un nombre propio también",
         "María de los Ángeles llegó tarde aquella noche de invierno"),
        ("y una inicial con punto",
         "M. Victor Duruy escribió una historia de Grecia bastante parcial"),
        ("«Conclusión» no se come «Conclusiones»",
         "Conclusiónes del autor sobre la doctrina que acaba de exponer"),
):
    prueba(nombre, limpia(texto) == texto, limpia(texto)[:48])

print("\nEL TÍTULO QUE NO ES CABECERA — dos formas, las dos protegidas:")
# «Introducción» sale 46 veces como cabecera, pero también abre el título del
# libro. En el original, la cabecera lleva SIEMPRE el número de página detrás;
# el título no. Esa es la diferencia, y no la forma de la frase.
TITULO = "Introducción al Estudio de la Doctrina Espírita I Para las cosas"
una = [["Introducción", "20", "cuerpo de la página veinte"],
       ["Introducción al Estudio de la Doctrina Espírita", "I Para las cosas"]]
dos = [["Introducción", "20", "cuerpo de la página veinte"],
       ["Introducción", "al Estudio de la Doctrina Espírita", "I Para"]]
for nombre, paginas in (("el título en UNA línea del original", una),
                        ("el título en DOS líneas del original", dos)):
    leg = rep._lineas_que_siguen(paginas, {"Introducción"})
    tit = rep._titulos_legitimos(paginas, {"Introducción"})
    prueba(nombre, limpia(TITULO, leg, tit) == TITULO,
           limpia(TITULO, leg, tit)[:48])

leg = rep._lineas_que_siguen(una, {"Introducción"})
tit = rep._titulos_legitimos(una, {"Introducción"})
prueba("y aun así la cabecera de verdad sí se quita",
       limpia("Introducción lista, una de cuyas fases presenta. Por esta",
              leg, tit).startswith("lista"))

print("\nLa señal del número de página, medida sobre el original:")
paginas = [["Introducción", "20", "cuerpo"], ["Introducción", "21", "cuerpo"],
           ["Introducción", "al Estudio de la Doctrina Espírita", "I Para"]]
tit = rep._titulos_legitimos(paginas, {"Introducción"})
prueba("lo que lleva número detrás NO cuenta como título",
       "20" not in tit and "21" not in tit, tit)
prueba("lo que no lleva número, sí",
       "al Estudio de la Doctrina Espírita" in tit, tit)

print("\nLo que se deja en paz:")
prueba("la línea que es SOLO el título", limpia("Introducción") == "Introducción")
prueba("un resto demasiado corto no cuenta",
       limpia("Introducción y ya") == "Introducción y ya")
prueba("prosa normal",
       limpia("La identidad necesaria para que se establezca una simpatía")
       == "La identidad necesaria para que se establezca una simpatía")

print("\nNada de esto revienta con lo raro:")
for nombre, texto in (("texto vacío", ""), ("solo saltos", "\n\n\n"),
                      ("una línea en blanco", "   "),
                      ("sin cabeceras", "cualquier cosa")):
    try:
        rep.limpiar_parte(texto, CABS)
        prueba(nombre, True)
    except Exception as e:
        prueba(nombre, False, repr(e))
prueba("sin cabeceras no cambia nada",
       rep.limpiar_parte("Muchos hombres", [])[0] == "Muchos hombres")

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
