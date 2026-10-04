"""El pulso de telemetria: que no estorbe y que no mienta."""
import asyncio, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nexus

ok = fallos = 0
def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond: ok += 1; print(f"  OK    {nombre}")
    else:    fallos += 1; print(f"  FALLO {nombre}   {extra}")

print("Sin claves, silencio absoluto:")
nexus.NEXUS_URL, nexus.CLAVE = "", ""
prueba("activo() es False", nexus.activo() is False)
asyncio.run(nexus.pulso("u", "p", "m", "o"))
prueba("pulso() no lanza", True)
nexus.soltar("u", "p", "m", "o")
prueba("soltar() fuera de un bucle no lanza", True)

print("\nCon claves pero el servidor caido, tampoco pasa nada:")
nexus.NEXUS_URL, nexus.CLAVE = "https://127.0.0.1:1", "clave"
prueba("activo() es True", nexus.activo() is True)
try:
    asyncio.run(nexus.pulso("u", "p", "m", "o"))
    prueba("servidor inalcanzable: se traga el error", True)
except Exception as e:
    prueba("servidor inalcanzable: se traga el error", False, repr(e))

print("\nEl cronometro mide de verdad:")
import time
with nexus.Cronometro() as c:
    time.sleep(0.05)
prueba("mide al menos 40 ms", c.ms >= 40, c.ms)
prueba("y no se dispara", c.ms < 2000, c.ms)

print("\nY una excepcion dentro del cronometro no se traga:")
try:
    with nexus.Cronometro() as c2:
        raise ValueError("a proposito")
    prueba("la excepcion sale", False)
except ValueError:
    prueba("la excepcion sale", True)
    prueba("y aun asi midio", c2.ms >= 0, c2.ms)

print("\nEl primer fallo se cuenta; los demas se callan:")
import io, contextlib
nexus._ya_me_queje = False
nexus.NEXUS_URL, nexus.CLAVE = "https://127.0.0.1:1", "clave"
salida = io.StringIO()
with contextlib.redirect_stdout(salida):
    asyncio.run(nexus.pulso("u", "p", "m", "o"))
primero = salida.getvalue()
prueba("el primer fallo avisa", "[Nexus]" in primero, repr(primero[:60]))
salida2 = io.StringIO()
with contextlib.redirect_stdout(salida2):
    asyncio.run(nexus.pulso("u", "p", "m", "o"))
    asyncio.run(nexus.pulso("u", "p", "m", "o"))
prueba("los siguientes se callan", salida2.getvalue() == "", repr(salida2.getvalue()[:60]))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
