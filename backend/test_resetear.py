"""resetear_libros.py — que NO borre nada sin --borrar, y que avise cuando no
hay archivo original (porque entonces el borrado no tiene vuelta atras).

Corre con Python pelado (R2 y Appwrite falsos):
    python test_resetear.py
"""
import io, sys
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}")
    globals().__setitem__('ok' if cond else 'fallos', (ok if cond else fallos) + 1)


def montar(con_original):
    claves = [f"LIBRO/text/part_{i}.txt" for i in range(3)]
    claves += ["LIBRO/audio/part_0.mp3", "LIBRO/cover.png", "LIBRO/index.json"]
    if con_original:
        claves.append("LIBRO/original/libro.pdf")
    almacen = {k: "x" for k in claves}
    huellas = {"borrados": [], "appwrite": []}

    class FakeS3:
        def list_objects_v2(self, Bucket, Prefix, **kw):
            return {"Contents": [{"Key": k} for k in almacen if k.startswith(Prefix)],
                    "IsTruncated": False}
        def delete_objects(self, Bucket, Delete):
            for o in Delete["Objects"]:
                almacen.pop(o["Key"], None)
                huellas["borrados"].append(o["Key"])

    import importlib
    sys.modules.pop("resetear_libros", None)
    R = importlib.import_module("resetear_libros")
    R.cliente_r2 = lambda: FakeS3()
    R.listar_libros = lambda: [{"book_id": "LIBRO", "title": "Libro de prueba"}]
    R.ficha_appwrite = lambda b: {"$id": "DOC1", "added_by": "biblioteca"}
    R.AW_KEY = "clave-falsa"
    def _aw(metodo, ruta, cuerpo=None):
        huellas["appwrite"].append((metodo, ruta))
        return {}
    R._aw = _aw
    return R, almacen, huellas


print("Sin --borrar no toca nada:")
R, almacen, h = montar(con_original=False)
sys.argv = ["x", "--libro", "LIBRO"]
salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
try: R.main()
except SystemExit: pass
sys.stdout = real
texto = salida.getvalue()
c("no borra de R2", not h["borrados"])
c("no toca Appwrite", not h["appwrite"])
c("cuenta los 6 objetos", "6 objetos" in texto)
c("AVISA de que no hay original", "DEFINITIVO" in texto)
c("dice quien es el propietario", "biblioteca" in texto)

print("\nCon archivo original, lo dice:")
R, almacen, h = montar(con_original=True)
sys.argv = ["x", "--libro", "LIBRO"]
salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
try: R.main()
except SystemExit: pass
sys.stdout = real
texto = salida.getvalue()
c("avisa de que se puede reprocesar", "se puede reprocesar" in texto)
c("y no llama a nada DEFINITIVO", "DEFINITIVO" not in texto)

print("\nCon --borrar si borra, y borra las dos cosas:")
R, almacen, h = montar(con_original=True)
sys.argv = ["x", "--libro", "LIBRO", "--borrar"]
salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
try: R.main()
except SystemExit: pass
sys.stdout = real
c("R2 queda vacio", not almacen)
c("borro los 7 objetos", len(h["borrados"]) == 7)
c("borro la ficha de Appwrite",
  h["appwrite"] == [("DELETE", "/documents/DOC1")])

print("\nSin APPWRITE_API_KEY se niega a borrar:")
R, almacen, h = montar(con_original=True)
R.AW_KEY = ""
sys.argv = ["x", "--libro", "LIBRO", "--borrar"]
salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
codigo = None
try: R.main()
except SystemExit as e: codigo = e.code
sys.stdout = real
c("aborta", codigo is not None and codigo != 0)
c("y no ha borrado nada de R2", not h["borrados"])

print("\nLa guarda de la clave de ejemplo:")
R, almacen, h = montar(con_original=True)
for mala in ("", "...", "…", "<TU_CLAVE>", "TU_CLAVE"):
    R.AW_KEY = mala
    try:
        R.comprobar_aw_key()
        c(f"detecta la clave {mala!r}", False, "la dejo pasar")
    except SystemExit as e:
        c(f"detecta la clave {mala!r}", "no tiene una clave de verdad" in str(e))
R.AW_KEY = "standard_bb434ca194434c1144b8419ad413abd9"
try:
    R.comprobar_aw_key()
    c("deja pasar una clave con pinta buena", True)
except SystemExit as e:
    c("deja pasar una clave con pinta buena", False, str(e))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
