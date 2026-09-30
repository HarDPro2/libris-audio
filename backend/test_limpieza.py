"""La limpieza de huérfanos: el endpoint que puede borrar la biblioteca.

/api/clean-orphans borra prefijos enteros de R2. El fallo que hay que hacer
imposible no es un error de código: es que la lista de libros vivos llegue
INCOMPLETA. Si Appwrite falla o devuelve media lista, los libros que no
aparecen parecen huérfanos, y se borra el catálogo entero sin un solo error en
los registros.

Casi todas las pruebas de aquí abajo son de eso: de que en la duda NO borra.
"""
import asyncio
import importlib.util
import os
import pathlib
import sys
import types

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.modules.setdefault("fitz", types.ModuleType("fitz"))

_spec = importlib.util.spec_from_file_location("main_limpieza", AQUI / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)

from fastapi.testclient import TestClient

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre}   {extra}")


# ---------------------------------------------------------------------------
# Dobles: un bucket y una base de datos de mentira
# ---------------------------------------------------------------------------

class BucketFalso:
    """Lo mínimo de boto3 que usa el endpoint."""

    def __init__(self, contenido):
        # {prefijo: [(clave, bytes), ...]}
        self.contenido = {p: list(v) for p, v in contenido.items()}
        self.borrados = []

    def get_paginator(self, _nombre):
        bucket = self

        class Paginador:
            def paginate(self, Bucket=None, Prefix=None, Delimiter=None):
                if Delimiter == "/":
                    yield {"CommonPrefixes":
                           [{"Prefix": f"{p}/"} for p in bucket.contenido]}
                    return
                pref = (Prefix or "").rstrip("/")
                objetos = [{"Key": k, "Size": s}
                           for k, s in bucket.contenido.get(pref, [])]
                yield {"Contents": objetos}

        return Paginador()

    def delete_objects(self, Bucket=None, Delete=None):
        self.borrados.extend(o["Key"] for o in Delete["Objects"])
        return {}


class RespuestaFalsa:
    def __init__(self, datos, error=None):
        self.datos, self.error = datos, error

    def raise_for_status(self):
        if self.error:
            raise RuntimeError(self.error)

    def json(self):
        return self.datos


class ClienteFalso:
    """Sustituye httpx.AsyncClient dentro de _libros_vivos."""

    def __init__(self, paginas, total, error=None, **_):
        self.paginas, self.total, self.error = paginas, total, error
        self.llamadas = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, _url, params=None, headers=None):
        if self.error:
            return RespuestaFalsa(None, self.error)
        i = self.llamadas
        self.llamadas += 1
        docs = self.paginas[i] if i < len(self.paginas) else []
        return RespuestaFalsa({"documents": docs, "total": self.total})


def montar(prefijos, paginas, total, error=None, token="secreto-de-prueba"):
    """Deja el módulo listo y devuelve (cliente HTTP de prueba, bucket)."""
    bucket = BucketFalso(prefijos)
    main.get_r2 = lambda: bucket
    main.CLEANUP_TOKEN = token
    main.httpx = types.SimpleNamespace(
        AsyncClient=lambda **kw: ClienteFalso(paginas, total, error))
    return TestClient(main.app, raise_server_exceptions=False), bucket


def libro(bid, partes=2, tam=1_000_000):
    return {bid: [(f"{bid}/audio/part_{i}_voz.mp3", tam) for i in range(partes)]
                 + [(f"{bid}/text/part_0.txt", 4_000)]}


def docs(*ids):
    return [{"book_id": i, "$id": f"doc_{i}"} for i in ids]


VIVOS = {}
for _b in ("aaa1", "bbb2", "ccc3"):
    VIVOS.update(libro(_b))
CON_MUSICA = dict(VIVOS, **{"music": [("music/epico/tema.mp3", 2_000_000)]})


# ---------------------------------------------------------------------------
print("El token es lo único que protege el endpoint:")

cli, bucket = montar(CON_MUSICA, [docs("aaa1", "bbb2", "ccc3")], 3)
prueba("sin token -> 401",
       cli.get("/api/clean-orphans").status_code == 401)
prueba("token equivocado -> 401",
       cli.get("/api/clean-orphans?token=otro").status_code == 401)
prueba("token con acentos -> 401, no 500",
       cli.get("/api/clean-orphans?token=ñandú").status_code == 401,
       "compare_digest revienta con str no ASCII")
prueba("nada borrado tras los 401", bucket.borrados == [])

cli, _ = montar(CON_MUSICA, [docs("aaa1")], 1, token="")
prueba("servicio sin CLEANUP_TOKEN -> 503",
       cli.get("/api/clean-orphans?token=algo").status_code == 503)


# ---------------------------------------------------------------------------
print("\nEN LA DUDA NO BORRA — esto es lo que importa:")

cli, bucket = montar(CON_MUSICA, [], 0, error="conexión perdida")
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
prueba("Appwrite caído -> 502", r.status_code == 502)
prueba("Appwrite caído -> no borra NADA", bucket.borrados == [],
       f"borró {len(bucket.borrados)} claves")

cli, bucket = montar(CON_MUSICA, [[]], 0)
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
prueba("base de datos vacía -> 502", r.status_code == 502)
prueba("base de datos vacía -> no borra nada", bucket.borrados == [])

