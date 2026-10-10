# -*- coding: utf-8 -*-
"""El vigilante, probado contra las respuestas REALES del 10-10-2026.

Los cuerpos de abajo no son inventados: son los que devolvio Cloud Run ese
dia, copiados tal cual. Un vigilante probado contra respuestas imaginadas
avisa de lo que imaginamos, no de lo que pasa.

El fallo que esto evita: que el vigilante diga «todo bien» cuando no lo esta.
Un vigilante demasiado optimista es peor que ninguno, porque ademas tranquiliza.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from comprobar import (BIEN, CAIDO, DEGRADADO, LENTO, PLATAFORMA,  # noqa: E402
                       clasificar, diagnostico, revisar)

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


# ── Lo que devolvio Cloud Run de verdad cuando cayo la facturacion ──────────
GOOGLE_503 = """<html><head>
<meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>503 Server Error</title>
</head>
<body text=#000000 bgcolor=#ffffff>
<h1>Error: Server Error</h1>
<h2>The service you requested is not available yet.<p>Please try again in 30 seconds.</h2>
<h2></h2>
</body></html>"""

GOOGLE_500 = """<html><head>
<title>500 Server Error</title>
</head><body>
<h1>Error: Server Error</h1>
<h2>The server encountered an error and could not complete your request.<p>Please try again in 30 seconds.</h2>
</body></html>"""

# Un trozo del catalogo de verdad, con un libro real
CATALOGO_BUENO = ('[{"id":"487baf6e","book_id":"8ade9383c727",'
                  '"title":"Dias de sangre y resplandor","author":"Laini Taylor",'
                  '"parts_count":203,"category":"Fantasía","added_by":"biblioteca"}]')

# Lo que /api/books inventa cuando Appwrite no contesta (de main.py)
CATALOGO_INVENTADO = ('[{"id": "1", "book_id": "9780140449136", '
                      '"title": "La Odisea", "author": "Homero", '
                      '"parts_count": 5, "category": "Clásicos", '
                      '"added_by": "Libris"}, '
                      '{"id": "2", "title": "Don Quijote de la Mancha", '
                      '"added_by": "Libris"}]')


def main() -> int:
    print("Lo que paso de verdad el 10-10 — paginas de error de Google:")
    s, p = clasificar(503, GOOGLE_503, 0.22)
    prueba("el 503 de Google es PLATAFORMA, no un fallo de la app", s == PLATAFORMA, f"{s}: {p}")
    prueba("y lo explica", "facturacion" in p.lower() or "Facturacion" in p, p)
    s, p = clasificar(500, GOOGLE_500, 0.40)
    prueba("el 500 de Google, igual", s == PLATAFORMA, f"{s}: {p}")

    print("\nUn 500 de TU aplicacion es otra cosa y hay que distinguirlo:")
    s, p = clasificar(500, '{"error":"no_se_pudo_sintetizar","detalle":"..."}', 2.0)
    prueba("el 500 con JSON propio es CAIDO, no PLATAFORMA", s == CAIDO, f"{s}: {p}")

    print("\nNo contestar:")
    s, p = clasificar(0, "TimeoutError: timed out", 90.0)
    prueba("sin respuesta es CAIDO", s == CAIDO, s)

    print("\nEl 200 que miente —el fallo que no da error:")
    s, p = clasificar(200, CATALOGO_INVENTADO, 1.0, es_catalogo=True)
    prueba("catalogo con los libros inventados es DEGRADADO", s == DEGRADADO, f"{s}: {p}")
    prueba("y dice que Appwrite no contesta", "appwrite" in p.lower(), p)
    s, p = clasificar(200, CATALOGO_BUENO, 1.0, es_catalogo=True)
    prueba("el catalogo de verdad pasa", s == BIEN, f"{s}: {p}")
    s, p = clasificar(200, CATALOGO_INVENTADO, 1.0, es_catalogo=False)
    prueba("fuera del catalogo no se aplica esa regla", s == BIEN, s)

    print("\nLento no es caido —un arranque en frio tarda:")
    s, p = clasificar(200, "{}", 11.2)
    prueba("11 s despues de dos dias parado es normal", s == BIEN, f"{s}: {p}")
    s, p = clasificar(200, "{}", 48.0)
    prueba("48 s ya se avisa, pero no es caida", s == LENTO, f"{s}: {p}")

    print("\nOtros codigos:")
    prueba("404 de la app = viva", clasificar(404, "Not Found", 0.3)[0] == BIEN)
    prueba("403 se avisa (pudo cambiar un permiso)",
           clasificar(403, "Forbidden", 0.3)[0] == CAIDO)
    prueba("200 normal", clasificar(200, '{"ok":true}', 0.4)[0] == BIEN)

    print("\nLa conclusion, que es lo que ahorra el tiempo:")
    todos_plataforma = [{"situacion": PLATAFORMA} for _ in range(5)]
    d = diagnostico(todos_plataforma)
    prueba("si caen TODOS con error de plataforma, manda mirar la facturacion",
           "FACTURACION" in d.upper(), d)
    prueba("y da el comando", "billing" in d, d)
    uno = [{"situacion": CAIDO}] + [{"situacion": BIEN} for _ in range(4)]
    prueba("si cae uno solo, no culpa a la facturacion",
           "FACTURACION" not in diagnostico(uno).upper(), diagnostico(uno))
    prueba("si no cae ninguno, no dice nada",
           diagnostico([{"situacion": BIEN}] * 5) == "")

    print("\nLa ronda entera, con respuestas falsas pero reales:")
    servicios = [
        {"nombre": "uno", "producto": "A", "url": "http://x/health",
         "catalogo": "http://x/books"},
        {"nombre": "dos", "producto": "B", "url": "http://y/"},
    ]

    def red_fingida(url):
        if url.endswith("/books"):
            return 200, CATALOGO_INVENTADO, 0.5      # salud bien, catalogo mintiendo
        if url.startswith("http://x"):
            return 200, '{"ok":true}', 0.3
        return 503, GOOGLE_503, 0.2

    inf = revisar(servicios, pedir_fn=red_fingida)
    prueba("el primero sale DEGRADADO aunque su /health diera 200",
           inf[0]["situacion"] == DEGRADADO, inf[0])
    prueba("el segundo sale PLATAFORMA", inf[1]["situacion"] == PLATAFORMA, inf[1])
    prueba("se guarda el tiempo de cada uno",
           all("segundos" in f for f in inf))

    print("\n" + "=" * 54)
    print(f"{ok} OK · {fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
