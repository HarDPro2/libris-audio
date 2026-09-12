"""subir_biblioteca.py — sin red y sin nube.

Lo que hay que garantizar:
  1. Sin --subir no borra ni sube NADA.
  2. El multipart sale bien formado (si no, el backend recibe basura).
  3. Borra el libro viejo ANTES de subir el nuevo, y en ese orden.
  4. Si la subida falla, queda anotado y el reintento lo repite.
  5. Lo ya hecho no se repite al volver a lanzarlo.
  6. Los documentos que no son libros no se suben nunca.
"""
import io, json, os, sys, tempfile
sys.path.insert(0, '.')

ok = fallos = 0
def c(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}" + (f"  {extra}" if not cond else ""))
    if cond: ok += 1
    else:    fallos += 1


carpeta = tempfile.mkdtemp()
LIBROS = ["Ana_Karenina-Tolstoi_Leon.pdf", "Analectas-Confucio.pdf"]
NO_LIBROS = ["ESTADO DE CUENTA BDV.pdf", "Clase.pdf"]
for n in LIBROS + NO_LIBROS:
    with open(os.path.join(carpeta, n), "wb") as f:
        f.write(b"%PDF-1.4 fake " + n.encode())

FICHAS = [
    {"book_id": "AAA", "title": "Ana Karenina Tolstoi Leon", "category": "Novela"},
    {"book_id": "BBB", "title": "Analectas Confucio", "category": "Filosofia"},
]


def montar():
    huellas = {"borrados": [], "appwrite": [], "subidas": []}

    class FakeS3:
        def list_objects_v2(self, Bucket, Prefix, **kw):
            return {"Contents": [{"Key": f"{Prefix}part_0.txt"}], "IsTruncated": False}
        def delete_objects(self, Bucket, Delete):
            huellas["borrados"] += [o["Key"] for o in Delete["Objects"]]

    import importlib
    for m in ("subir_biblioteca", "resetear_libros"):
        sys.modules.pop(m, None)
    S = importlib.import_module("subir_biblioteca")
    S.cliente_r2 = lambda: FakeS3()
    S.listar_libros = lambda: FICHAS
    S.reset.ficha_appwrite = lambda b: {"$id": f"DOC{b}"}
    S.reset._aw = lambda m, r, cuerpo=None: huellas["appwrite"].append((m, r)) or {}
    S.abrir_sesion = lambda e, p: "SECRETO"
    S.REGISTRO = os.path.join(carpeta, "registro.json")
    def falso_subir(ruta, titulo, categoria, token, espera=900):
        huellas["subidas"].append((os.path.basename(ruta), titulo, categoria, token))
        return {"ok": True, "respuesta": {"book_id": "NUEVO" + titulo[:3]}}
    S.subir_real = S.subir   # la de verdad, para probar el multipart
    S.subir = falso_subir
    os.environ["LIBRIS_EMAIL"] = "yo@ejemplo.com"
    os.environ["LIBRIS_PASSWORD"] = "x"
    return S, huellas


def correr(S, *args):
    sys.argv = ["x", "--carpeta", carpeta] + list(args)
    salida = io.StringIO(); real = sys.stdout; sys.stdout = salida
    try: S.main()
    except SystemExit: pass
    finally: sys.stdout = real
    return salida.getvalue()


print("Sin --subir no toca nada:")
S, h = montar()
texto = correr(S)
c("no borra", not h["borrados"])
c("no sube",  not h["subidas"])
c("no toca Appwrite", not h["appwrite"])
c("lista los 2 libros", texto.count("<-") == 2, texto)
c("deja fuera los documentos personales",
  "ESTADO DE CUENTA BDV.pdf" in texto.split("archivos sin ficha")[1])

print("\nEl multipart esta bien formado:")
SB, h = montar()
cuerpo_visto = {}
class FakeResp:
    def __enter__(self): return io.BytesIO(b'{"book_id":"X"}')
    def __exit__(self, *a): pass
def fake_urlopen(pet, timeout=None):
    cuerpo_visto["datos"] = pet.data
    cuerpo_visto["cabeceras"] = dict(pet.headers)
    return FakeResp()
SB.urllib.request.urlopen = fake_urlopen
res = SB.subir_real(os.path.join(carpeta, LIBROS[0]), "Ana Karenina",
                    "Novela", "TOK")
datos, cab = cuerpo_visto["datos"], cuerpo_visto["cabeceras"]
limite = cab["Content-type"].split("boundary=")[1]
import email
mensaje = email.message_from_bytes(
    f"Content-Type: multipart/form-data; boundary={limite}\r\nMIME-Version: 1.0\r\n\r\n".encode()
    + datos)
campos = {}
for parte in mensaje.get_payload():
    nombre = parte.get_param("name", header="content-disposition")
    campos[nombre] = parte.get_payload(decode=True)
c("se parsea como multipart", mensaje.is_multipart())
c("lleva el titulo",    campos.get("title") == b"Ana Karenina", str(campos.get("title")))
c("lleva la categoria", campos.get("category") == b"Novela")
c("lleva el archivo entero",
  campos.get("file") == open(os.path.join(carpeta, LIBROS[0]), "rb").read())
c("Content-Length cuadra", int(cab["Content-length"]) == len(datos))
c("manda el Bearer", cab["Authorization"] == "Bearer TOK")

print("\nBorra el viejo y sube el nuevo, en ese orden:")
S, h = montar()
texto = correr(S, "--subir")
c("borro los 2 de R2", len(h["borrados"]) == 2, str(h["borrados"]))
c("borro las 2 fichas",
  h["appwrite"] == [("DELETE", "/documents/DOCAAA"), ("DELETE", "/documents/DOCBBB")],
  str(h["appwrite"]))
c("subio los 2", len(h["subidas"]) == 2)
c("conserva titulo y categoria del catalogo",
  h["subidas"][0][1:3] == ("Ana Karenina Tolstoi Leon", "Novela"), str(h["subidas"][0]))
c("usa el secreto de sesion como token", h["subidas"][0][3] == "SECRETO")

print("\nAl volver a lanzarlo no repite lo hecho:")
S2, h2 = montar()
correr(S2, "--subir")
c("no vuelve a subir", not h2["subidas"], str(h2["subidas"]))
c("no vuelve a borrar", not h2["borrados"])

print("\nSi la subida falla, queda anotado y se reintenta:")
os.remove(os.path.join(carpeta, "registro.json"))
S3, h3 = montar()
S3.subir = lambda *a, **k: {"ok": False, "error": "HTTP 500: boom"}
texto = correr(S3, "--subir")
reg = json.load(open(os.path.join(carpeta, "registro.json"), encoding="utf-8"))
c("anota el fallo", all(not v["ok"] for v in reg.values()), str(reg))
c("lo avisa por pantalla", "fallidos: 2" in texto)
S4, h4 = montar()
S4.subir = lambda ruta, *a, **k: h4["subidas"].append(os.path.basename(ruta)) or \
    {"ok": True, "respuesta": {"book_id": "Z"}}
correr(S4, "--subir")
c("el reintento si los sube", len(h4["subidas"]) == 2, str(h4["subidas"]))

print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
