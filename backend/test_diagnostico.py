"""diagnostico_texto.py — que CORRA, no solo que compile.

Un NameError no lo ve py_compile: la primera version de esta prueba no existia
y por eso el script llego roto a produccion. Aqui se ejecuta entero contra un
R2 falso, con un texto que tiene las tres plagas a la vez.
"""
import io, sys
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}" + (f"   {extra}" if not cond else ""))
    if cond: ok += 1
    else:    fallos += 1

# Parrafo con: guion de corte, basura de encabezado repetida, y una palabra
# pegada de verdad.
PARTES = {
    "LIBRO/text/part_0.txt":
        "La denomi- nación de los niños. RVC Esto es un texto de prueba con "
        "palabras normales y frases enteras que se repiten. RVC otra vez.",
    "LIBRO/text/part_1.txt":
        "El hombre-lobo y la casa. RVC aparece de nuevo aqui. LS—CVII tambien. "
        "Dios no les ha dadoeste aspecto, dijo. Los niños son seres.",
    # Aqui salen "dado" y "este" sueltas: sin eso, la regla nueva no propone
    # separar "dadoeste", y hace bien — exige que las dos mitades se usen en
    # el libro.
    "LIBRO/text/part_2.txt":
        "Texto limpio sin nada raro. RVC. Las frases enteras y los niños "
        "normales. LS—CVII final. Dios ha dado este nombre, y este otro. "
        "Lo ha dado sin pedir nada.",
}

class FakeS3:
    def list_objects_v2(self, Bucket, Prefix, **kw):
        return {"Contents": [{"Key": k} for k in PARTES if k.startswith(Prefix)],
                "IsTruncated": False}
    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(PARTES[Key].encode())}

import importlib
sys.modules.pop("diagnostico_texto", None)
D = importlib.import_module("diagnostico_texto")
D.cliente_r2 = lambda: FakeS3()
D.listar_libros = lambda: [{"book_id": "LIBRO", "title": "Libro de prueba"}]
D.MIN_APARICIONES_BASURA = 2      # el texto de prueba es corto

def correr(*args):
    sys.argv = ["x", "--libro", "LIBRO"] + list(args)
    salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
    try: D.main()
    except SystemExit: pass
    finally: sys.stdout = real
    return salida.getvalue()

print("El libro entero:")
t = correr()
c("corre sin reventar", "caracteres en total" in t)
c("cuenta las formas de guion", "guion + espacio" in t)
c("ve el guion de corte", "denomi- nación" in t)
c("llega al bloque de BASURA", "BASURA REPETIDA" in t, t[-400:])
c("senala RVC como basura", "«RVC»" in t)
c("senala LS—CVII como basura", "LS" in t.split("BASURA REPETIDA")[1])
c("llega al bloque de PEGADAS", "PALABRAS PEGADAS" in t)
c("propone el arreglo de 'dadoeste'", "dado este" in t, t.split("PEGADAS")[1][:300])
c("NO marca palabras normales", "«niños»" not in t and "«frases»" not in t)

print("\nUna parte concreta:")
t = correr("--parte", "0", "--ver")
c("imprime la parte", "denomi- nación" in t)
c("y su recuento", "recuento en ESTA parte" in t)

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