# Dice tener 3 y solo entrega 1: la lista está incompleta.
cli, bucket = montar(CON_MUSICA, [docs("aaa1")], 3)
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
prueba("lista incompleta (1 de 3) -> 502", r.status_code == 502)
prueba("lista incompleta -> no borra nada", bucket.borrados == [],
       "AQUÍ SE PERDERÍA LA BIBLIOTECA")

# Appwrite no dice el total: tampoco se puede confiar.
class SinTotal(ClienteFalso):
    async def get(self, *a, **k):
        return RespuestaFalsa({"documents": docs("aaa1")})

bucket = BucketFalso(CON_MUSICA)
main.get_r2 = lambda: bucket
main.CLEANUP_TOKEN = "secreto-de-prueba"
main.httpx = types.SimpleNamespace(AsyncClient=lambda **kw: SinTotal([], 0))
cli = TestClient(main.app, raise_server_exceptions=False)
prueba("sin campo total -> 502",
       cli.get("/api/clean-orphans?token=secreto-de-prueba").status_code == 502)
prueba("sin campo total -> no borra nada", bucket.borrados == [])


# ---------------------------------------------------------------------------
print("\nEl tope del 30% es la segunda red:")

muchos = dict(VIVOS)
for b in ("h1", "h2", "h3", "h4"):
    muchos.update(libro(b))
cli, bucket = montar(muchos, [docs("aaa1", "bbb2", "ccc3")], 3)
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
prueba("4 huérfanos de 7 prefijos -> 409", r.status_code == 409)
prueba("pasado el tope -> no borra nada", bucket.borrados == [])
prueba("el 409 dice cuántos son", "4 de 7" in r.json().get("detail", ""),
       r.json())


# ---------------------------------------------------------------------------
print("\nLo que sí debe hacer:")

cli, bucket = montar(CON_MUSICA, [docs("aaa1", "bbb2", "ccc3")], 3)
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
d = r.json()
prueba("todo vivo -> 200", r.status_code == 200)
prueba("todo vivo -> 0 huérfanos", d["huerfanos"] == 0, d)
prueba("music/ no es un libro huérfano", bucket.borrados == [],
       f"borró {bucket.borrados}")
prueba("cuenta bien los libros vivos", d["libros_vivos"] == 3, d)

uno_muerto = dict(CON_MUSICA, **libro("zzz9", partes=3))
cli, bucket = montar(uno_muerto, [docs("aaa1", "bbb2", "ccc3")], 3)
d = cli.get("/api/clean-orphans?token=secreto-de-prueba").json()
prueba("un huérfano -> lo encuentra", d["huerfanos"] == 1, d)
prueba("borra sus 4 archivos", d["files_deleted"] == 4, d)
prueba("borra SOLO lo suyo",
       all(k.startswith("zzz9/") for k in bucket.borrados), bucket.borrados)
prueba("no toca a los vivos", len(bucket.borrados) == 4, bucket.borrados)
prueba("informa los megas", d["megas"] > 2.8, d)
prueba("el detalle nombra el libro",
       d["detalle"][0]["book_id"] == "zzz9", d["detalle"])

cli, bucket = montar(uno_muerto, [docs("aaa1", "bbb2", "ccc3")], 3)
d = cli.get("/api/clean-orphans?token=secreto-de-prueba&dry=true").json()
prueba("simulación -> informa igual", d["huerfanos"] == 1 and d["dry_run"], d)
prueba("simulación -> NO borra", bucket.borrados == [], bucket.borrados)


# ---------------------------------------------------------------------------
print("\nLos casos que casi se nos cuelan:")

# Un documento sin book_id: su carpeta parecería huérfana.
sin_bid = [{"$id": "aaa1"}] + docs("bbb2", "ccc3")
cli, bucket = montar(CON_MUSICA, [sin_bid], 3)
d = cli.get("/api/clean-orphans?token=secreto-de-prueba").json()
prueba("documento sin book_id -> se salva por su $id",
       d["huerfanos"] == 0 and bucket.borrados == [], d)

# Más de cien libros: la paginación tiene que traerlos todos.
grandes = {}
ids = [f"lib{i:03d}" for i in range(250)]
for b in ids:
    grandes.update(libro(b, partes=1, tam=10))
paginas = [docs(*ids[i:i + 100]) for i in range(0, 250, 100)]
cli, bucket = montar(grandes, paginas, 250)
d = cli.get("/api/clean-orphans?token=secreto-de-prueba").json()
prueba("250 libros en 3 páginas -> los 250 vivos", d["libros_vivos"] == 250, d)
prueba("250 libros -> 0 huérfanos", d["huerfanos"] == 0, d)
prueba("250 libros -> no borra nada", bucket.borrados == [])

# Bucket vacío: ni error ni borrado.
cli, bucket = montar({}, [docs("aaa1")], 1)
r = cli.get("/api/clean-orphans?token=secreto-de-prueba")
prueba("bucket vacío -> 200 y cero", r.status_code == 200
       and r.json()["huerfanos"] == 0, r.json())

# Solo music/: no es huérfano aunque no haya ningún libro en el bucket.
cli, bucket = montar({"music": [("music/x.mp3", 10)]}, [docs("aaa1")], 1)
d = cli.get("/api/clean-orphans?token=secreto-de-prueba").json()
prueba("solo music/ -> 0 huérfanos", d["huerfanos"] == 0 and not bucket.borrados, d)


print("\n" + "=" * 54)
print(f"{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
