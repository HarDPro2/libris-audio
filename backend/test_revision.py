"""Pruebas del motor de revision al subir. Sin red y sin el backend entero:
solo necesitan guiones.py, calidad.py, calidad_ia.py y el diccionario.
"""
import asyncio
import json
import sys

import calidad
import revision

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        print(f"  OK    {nombre}")
        ok += 1
    else:
        print(f"  FALLO {nombre}  {extra}")
        fallos += 1


# Un libro de juguete con los dos males a la vez: palabras partidas por el
# guion de la maquina de escribir y un error de OCR sistematico.
LIBRO = """CAPITULO PRIMERO

En un lugar de la Mancha vivia un hidalgo muy inge-
nioso que leia libros de caballerias. El hidalgo era
hombre de bien y su casa estaba llena de libros.

CAPITULO SEGUNDO

El hidalgo salio de su casa una manana. Los libros que
habia leido le habian llenado la cabeza de aventuras.
El hidalgo penso que era caballero y que su casa era
un castillo. Su vecino, hombre sencillo, lo siguio.

CAPITULO TERCERO

En la venta habia dos mujeres. El hidaigo las tomo por
damas y a la venta por castillo. El ventero, hombre de
mundo, le siguio la burla. Los libros tenian la culpa.
El hidalgo era ya caballero andante y su casa quedaba
lejos. Su vecino, hombre fiel, cargaba los libros.
El hidalgo volvio molido a su casa, y el ama y la
sobrina lo metieron en la cama sin decir palabra.
"""


def falsa_ia(respuestas):
    """Simula a la IA: devuelve el JSON que le pasemos, sin tocar la red."""
    async def _pedir(sistema, usuario):
        return json.dumps(respuestas, ensure_ascii=False)
    return _pedir


def correr(**kw):
    return asyncio.run(revision.revisar(LIBRO, **kw))


print("Paso 1 — los guiones se unen siempre, aunque no haya IA:")
texto, inf = correr(con_ia=False)
prueba("une 'inge-\\nnioso' en 'ingenioso'", "ingenioso" in texto)
prueba("no queda el guion partido", "inge-" not in texto)
prueba("lo cuenta en el informe", inf["guiones_unidos"] >= 1,
       f"guiones_unidos={inf['guiones_unidos']}")

print("\nPaso 2 — la deteccion encuentra el error sistematico:")
prueba("ve 'hidaigo' como sospechosa", inf["candidatas"]["candidatas"] >= 1,
       json.dumps(inf["candidatas"]))
prueba("dice que la IA no corrio", inf["ia"]["ejecutada"] is False)
prueba("y por que", inf["ia"]["motivo_omitida"] == "desactivada",
       inf["ia"]["motivo_omitida"])

print("\nPaso 3 — con IA simulada, se aplica lo sistematico:")
texto2, inf2 = correr(pedir=falsa_ia([
    {"palabra": "hidaigo", "correcta": "hidalgo",
     "destino_correcto": "hidalgo", "confianza": "alta"},
]))
prueba("corrige 'hidaigo' -> 'hidalgo'", "hidaigo" not in texto2, texto2[:60])
prueba("no toca los 'hidalgo' que ya estaban bien",
       texto2.count("hidalgo") == LIBRO.count("hidalgo") + 1,
       f"{texto2.count('hidalgo')} vs {LIBRO.count('hidalgo')}")
prueba("informa de las ocurrencias", inf2["ia"].get("ocurrencias_sustituidas", 0) >= 1,
       str(inf2["ia"].get("ocurrencias_sustituidas")))
prueba("marca la IA como ejecutada", inf2["ia"]["ejecutada"] is True)

print("\nPaso 4 — el presupuesto de tiempo salta la IA, no la subida:")
texto3, inf3 = correr(presupuesto_s=1.0, pedir=falsa_ia([]))
prueba("no llama a la IA", inf3["ia"]["ejecutada"] is False)
prueba("lo explica", "sin tiempo" in inf3["ia"]["motivo_omitida"],
       inf3["ia"]["motivo_omitida"])
prueba("pero los guiones SI se unieron", "ingenioso" in texto3)

print("\nPaso 5 — si la IA se cae, el texto sale igual, no roto:")
async def _explota(sistema, usuario):
    raise RuntimeError("openrouter caido")
texto4, inf4 = correr(pedir=_explota)
prueba("devuelve texto utilizable", "hidalgo" in texto4)
prueba("no perdio el arreglo de guiones", "ingenioso" in texto4)
prueba("lo deja escrito en el informe",
       not inf4["ia"]["ejecutada"] and inf4["ia"]["motivo_omitida"] != "",
       inf4["ia"]["motivo_omitida"])

print("\nPaso 6 — el informe es JSON puro (se guarda junto al libro):")
try:
    json.dumps(inf2)
    prueba("serializa sin trucos", True)
except Exception as e:
    prueba("serializa sin trucos", False, str(e))
prueba("el resumen de una linea dice algo",
       "guiones unidos" in revision.resumen_humano(inf2),
       revision.resumen_humano(inf2))

print("\nPaso 7 — sin diccionario no se inventa nada:")
class SinDic:
    disponible = False
    def existe(self, w): return True
texto5, inf5 = correr(dic=SinDic())
prueba("se abstiene", inf5["ia"]["motivo_omitida"] == "sin diccionario espanol",
       inf5["ia"]["motivo_omitida"])
prueba("y aun asi une los guiones", "ingenioso" in texto5)

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
