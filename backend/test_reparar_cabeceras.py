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

# ── Un titulo sale una vez; el cuerpo de la pagina, doscientas ──────────────
#
# «El libro de los mediums»: sus dos cabeceras salen 196 y 205 veces, y en ESE
# original el numero de pagina no va en la linea siguiente — va el cuerpo. La
# funcion apuntaba como «titulo legitimo» la primera linea de casi cada pagina
# y luego las indultaba todas: 205 cabeceras encontradas, CERO quitadas.
print("\nUn titulo sale una vez; el cuerpo de la pagina, doscientas:")

_mediums = []
_cuerpos = [
    "28. Los Espiritus pueden hacerse visibles bajo otra apariencia",
    "Observacion. Solo la supersticion puede hacer creer que ciertos",
    "La vision general y permanente de los Espiritus es excepcional",
    "Respuesta del Espiritu sobre la naturaleza de las apariciones",
    "Continuacion del capitulo anterior acerca de las manifestaciones",
    "Nota del traductor sobre la terminologia empleada en esta obra",
]
for _k, _c in enumerate(_cuerpos * 2):          # 12 paginas
    _mediums.append(["ALLAN KARDEC", _c] + [f"resto {i} de la pagina {_k}"
                                            for i in range(8)])

_titulos = rep._titulos_legitimos(_mediums, {"ALLAN KARDEC"})
prueba("una cabecera con 6 continuaciones distintas no legitima ninguna",
       _titulos == set(), sorted(_titulos)[:2])

# Y el caso que esta guarda vino a salvar sigue salvado: «Introduccion» como
# titulo de verdad aporta UNA continuacion.
_intro = [["Introduccion", "al Estudio de la Doctrina Espirita, por Allan Kardec"]
          + [f"cuerpo {i}" for i in range(8)]]
for _n in range(9):
    _intro.append(["Introduccion", str(20 + _n)]
                  + [f"texto corriente {i}" for i in range(8)])
_titulos_intro = rep._titulos_legitimos(_intro, {"Introduccion"})
prueba("un titulo de verdad sigue siendo legitimo",
       "al Estudio de la Doctrina Espirita, por Allan Kardec" in _titulos_intro,
       sorted(_titulos_intro))

# Y entonces la cabecera SI se quita del texto guardado.
_limpio, _cambios = rep.limpiar_parte(
    "ALLAN KARDEC 28. Los Espiritus pueden hacerse visibles bajo otra apariencia",
    ["ALLAN KARDEC"], frozenset(), _titulos)
prueba("con la lista acotada, la cabecera se quita",
       _limpio.startswith("28. Los Espiritus"), _limpio[:40])

# ───────────────────────────────────────────────────────────────────────────
print("\nLAS SECCIONES SE INVALIDAN — el pendiente que llevaba dos dias:")
# Las secciones son posiciones de caracter sobre el texto unido. Al quitar
# cabeceras el texto encoge y todas las de detras se desplazan: el boton de
# «saltar indice» lleva a mitad de un capitulo. Y nada avisa.
import json as _json

_INDICE = {
    "title": "El libro de los espiritus",
    "language": "es",
    "capitulos": [{"titulo": "Prolegomenos", "parte": 3}],
    "secciones": [{"clase": "creditos", "inicio": 0, "fin": 900},
                  {"clase": "indice", "inicio": 240000, "fin": 310000}],
    "partes": {"0": {"clase": "creditos", "sintetizar": False, "saltaA": 2},
               "246": {"clase": "indice", "sintetizar": False, "saltaA": None},
               "247": {"clase": "indice", "sintetizar": False, "saltaA": None}},
}

_limpio, _ns, _np = rep._sin_secciones(_INDICE)
prueba("cuenta las secciones y las partes marcadas", (_ns, _np) == (2, 3),
       (_ns, _np))
prueba("quita las dos claves",
       "secciones" not in _limpio and "partes" not in _limpio,
       sorted(_limpio))
prueba("y NO se lleva el resto del indice",
       _limpio["title"] == "El libro de los espiritus"
       and _limpio["language"] == "es" and len(_limpio["capitulos"]) == 1,
       sorted(_limpio))
