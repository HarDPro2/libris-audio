"""Modo comunidad — Libris Audio.

Corre con Python pelado: `ajustes.py` no importa nada del backend.
    python test_comunidad.py

Libris es la version gratuita de uso personal: lo que sube uno lo ven todos.
El aislamiento por usuario sigue entero detras del interruptor MODO_COMUNIDAD,
porque es lo que necesita la version comercial.
"""
import sys, os, importlib
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  ' + extra if extra else ''}")
    if cond: ok += 1
    else:    fallos += 1

def cargar(valor):
    """Recarga ajustes.py con MODO_COMUNIDAD puesto a `valor`."""
    if valor is None:
        os.environ.pop("MODO_COMUNIDAD", None)
    else:
        os.environ["MODO_COMUNIDAD"] = valor
    sys.modules.pop("ajustes", None)
    return importlib.import_module("ajustes")


print("Por defecto (sin variable) Libris va en comunidad:")
a = cargar(None)
c("MODO_COMUNIDAD activo", a.MODO_COMUNIDAD is True)
c("los libros nuevos entran al catalogo comun", a.VISIBILIDAD_AL_SUBIR == "catalog")

print("\nSe puede apagar para la version comercial:")
for valor in ("0", "false", "no", "off", "FALSE", " Off "):
    a = cargar(valor)
    c(f"MODO_COMUNIDAD={valor!r}", a.MODO_COMUNIDAD is False and a.VISIBILIDAD_AL_SUBIR == "private")

print("\nY se puede volver a encender:")
for valor in ("1", "true", "si", "yes"):
    a = cargar(valor)
    c(f"MODO_COMUNIDAD={valor!r}", a.MODO_COMUNIDAD is True and a.VISIBILIDAD_AL_SUBIR == "catalog")

print("\nQuien ve que — en comunidad:")
a = cargar("1")
c("libro privado de OTRO usuario: visible",  a.visible_para("private", "otro", "yo"))
c("libro privado propio: visible",           a.visible_para("private", "yo", "yo"))
c("libro de catalogo: visible",              a.visible_para("catalog", "otro", "yo"))
c("libro sin campo visibility: visible",     a.visible_para(None, "otro", "yo"))
c("visitante sin sesion: ve todo",           a.visible_para("private", "otro", None))

print("\nQuien ve que — modo aislado (version comercial):")
a = cargar("0")
c("libro privado de OTRO usuario: OCULTO", not a.visible_para("private", "otro", "yo"))
c("libro privado propio: visible",              a.visible_para("private", "yo", "yo"))
c("libro de catalogo: visible",                 a.visible_para("catalog", "otro", "yo"))
c("libro sin campo visibility: visible",        a.visible_para(None, "otro", "yo"))
c("visitante sin sesion NO ve lo privado", not a.visible_para("private", "otro", None))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
