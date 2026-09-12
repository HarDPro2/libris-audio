"""comparar.py — que CORRA y que distinga un arreglo de un destrozo.

Con un R2 falso: una parte con los tres tipos de cambio (union de guion,
basura quitada, y un destrozo inventado) y una parte que no cambio.
"""
import io, sys
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}" + (f"   {extra}" if not cond else ""))
    if cond: ok += 1
    else:    fallos += 1

ALMACEN = {
    # respaldo (antes)
    "LIBRO/text_original/part_0.txt":
        "El hombre inge- nioso de la Mancha LS—CVII vivia en un lugar tranquilo "
        "y sereno donde nadie le molestaba jamas de los jamases.",
    # actual (despues): guion unido + basura quitada
    "LIBRO/text/part_0.txt":
        "El hombre ingenioso de la Mancha vivia en un lugar tranquilo "
        "y sereno donde nadie le molestaba jamas de los jamases.",
    # una parte donde algo se destrozo: una palabra cambio por otra distinta
    "LIBRO/text_original/part_1.txt":
        "Las mujercitas jugaban en el patio de la casa grande y vieja.",
    "LIBRO/text/part_1.txt":
        "Las mujer citas jugaban en el patio de la casa grande y vieja.",
}

class FakeS3:
    def list_objects_v2(self, Bucket, Prefix, **kw):
        return {"Contents": [{"Key": k} for k in ALMACEN if k.startswith(Prefix)],
                "IsTruncated": False}
    def get_object(self, Bucket, Key):
        if Key not in ALMACEN:
            raise KeyError(Key)
        return {"Body": io.BytesIO(ALMACEN[Key].encode())}

import importlib
sys.modules.pop("comparar", None)
C = importlib.import_module("comparar")
C.cliente_r2 = lambda: FakeS3()
C.listar_libros = lambda: [{"book_id": "LIBRO", "title": "Libro de prueba"}]

def correr(*args):
    sys.argv = ["x", "--libro", "LIBRO"] + list(args)
    salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
    try: C.main()
    except SystemExit: pass
    finally: sys.stdout = real
    return salida.getvalue()

print("Distingue los tres casos:")
t = correr()
c("corre sin reventar", "cambios en total" in t)
c("ve la union del guion", "ingenioso" in t)
c("ve la basura quitada", "LS—CVII" in t)
c("marca el destrozo como sospechoso", "PARA MIRAR A OJO" in t and "mujer citas" in t)
c("cuenta que el texto crecio", "el texto crecio  : 1" in t, t[:300])

print("\nLa clasificacion por dentro:")
c("union de guion NO es sospechosa", not C.sospechoso("inge- nioso", "ingenioso"))
c("borrar basura NO es sospechoso",  not C.sospechoso("Mancha LS—CVII vivia", "Mancha vivia"))
c("partir una palabra SI lo es",     C.sospechoso("mujercitas", "mujer citas"))
c("cambiar una palabra por otra SI", C.sospechoso("carácter", "cordón"))

print("\nLos dos arreglos a la vez (casos reales de Los Mediums):")
JUNTOS = [
    ("prác- EL LIBRO DE LOS MÉDIUMS ticas.", "prácticas."),
    ("vivi- ALLAN KARDEC mos,", "vivimos,"),
    ("sobre- ALLAN KARDEC natural,", "sobrenatural,"),
    ("inex- EL LIBRO DE LOS MÉDIUMS plicables,", "inexplicables,"),
    ("oposito- EL LIBRO DE LOS MÉDIUMS res,", "opositores,"),
]
for antes, ahora in JUNTOS:
    c(f"no marca «{antes[:30]}...»", not C.sospechoso(antes, ahora),
      f"lo marco sospechoso")

print("\nY sigue marcando lo que si es raro:")
c("partir una palabra",        C.sospechoso("mujercitas", "mujer citas"))
c("cambiar una palabra",       C.sospechoso("carácter", "cordón"))
c("borrar media frase",
  C.sospechoso("el hombre bueno y justo", "el hombre malo"))

print("\nUna parte concreta:")
t = correr("--parte", "0")
c("solo mira esa parte", "1 partes con respaldo" in t)

print("\nUn libro sin respaldo no se puede comparar:")
sys.argv = ["x", "--libro", "OTRO"]
salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
codigo = None
try: C.main()
except SystemExit as e: codigo = e.code
finally: sys.stdout = real
c("lo dice y no revienta", isinstance(codigo, str) and "respaldo" in codigo, str(codigo))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
