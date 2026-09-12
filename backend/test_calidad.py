"""Motor de calidad — filtros mecanicos + capa de IA.

Corre con Python pelado (la IA va simulada, no llama a nadie):
    python test_calidad.py

Necesita el diccionario hunspell de espanol. Si no esta, el motor se abstiene
y las pruebas lo comprueban.
"""
import sys, asyncio, json, re
sys.path.insert(0, '.')
import calidad, calidad_ia
from calidad import Diccionario, Candidata

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  ' + extra if extra else ''}")
    if cond: ok += 1
    else:    fallos += 1


print("Distancia de una letra:")
for a, b, esperado in [("tiera","tierra",True), ("cemo","como",True),
                       ("dias","dios",True),    ("casa","casa",False),
                       ("gato","perro",False),  ("ano","anno",True),
                       ("abc","abcde",False)]:
    c(f"{a} ~ {b}", calidad.a_una_letra(a,b) is esperado)

dic = Diccionario()
print(f"\nDiccionario: {dic.ruta or 'NO DISPONIBLE'}")
if not dic.disponible:
    print("  (sin diccionario el motor se abstiene; instala hunspell-es)")
    c("se abstiene sin diccionario", calidad.detectar(["texto cualquiera"], dic) == [])
else:
    c("reconoce plurales",      dic.existe("fiestas"))
    c("reconoce conjugaciones", dic.existe("adoraban") and dic.existe("hacía"))
    c("reconoce acentuadas",    dic.existe("qué") and dic.existe("días"))
    c("rechaza basura de OCR",  not dic.existe("carpírulo") and not dic.existe("cémo"))
    c("rechaza 'dias' sin tilde", not dic.existe("dias"))

    print("\nLos tres filtros sobre un libro de juguete:")
    # "carírulo" x9 imita el error sistematico real del libro de Nueva Espana
    libro = ([ "El carírulo primero trata de la tierra y de los reyes. " * 3 +
               "En la tierra vivían los reyes de la tierra. " * 3 ] +
             [ "carírulo " * 6 + "carpírulo del rey. La tiera era grande. " +
               "cómo cómo cómo cómo cómo cémo se hizo. " ])
    cands = calidad.detectar(libro, dic)
    porp = {x.palabra: x for x in cands}
    c("detecta 'carpírulo'", "carpírulo" in porp)
    c("detecta 'tiera'",     "tiera" in porp)
    c("detecta 'cémo'",      "cémo" in porp)
    c("NO toca 'tierra'",    "tierra" not in porp)
    c("NO toca 'reyes'",     "reyes" not in porp)
    if "carpírulo" in porp:
        c("marca 'carpírulo' como SISTEMATICO", porp["carpírulo"].sistematico,
          "(el destino tampoco es espanol)")
    if "tiera" in porp:
        c("'tiera' NO es sistematico", not porp["tiera"].sistematico)
        c("recoge contexto", len(porp["tiera"].contextos) > 0)

    print("\nPalabras cortas: se dejan en paz a proposito")
    c("ignora palabras de menos de 4 letras",
      not any(len(x.palabra) < calidad.LARGO_MIN for x in cands))

    print("\nBarandillas de la capa de IA:")
    cand = Candidata("tiera", 1, "tierra", 13, True, ["La tiera era grande"])
    frec = {"tierra": 13}

    def probar(respuesta):
        return calidad_ia.validar(cand, respuesta, dic, frec)

    d = probar({"correcta":"tierra","destino_correcto":"tierra","confianza":"alta"})
    c("acepta una correccion sensata", d.aceptada)

    d = probar({"correcta":"montaña","destino_correcto":"tierra","confianza":"alta"})
    c("RECHAZA una palabra que no se parece", not d.aceptada, d.motivo)

    d = probar({"correcta":"tierrraa","destino_correcto":"tierra","confianza":"alta"})
    c("RECHAZA lo que no es espanol ni sale en el libro", not d.aceptada, d.motivo)

    d = probar({"correcta":"tiera","destino_correcto":"tierra","confianza":"alta"})
    c("RECHAZA si dice que ya esta bien", not d.aceptada, d.motivo)

    d = probar({"destino_correcto":"tierra","confianza":"alta"})
    c("RECHAZA si no propone nada", not d.aceptada, d.motivo)

    d = probar({"correcta":"tierra","destino_correcto":"tierra","confianza":"inventada"})
    c("una confianza rara se degrada a baja", d.confianza == "baja")

    print("\nNombres propios que no estan en ningun diccionario:")
    cand2 = Candidata("molecuhzoma", 2, "motecuhzoma", 22, False, [])
    d = calidad_ia.validar(cand2, {"correcta":"Motecuhzoma",
                                   "destino_correcto":"Motecuhzoma",
                                   "confianza":"alta"}, dic,
                           {"motecuhzoma": 22})
    c("acepta un nombre propio que el libro usa", d.aceptada, d.motivo)

    print("\nLa IA no devuelve JSON:")
    async def ia_rota(s, u): return "Claro, con gusto te ayudo con eso."
    res = asyncio.run(calidad_ia.revisar([cand], dic, frec, pedir=ia_rota))
    c("se descarta el lote entero, no se inventa nada", res == [])

    async def ia_vacia(s, u): return None
    res = asyncio.run(calidad_ia.revisar([cand], dic, frec, pedir=ia_vacia))
    c("si la IA no responde, tampoco pasa nada", res == [])

    print("\nModo MIXTO — que se aplica solo y que espera revision:")
    decs = [
        calidad_ia.Decision("carpírulo","capítulo","carírulo","capítulo","alta",True),
        calidad_ia.Decision("cémo","cómo","cómo","cómo","alta",True),
        calidad_ia.Decision("clección","elección","elección","elección","baja",True),
        calidad_ia.Decision("xxx","yyy","zzz","zzz","alta",False,"rechazada antes"),
    ]
    textos = ["El carpírulo y el carírulo y cémo y clección aquí."]
    nuevos, inf = calidad_ia.aplicar(textos, decs, solo_alta=True)
    c("aplica la sistematica",            "capítulo" in nuevos[0])
    c("corrige tambien el destino x80",   "carírulo" not in nuevos[0])
    c("aplica la de confianza alta",      "cémo" not in nuevos[0])
    c("DEJA la de confianza baja",        "clección" in nuevos[0])
    c("no aplica lo ya rechazado",        len(inf["aplicadas"]) == 2)
    c("las demas van al informe",         len(inf["pendientes"]) == 2)

    print("\nRespeta la mayuscula inicial:")
    nuevos2, _ = calidad_ia.aplicar(["Carpírulo primero"], decs[:1], solo_alta=True)
    c("Carpírulo -> Capítulo", "Capítulo" in nuevos2[0], nuevos2[0])

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