prueba("sin tocar el diccionario que le dieron",
       "secciones" in _INDICE and len(_INDICE["partes"]) == 3)

# EL CASO QUE HAY QUE NO ROMPER. Un libro ya revisado y sin secciones tiene
# `secciones: []` escrito a proposito: es lo que hace que marcar_secciones no
# vuelva a bajarlo entero. Borrar ese [] costaria una hora en cada pasada.
_vacio, _ns0, _np0 = rep._sin_secciones({"title": "Una novela",
                                         "secciones": [], "partes": {}})
prueba("un «revisado y no hay nada» se deja en paz",
       _vacio is None and (_ns0, _np0) == (0, 0), (_vacio, _ns0, _np0))
prueba("y un indice que nunca se marco, igual",
       rep._sin_secciones({"title": "x"})[0] is None)
# Al reves si: partes sin secciones tambien son marcas que estorban.
prueba("solo con partes marcadas, tambien invalida",
       rep._sin_secciones({"partes": {"5": {"clase": "indice"}}})[0] == {},
       rep._sin_secciones({"partes": {"5": {}}})[0])

print("\nY escribe solo cuando toca:")


class _R2Falso:
    """Lo minimo para ver QUE se escribe y cuando. Sin red."""

    def __init__(self, indice):
        self.guardado = _json.dumps(indice).encode("utf-8")
        self.escrituras = []

    def get_object(self, Bucket, Key):
        import io
        return {"Body": io.BytesIO(self.guardado)}

    def put_object(self, Bucket, Key, Body, ContentType=None):
        self.escrituras.append((Key, Body, ContentType))


_r2 = _R2Falso(_INDICE)
_marcas = rep._invalidar_secciones(_r2, "LIBRO", ["LIBRO/index.json"], False)
prueba("la simulacion cuenta pero no escribe",
       _marcas == (2, 3) and _r2.escrituras == [], (_marcas, _r2.escrituras))

_r2 = _R2Falso(_INDICE)
_marcas = rep._invalidar_secciones(_r2, "LIBRO", ["LIBRO/index.json"], True)
prueba("con --aplicar escribe una vez", len(_r2.escrituras) == 1,
       _r2.escrituras)
prueba("y la escribe donde va", _r2.escrituras[0][0] == "LIBRO/index.json")
prueba("con el tipo de un json",
       "application/json" in (_r2.escrituras[0][2] or ""),
       _r2.escrituras[0][2])
_tras = _json.loads(_r2.escrituras[0][1].decode("utf-8"))
prueba("lo escrito ya no tiene marcas",
       "secciones" not in _tras and "partes" not in _tras, sorted(_tras))
prueba("pero sigue siendo el indice del libro",
       _tras["title"] == "El libro de los espiritus")

# `marcar_secciones.al_dia` se niega a dar por bueno un indice sin `secciones`,
# y de ahi sale que el libro se vuelva a analizar. Si esto deja de ser verdad,
# la invalidacion no sirve de nada: el libro se queda sin marcas para siempre.
_spec_ms = importlib.util.spec_from_file_location(
    "marcar_secciones", AQUI / "marcar_secciones.py")
_ms = importlib.util.module_from_spec(_spec_ms)
_spec_ms.loader.exec_module(_ms)
_ms.bajar = lambda s3, clave: _json.dumps(_tras).encode("utf-8")
prueba("y marcar_secciones NO lo da por al dia",
       _ms.al_dia(None, "LIBRO", {"LIBRO/index.json": "2026-10-05"}) is False)

_r2_vacio = _R2Falso({"title": "Una novela", "secciones": [], "partes": {}})
prueba("un libro sin marcas no se reescribe",
       rep._invalidar_secciones(_r2_vacio, "L", ["L/index.json"], True)
       == (0, 0) and _r2_vacio.escrituras == [], _r2_vacio.escrituras)
prueba("y sin index.json no pasa nada",
       rep._invalidar_secciones(_R2Falso({}), "L", [], True) == (0, 0))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
