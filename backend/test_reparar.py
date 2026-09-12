"""Script de reparacion de libros ya subidos — reparar_libros.py

Corre con Python pelado (usa un R2 falso, no toca la nube):
    python test_reparar.py

Lo que hay que garantizar:
  1. En simulacion NO escribe ni borra nada.
  2. Al aplicar, solo reescribe las partes que de verdad cambiaron.
  3. Invalida el audio y el karaoke SOLO de esas partes — si no, el MP3
     cacheado seguiria leyendo la palabra partida.
  4. No toca la portada ni las partes sanas.
"""
import sys, io
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}")
    if cond: ok += 1
    else:    fallos += 1


def montar():
    almacen = {
        "LIBRO/text/part_0.txt": "El carác- ter del Espíritu y su asisten- cia. El carácter importa.",
        "LIBRO/text/part_1.txt": "La infan- cia y la adolescen- cia son etapas. La infancia pasa rápido.",
        "LIBRO/text/part_2.txt": "Sin ningun corte en esta parte, todo correcto.",
        "LIBRO/audio/part_0_es-MX-JorgeNeural.mp3": b"VIEJO0",
        "LIBRO/audio/part_1_es-MX-JorgeNeural.mp3": b"VIEJO1",
        "LIBRO/audio/part_2_es-MX-JorgeNeural.mp3": b"BUENO2",
        "LIBRO/timing/part_0_es-MX-JorgeNeural_v3.json": b"[]",
        "LIBRO/timing/part_1_es-MX-JorgeNeural_v3.json": b"[]",
        "LIBRO/timing/part_2_es-MX-JorgeNeural_v3.json": b"[]",
        "LIBRO/cover.png": b"PNG",
    }
    huellas = {"escritos": [], "borrados": []}

    class FakeS3:
        def list_objects_v2(self, Bucket, Prefix, **kw):
            return {"Contents": [{"Key": k} for k in almacen if k.startswith(Prefix)],
                    "IsTruncated": False}
        def get_object(self, Bucket, Key):
            v = almacen[Key]
            return {"Body": io.BytesIO(v.encode() if isinstance(v, str) else v)}
        def put_object(self, Bucket, Key, Body, ContentType=None):
            almacen[Key] = Body.decode(); huellas["escritos"].append(Key)
        def delete_object(self, Bucket, Key):
            almacen.pop(Key, None); huellas["borrados"].append(Key)

    import importlib
    sys.modules.pop("reparar_libros", None)
    R = importlib.import_module("reparar_libros")
    R.cliente_r2 = lambda: FakeS3()
    R.listar_libros = lambda: [{"book_id": "LIBRO", "title": "Libro de prueba"}]
    return R, almacen, huellas


print("Simulacion (por defecto):")
R, almacen, h = montar()
sys.argv = ["x", "--sin-ejemplos"]
try: R.main()
except SystemExit: pass
c("no escribe nada", not h["escritos"])
c("no borra nada",   not h["borrados"])
c("el texto roto sigue roto", "carác- ter" in almacen["LIBRO/text/part_0.txt"])

print("\nAplicando de verdad:")
R, almacen, h = montar()
sys.argv = ["x", "--aplicar", "--sin-ejemplos"]
try: R.main()
except SystemExit: pass
c("parte 0 arreglada",               "carácter" in almacen["LIBRO/text/part_0.txt"])
c("parte 0 sin restos",              "carác- ter" not in almacen["LIBRO/text/part_0.txt"])
c("parte 1 arreglada",               "infancia" in almacen["LIBRO/text/part_1.txt"])
c("parte 2 intacta",                 almacen["LIBRO/text/part_2.txt"].startswith("Sin ningun"))
c("solo reescribe 2 partes",         len(h["escritos"]) == 2)

print("\nEl audio y el karaoke viejos quedan invalidados:")
c("audio 0 borrado",    "LIBRO/audio/part_0_es-MX-JorgeNeural.mp3" not in almacen)
c("audio 1 borrado",    "LIBRO/audio/part_1_es-MX-JorgeNeural.mp3" not in almacen)
c("audio 2 CONSERVADO", "LIBRO/audio/part_2_es-MX-JorgeNeural.mp3" in almacen)
c("karaoke 0 borrado",  "LIBRO/timing/part_0_es-MX-JorgeNeural_v3.json" not in almacen)
c("karaoke 1 borrado",  "LIBRO/timing/part_1_es-MX-JorgeNeural_v3.json" not in almacen)
c("karaoke 2 CONSERVADO","LIBRO/timing/part_2_es-MX-JorgeNeural_v3.json" in almacen)
c("portada intacta",    "LIBRO/cover.png" in almacen)
c("borra exactamente 4 archivos", len(h["borrados"]) == 4)

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
