"""Palabras cortadas por guion al final de linea.

Corre con Python pelado: `guiones.py` no importa nada del backend.
    python test_guiones.py

Casos reales tomados de "El libro de los espiritus" (Allan Kardec), parte 100
de 231, que es el libro donde se detecto el problema.
"""
import sys, re
sys.path.insert(0, '.')
from guiones import vocabulario, unir_palabras_cortadas, decidir_union

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  ' + extra if extra else ''}")
    if cond: ok += 1
    else:    fallos += 1

def procesar(texto):
    vocab = vocabulario([texto])
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    return re.sub(r"  +", " ", " ".join(unir_palabras_cortadas(lineas, vocab))).strip()


print("Casos REALES de El libro de los espiritus (Kardec), parte 100:")
for izq, der, esperado in [
    ("carác",      "ter",   "carácter"),
    ("adolescen",  "cia",   "adolescencia"),
    ("infan",      "cia",   "infancia"),
    ("pensamien",  "tos",   "pensamientos"),
    ("inclinacio", "nes",   "inclinaciones"),
    ("asisten",    "cia",   "asistencia"),
    ("notablamen", "te",    "notablamente"),
    ("tempran",    "a",     "temprana"),
]:
    r = procesar(f"del {izq}-\n{der} a cierta edad")
    c(f"{izq}- {der}", esperado in r, "-> " + esperado)

print("\nSe unen las palabras partidas:")
for entrada, esperado in [
    ("El inge-\nnioso hidalgo",        "ingenioso"),
    ("don Qui-\njote de la Man-\ncha", "Quijote"),
    ("don Qui-\njote de la Man-\ncha", "Mancha"),
    ("era re-\nverenciada por todos",  "reverenciada"),
    ("el dios Tezcatli-\npoca reinaba","Tezcatlipoca"),
    ("Lla-\nmaban a eso",              "Llamaban"),
]:
    c(repr(entrada[:26]), esperado in procesar(entrada), "-> " + esperado)

print("\nNO se toca lo que no es un corte de palabra:")
for desc, entrada, no_debe in [
    ("raya de dialogo",        "—Hola —dijo—\nvenia de lejos",       "—Hola venia"),
    ("guion entre espacios",   "el articulo 5 - pagina 3\nsigue",    "5-pagina"),
    ("continuacion en mayus.", "el tratado franco-\nAleman de 1870", "francoAleman"),
    ("numero tras el guion",   "el capitulo-\n5 empieza",            "capitulo5"),
    ("linea normal",           "una linea cualquiera\ny otra mas",   "cualquieray"),
]:
    c(desc, no_debe not in procesar(entrada))

print("\nSalvaguarda: OCR roto + continuacion que es palabra frecuente")
# Caso real: "corporai- para para". "para" sale mucho en el libro y
# "corporaipara" no existe -> no se une.
libro = ("el cuerpo corporai-\npara para el alma\n"
         "esto es para todos\ny para siempre\npara que se vea")
r = procesar(libro)
c("no fusiona corporai + para", "corporaipara" not in r)
c("deja el texto legible",      "corporai- para" in r or "corporai-\npara" in r)

print("\n...pero las silabas cortas SI se unen aunque sean palabras:")
# "de" es la palabra mas frecuente del espanol y aun asi "gran-de" se une,
# porque la salvaguarda solo mira continuaciones de 4 letras o mas.
libro2 = ("un gran-\nde senor\nde la casa de al lado de todos de nuevo")
c("gran- de -> grande", "grande" in procesar(libro2))

print("\nCompuestos con guion de verdad: se unen las lineas, se conserva el guion")
texto = ("un estudio teorico-\npractico riguroso\n"
         "el metodo teorico-practico ya es conocido")
r = procesar(texto)
c("conserva el guion del compuesto", "teorico-practico" in r)
c("no lo pega sin guion",            "teoricopractico" not in r)
c("no deja el espacio intruso",      "teorico- practico" not in r)

print("\nEl vocabulario del documento decide:")
r_sin = procesar("la bibli-\noteca estaba")
c("sin testigo, une por defecto", "biblioteca" in r_sin and "bibli- oteca" not in r_sin)
c("con testigo, une igual",
  "biblioteca" in procesar("la bibli-\noteca estaba\nvisito la biblioteca ayer"))

print("\nGuion blando (U+00AD) tambien cuenta como corte:")
c("guion blando", "ingenioso" in procesar("El inge­\nnioso hidalgo"))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
