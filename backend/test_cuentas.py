"""cuentas.py — sin tocar Appwrite de verdad."""
import io, sys
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}" + (f"   {extra}" if not cond else ""))
    if cond: ok += 1
    else:    fallos += 1

USUARIOS = [
    {"$id": "U1", "email": "yo@ejemplo.com", "name": "Yo"},
    {"$id": "U2", "email": "otro@ejemplo.com", "name": "Otro"},
]

import importlib
sys.modules.pop("cuentas", None)
C = importlib.import_module("cuentas")
C.reset.AW_KEY = "standard_clave_falsa_de_pruebas"
llamadas = []
def _falso(ruta, cuerpo=None, metodo="GET"):
    llamadas.append((metodo, ruta, cuerpo))
    return {"users": USUARIOS} if ruta == "/users" else {}
C._pedir = _falso

def correr(*args):
    llamadas.clear()
    sys.argv = ["x"] + list(args)
    salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
    try: C.main()
    except SystemExit: pass
    finally: sys.stdout = real
    return salida.getvalue()

print("Listar no cambia nada:")
t = correr("--listar")
c("ensena las dos cuentas", "yo@ejemplo.com" in t and "otro@ejemplo.com" in t)
c("no llama a ningun PATCH", not any(m == "PATCH" for m, _, _ in llamadas))

print("\nPoner clave nueva:")
t = correr("--clave", "yo@ejemplo.com")
patch = [l for l in llamadas if l[0] == "PATCH"]
c("llama al endpoint correcto", patch and patch[0][1] == "/users/U1/password",
  str(patch))
c("manda una clave de 16 caracteres",
  patch and len(patch[0][2]["password"]) == 16, str(patch[0][2] if patch else ""))
c("la imprime una vez", patch and patch[0][2]["password"] in t)
c("avisa de que no queda guardada", "no queda guardada" in t)

print("\nCon una clave elegida por ti:")
t = correr("--clave", "otro@ejemplo.com", "--nueva", "miClaveSegura123")
patch = [l for l in llamadas if l[0] == "PATCH"]
c("usa la que le das", patch and patch[0][2]["password"] == "miClaveSegura123")
c("y la cuenta correcta", patch and patch[0][1] == "/users/U2/password")

print("\nLo que no debe hacer:")
t = correr("--clave", "nadie@ejemplo.com")
c("email inexistente: no toca nada", not any(m == "PATCH" for m, _, _ in llamadas))
t = correr("--clave", "yo@ejemplo.com", "--nueva", "corta")
c("clave de menos de 8: la rechaza",
  not any(m == "PATCH" for m, _, _ in llamadas))

print("\nDos claves generadas seguidas son distintas:")
correr("--clave", "yo@ejemplo.com"); a = [l for l in llamadas if l[0]=="PATCH"][0][2]["password"]
correr("--clave", "yo@ejemplo.com"); b = [l for l in llamadas if l[0]=="PATCH"][0][2]["password"]
c("no se repiten", a != b)

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
