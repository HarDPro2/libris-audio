"""basura.py — con las frases REALES de "El libro de los espiritus" (Kardec).

Los 36 tokens y las 674 apariciones salieron del diagnostico del 12-09-2026.
Lo que hay que garantizar:
  1. Los encabezados incrustados a mitad de frase se van.
  2. Los numeros de capitulo y los nombres en mayusculas se quedan.
"""
import sys
from collections import Counter

import basura

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}" + (f"   {extra}" if not cond else ""))
    if cond: ok += 1
    else:    fallos += 1

# Los tokens tal como los conto el diagnostico.
BASURA = {"LS", "LT", "CII", "CI", "LC", "CVI", "CIX", "CVIII", "CIV", "LP",
          "IEMC", "CVII", "PGF", "CX", "CIII", "CV", "CXI", "RVC", "II", "LL"}

print("Frases reales del libro:")
CASOS = [
    ("nadie se inquietaria por lo que RVC necesita, cuando aun no sabe hablar",
     "nadie se inquietaria por lo que necesita, cuando aun no sabe hablar"),
    ("y afables, les LS—CVII profesan todo su afecto",
     "y afables, les profesan todo su afecto"),
    ("para perfeccionarse, RVC para mejorarse",
     "para perfeccionarse, para mejorarse"),
    ("los rodean de los LT mas exquisitos cuidados",
     "los rodean de los mas exquisitos cuidados"),
]
for antes, esperado in CASOS:
    salida, n = basura.limpiar(antes, BASURA)
    c(f"limpia «{antes[:38]}...»", salida == esperado and n == 1,
      f"obtuvo «{salida}»")

print("\nLo que NO se debe tocar:")
INTACTOS = [
    "CAPITULO II. De las leyes divinas",
    "El Libro II de la obra trata de esto",
    "Vease el capitulo CVII, donde se explica",   # tras coma pero con mayuscula antes
    "LS es la abreviatura que usa el autor",      # al principio de la frase
    "La doctrina espirita. II. Las penas futuras",
]
for texto in INTACTOS:
    salida, n = basura.limpiar(texto, BASURA)
    c(f"conserva «{texto[:40]}...»", n == 0 and salida == texto,
      f"quito {n}: «{salida}»")

print("\nEl par CODIGO—ROMANO se va con punto delante o sin el:")
PARES = [
    ("del pasado. LS—CVII Los que se creen superiores",
     "del pasado. Los que se creen superiores"),
    ("«Asi sea». LT—CVIII Los Espiritus lo dicen",
     "«Asi sea». Los Espiritus lo dicen"),
    ("y afables, les LS—CVII profesan todo su afecto",
     "y afables, les profesan todo su afecto"),
    # Este estaba antes en la lista de intactos, cuando la regla era solo de
    # contexto. Ahora se quita a proposito: es un encabezado igual.
    ("Dios ha establecido las leyes. LS—CVII",
     "Dios ha establecido las leyes."),
]
for antes, esperado in PARES:
    salida, n = basura.limpiar(antes, BASURA)
    c(f"quita «{antes[:34]}...»", salida == esperado and n == 1,
      f"obtuvo «{salida}» ({n})")

# Y con pares_siempre=False vuelve a la regla estricta de contexto.
salida, n = basura.limpiar(PARES[0][0], BASURA, pares_siempre=False)
c("con pares_siempre=False respeta el contexto", n == 0, f"quito {n}")

try:
    from calidad import Diccionario as _D
    _dic = _D()
    ev = (lambda w: _dic.existe(w) or _dic.existe(w.lower())) if _dic.disponible else None
except Exception:
    ev = None

print("\nLo que la regla del par se llevaba por delante (12-09-2026):")
# Estos salieron de la simulacion real sobre Kardec. La version anterior
# aceptaba cualquier pareja de tokens sospechosos, con guion O CON ESPACIO.
DESASTRES = [
    ("COMPILADOS Y PUESTOS EN ORDEN POR ALLAN KARDEC Traducción de José",
     "el nombre del autor en la portada"),
    ("en el fondo». CAPÍTULO III II. LEY DEL TRABAJO",
     "el numero de capitulo"),
    ("para todos. CAPÍTULO IV III. LEY DE REPRODUCCIÓN",
     "otro numero de capitulo"),
    ("MORALES  CI L  CII I.L  CIII II.L  CIV III.L",
     "el indice de materias"),
]
BASURA_KARDEC = {"LS", "LT", "CII", "CI", "CVI", "CVII", "CVIII", "LC",
                 "IEMC", "PGF", "RVC", "II", "III", "IV", "IX"}
for texto, que in DESASTRES:
    salida, n = basura.limpiar(texto, BASURA_KARDEC)
    c(f"conserva {que}", n == 0 and salida == texto, f"quito {n}: «{salida}»")

