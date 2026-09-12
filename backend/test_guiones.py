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

print("\nReparacion de texto YA guardado (libros subidos antes del arreglo):")
from guiones import reparar_texto_plano, vocabulario_de_textos

# Fragmento REAL de la parte 100 de El libro de los espiritus, tal como esta
# guardado hoy en R2: ya limpio, sin saltos de linea, con los cortes dentro.
kardec = ("¿De dónde procede el cambio que se opera en el carác- ter a cierta edad, "
          "particularmente al salir de la adolescen- cia? La benevoloen- cia que hasta "
          "entonces mostraba cambia notablamen- te a la asisten- cia que se le presta. "
          "En la infan- cia? En ella los pensamien- tos, los caracteres y las "
          "inclinacio- nes. Muchos pensamientos y muchas inclinaciones nacen en la "
          "adolescencia y en la infancia, cuando el carácter aún no existe. La "
          "asistencia de los padres importa.")
vocab_k = vocabulario_de_textos([kardec])
rep, n = reparar_texto_plano(kardec, vocab_k)
c("arregla los 8 cortes del fragmento real", n == 8, f"n={n}")
for esperado in ("carácter", "adolescencia", "notablamente", "asistencia",
                 "infancia", "pensamientos", "inclinaciones"):
    c(f"  {esperado}", esperado in rep)
c("no quedan restos", not re.search(r"[^\W\d_]+-\s+[a-záéíóúüñ]+", rep))

print("\n...y sigue respetando lo que no debe tocar:")
texto = "el metodo teorico- practico y el enfoque teorico-practico son iguales"
v = vocabulario_de_textos([texto])
r, _ = reparar_texto_plano(texto, v)
c("conserva el guion del compuesto", "teorico-practico" in r and "teoricopractico" not in r)

texto2 = ("el cuerpo corporai- para para el alma para todos para siempre "
          "para que se vea para bien")
v2 = vocabulario_de_textos([texto2])
r2, _ = reparar_texto_plano(texto2, v2)
c("no fusiona OCR roto con palabra frecuente", "corporaipara" not in r2)

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