print("\nY el par de verdad sigue yendose:")
for texto, esperado in [
    ("os de cuándo y cómo nos creó. LS—CI Puedes decir que no tenemos",
     "os de cuándo y cómo nos creó. Puedes decir que no tenemos"),
    ("nadie se inquietaría por lo que RVC necesita",
     "nadie se inquietaría por lo que necesita"),
]:
    salida, n = basura.limpiar(texto, BASURA_KARDEC)
    c(f"quita «{texto[:34]}...»", salida == esperado and n == 1,
      f"obtuvo «{salida}» ({n})")

print("\nSiglas largas: los nombres propios no son codigos de encabezado:")
from collections import Counter as _C
_frec = _C({"LS": 74, "ALLAN": 7, "KARDEC": 9, "IEMC": 13, "CVIII": 10})
if ev is not None:
    _tok = basura.detectar_basura(_frec, ev)
    c("detecta las siglas cortas", {"LS", "IEMC"} <= _tok, str(_tok))
    c("detecta los romanos largos", "CVIII" in _tok, str(_tok))
    c("NO detecta ALLAN ni KARDEC", not ({"ALLAN", "KARDEC"} & _tok), str(_tok))

print("\nDeteccion automatica de los tokens:")
# Un texto donde LS sale 6 veces y las palabras normales muchas mas.
textos = ["el hombre LS y la casa " * 6 + "palabras normales de verdad " * 20]
frec = basura.frecuencias(textos)
if ev is None:
    print("  (sin diccionario, me salto esta parte)")
else:
    detectada = basura.detectar_basura(frec, ev)
    c("detecta LS", "LS" in detectada, str(detectada))
    c("no detecta palabras normales",
      not (detectada & {"hombre", "casa", "palabras", "normales", "verdad"}),
      str(detectada))

print("\nDos tokens seguidos y el rastro que dejan:")
salida, n = basura.limpiar("les LS CVII profesan y luego RVC vino", BASURA)
c("quita los dos", n == 2 or salida == "les profesan y luego vino",
  f"quito {n}: «{salida}»")
c("no deja dobles espacios", "  " not in salida, repr(salida))

print("\nRegistro de lo que quita:")
reg = []
basura.limpiar(CASOS[0][0], BASURA, reg)
c("anota el token y su contexto", reg and reg[0][0] == "RVC" and "necesita" in reg[0][1],
  str(reg))

print("\nUn romano es basura solo si sale en CADA pagina:")
from collections import Counter as _CC
if ev is not None:
    # "Los Mediums": romanos de referencia, pocas veces cada uno
    _med = basura.detectar_basura(_CC({"II": 8, "VIII": 7, "III": 7,
                                       "IV": 7, "VII": 5, "XII": 5}), ev)
    c("en Los Mediums no marca ninguno", not _med, str(_med))
    # "Espiritus": numeros de pagina, decenas de veces
    _esp = basura.detectar_basura(_CC({"CI": 26, "CII": 29, "CVI": 24,
                                       "LS": 74, "LT": 45}), ev)
    c("en Espiritus los marca todos", {"CI", "CII", "CVI", "LS", "LT"} <= _esp,
      str(_esp))

_ref = "llamamos la atencion de nuestros lectores sobre el parrafo XII de la introduccion"
_sal, _n = basura.limpiar(_ref, {"XII"})
c("respeta «el parrafo XII de la introduccion»", _n == 0, f"quito {_n}: {_sal}")

print("\nCabeceras repetidas — el caso de «El libro de Los Mediums»:")
# Ahi la cabecera es el nombre del autor: ALLAN KARDEC sale 206 veces y
# MEDIUMS 209. Token a token no se distinguen de la portada; la secuencia si.
LIBRO = ""
for _ in range(12):
    LIBRO += ("el medium debe estar tranquilo y sereno para recibir. "
              "ALLAN KARDEC En este caso la comunicacion es directa. "
              "EL LIBRO DE LOS MEDIUMS Los espiritus se manifiestan de mil "
              "maneras y el observador atento las distingue. ")
LIBRO += "OBRA COMPILADA POR ALLAN KARDEC Traduccion de Jose Maria."

cabeceras = basura.detectar_cabeceras([LIBRO])
c("detecta «ALLAN KARDEC»", "ALLAN KARDEC" in cabeceras, str(cabeceras))
c("detecta «EL LIBRO DE LOS MEDIUMS»",
  "EL LIBRO DE LOS MEDIUMS" in cabeceras, str(cabeceras))

salida, n = basura.limpiar_cabeceras(LIBRO, cabeceras)
c("quita las 24 de dentro del texto", n == 24, f"quito {n}")
c("y NO la de la portada",
  "COMPILADA POR ALLAN KARDEC Traduccion" in salida)
c("no deja dobles espacios", "  " not in salida)

# Una frase normal en mayusculas que NO se repite no es cabecera.
suelta = "Y entonces dijo: NO HAY MAS REMEDIO que aceptarlo."
c("una racha que sale una vez no es cabecera",
  "NO HAY MAS REMEDIO" not in basura.detectar_cabeceras([suelta]),
  str(basura.detectar_cabeceras([suelta])))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
