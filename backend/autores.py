#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Separa el autor del titulo en el catalogo (Appwrite `global_books`).

POR QUE EXISTE
--------------
Los 97 libros del catalogo tienen `author = "Desconocido"` y el autor metido
dentro del titulo: «Crimen y castigo Dostoyevski Fiodor». El atributo `author`
existe en la coleccion con ese valor por defecto, y NADIE lo escribe nunca:
`main.py` no lo incluye al registrar un libro. Asi que no se puede buscar ni
ordenar por autor, y la ficha no lo puede enseñar.

LO QUE ESTE SCRIPT NO HACE
--------------------------
No adivina. En el catalogo hay siete patrones distintos y ninguna regla los
cubre todos:

    1984 George Orwell                       autor al final
    Albert Camus El Extranjero               autor al principio
    Crimen y castigo Dostoyevski Fiodor      apellido primero, sin coma
    Miyamoto, Musashi   El Libro De...       apellido primero, con coma
    El dios en llamas (R. F. Kuang)          entre parentesis
    charles bukowsky la senda del perdedor   minusculas y apellido mal escrito
    cadáver exquisito                        sin autor

Una expresion regular que intente con todos **se inventa autores**, y un autor
inventado es peor que un campo vacio: el vacio se ve, el invento no. Asi que
aqui el autor sale de un CATALOGO EXPLICITO que esta mas abajo y se puede
leer. Lo que no casa con el catalogo se queda como esta y se marca para que lo
mire una persona.

COMO SE USA
-----------
    python autores.py --desde libros.json      # propone, escribe el CSV
    python autores.py                          # igual, leyendo de Appwrite

Sale `autores_propuesta.csv`. Lo abres, miras la columna `confianza`, corriges
lo que haga falta y pones `si` en `aprobar` en las filas que quieras. Despues:

    $env:APPWRITE_API_KEY="<clave de servidor>"
    python autores.py --aplicar

Solo se escriben las filas con `aprobar = si`. Las demas no se tocan.
"""
import csv
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV_SALIDA = os.path.join(AQUI, "autores_propuesta.csv")
COLL = "global_books"

# ─────────────────────────────────────────────────────────────────────────────
# EL CATALOGO DE AUTORES
#
# canonico -> como aparece escrito en los titulos.
# Las variantes incluyen las erratas REALES que hay en el catalogo
# («HGuxley», «bukowsky», «EckhartTolle»): no se corrigen a mano en la base,
# se reconocen aqui y se guarda el nombre canonico.
#
# Una variante que acaba en «!» es PARCIAL —solo el apellido, o un nombre que
# tambien podria ser parte de un titulo— y fuerza revision humana aunque case.
# ─────────────────────────────────────────────────────────────────────────────
CATALOGO = {
    "George Orwell":            ["George Orwell"],
    "Albert Camus":             ["Albert Camus"],
    "Aldous Huxley":            ["Aldous HGuxley", "Aldous Huxley"],
    "León Tolstói":             ["Leon Tolstoi", "Tolstoi Leon"],
    "Confucio":                 ["Confucio"],
    "Arthur Schopenhauer":      ["Arthur Schopenhauer"],
    "Friedrich Nietzsche":      ["Friedrich Nietzsche"],
    "B. F. Skinner":            ["B. f. Skinner", "B. F. Skinner"],
    "Charles Bukowski":         ["Charles Bukowski", "charles bukowsky"],
    "Gabriel García Márquez":   ["Gabriel Garcia Marquez"],
    "Ralph Waldo Emerson":      ["Ralph Waldo Emerson"],
    "Fiódor Dostoyevski":       ["Dostoyevski Fiodor", "Fiodor Dostoyevski"],
    "Immanuel Kant":            ["Immanuel Kant"],
    "Daniel Kahneman":          ["Daniel Kahneman"],
    "Séneca":                   ["Seneca"],
    "Laini Taylor":             ["Laini Taylor"],
    "René Descartes":           ["Rene Descartes"],
    "Miguel de Cervantes":      ["Cervantes Miguel", "Miguel de Cervantes"],
    "Sun Tzu":                  ["Sun Tzu"],
    "Epicteto":                 ["Epicteto"],
    "Voltaire":                 ["Voltaire"],
    "Franz Kafka":              ["Kafka Franz", "Franz Kafka"],
    "R. F. Kuang":              ["R. F. Kuang"],
    "Mark Twain":               ["Mark Twain"],
    "Edgar Allan Poe":          ["Allan Poe Edgar", "Edgar Allan Poe"],
    "Oscar Wilde":              ["Wilde Oscar", "Oscar Wilde"],
    "Francis Scott Fitzgerald": ["Francis Scott Fitzgerald"],
    "Anónimo":                  ["Anonimo"],
    "Allan Kardec":             ["Allan Kardec"],
    "Eckhart Tolle":            ["Eckhart Tolle", "EckhartTolle"],
    "Nicolás Maquiavelo":       ["Nicolas Maquiavelo"],
    "Sigmund Freud":            ["Sigmund Freud"],
    "Emily Brontë":             ["Emily Bronte"],
    "Epicuro":                  ["Epicuro"],
    "Aristóteles":              ["Aristoteles"],
    "William Shakespeare":      ["Shakespeare William", "William Shakespeare"],
    "James Clear":              ["James Clear"],
    "Isaac Asimov":             ["Isaac Asimov"],
    "Jean Piaget":              ["Jean Piaget"],
    "Jorge Luis Borges":        ["Jorge Luis Borges"],
    "Juan Rulfo":               ["Juan Rulfo"],
    "Dante Alighieri":          ["Dante Alighieri"],
    "Homero":                   ["Homero"],
    "Platón":                   ["Platon"],
    "Vicent Guillem":           ["Vicent Guillem"],
    "Víctor Hugo":              ["Hugo Victor", "Victor Hugo"],
    "Eurípides":                ["Euripides"],
    "Marco Aurelio":            ["Marco Aurelio"],
    "Miyamoto Musashi":         ["Miyamoto Musashi"],
    "Jane Austen":              ["Jane Austen"],
    "Jean-Jacques Rousseau":    ["Jean Jacques Rousseau"],
    "Earle Herrera":            ["Earle Herrera"],
    "Marcel Proust":            ["Proust Marcel", "Marcel Proust"],
    "Gustave Le Bon":           ["Gustave Le Bon"],
    "Ray Bradbury":             ["Ray Bradbury"],
    "Julio Cortázar":           ["Julio Cortazar"],
    "Roger Zelazny":            ["Roger Zelazny"],
    "Jean-Paul Sartre":         ["Jean Paul Sartre", "Sartre!"],
    "Steven Pinker":            ["Steven Pinker"],
    "James Joyce":              ["James Joyce"],
    "Diógenes Laercio":         ["Diogenes Laercio"],
    "Viktor Frankl":            ["Viktor Frankl"],
    "Wilhelm Wundt":            ["Wilhelm Wundt"],
    "Chico Xavier":             ["Chico Xavier"],
    "André Luiz":               ["Andre Luis", "Andre Luiz"],
}

# Palabras que sobran en los bordes cuando se saca el autor de en medio.
# «Ulises Por James Joyce» deja «Ulises Por»; «el principe de Nicolas
# Maquiavelo» deja «el principe de».
# Solo nexos, NUNCA articulos: «El existencialismo es un humanismo» empieza
# por «El» de verdad, y quitarlo deja un titulo roto que nadie revisaria
# porque la fila saldria con confianza alta. Medido: paso en la primera
# version de este script.
PEGAMENTO = {"por", "de", "del", "y", "e"}
# Al FINAL si sobran, porque ahi no empieza ningun titulo.
PEGAMENTO_FINAL = PEGAMENTO | {"la", "el", "los", "las", "un", "una"}
BORDES = " \t,.;:·-–—_()[]{}«»\"'“”‘’"


def normalizar(texto):
    """Minusculas, sin acentos, puntuacion a espacios.

    Devuelve (normalizado, mapa) donde mapa[i] es el indice en el texto
    ORIGINAL del caracter i del normalizado. Hace falta para poder recortar
    el trozo del titulo original, con sus tildes y mayusculas intactas.
    """
    salida, mapa, ultimo_espacio = [], [], False
    for i, ch in enumerate(texto):
        base = "".join(c for c in unicodedata.normalize("NFD", ch)
                       if not unicodedata.combining(c)).lower()
        if not base:
            continue
        for c in base:
            if not c.isalnum():
                if ultimo_espacio:
                    continue
                c, ultimo_espacio = " ", True
            else:
                ultimo_espacio = False
            salida.append(c)
            mapa.append(i)
    return "".join(salida).strip(), mapa


def _normalizar_llano(texto):
    return normalizar(texto)[0]


def buscar(variante_norm, titulo_norm):
    """Donde cae la variante en el titulo, respetando limites de palabra."""
    desde = 0
    while True:
        i = titulo_norm.find(variante_norm, desde)
        if i < 0:
            return None
        fin = i + len(variante_norm)
        antes_ok = i == 0 or not titulo_norm[i - 1].isalnum()
        despues_ok = fin >= len(titulo_norm) or not titulo_norm[fin].isalnum()
        if antes_ok and despues_ok:
            return i, fin
        desde = i + 1


def limpiar(trozo):
    """Quita bordes y palabras de pegamento sueltas en los extremos."""
    t = trozo.strip(BORDES)
    cambio = True
    while cambio and t:
        cambio = False
        palabras = t.split()
        if palabras and _normalizar_llano(palabras[-1]) in PEGAMENTO_FINAL:
            t, cambio = " ".join(palabras[:-1]).strip(BORDES), True
        # Del PRINCIPIO no se quita ninguna palabra. «De la ira», «De la
        # brevedad de la vida», «El existencialismo es un humanismo»: los
        # titulos empiezan por nexos y articulos constantemente. Cuando el
        # autor va delante, lo que queda detras ya es el titulo entero y solo
        # hay que limpiar puntuacion. Medido: quitar «de» y «el» del principio
        # estropeaba seis titulos de 97, y los seis salian con confianza alta.
    # Comas que se quedan solas al sacar un nombre de en medio.
    t = " ".join(t.split())
    for sobra in (" , ,", ", ,", " ,", ",,"):
        while sobra in t:
            t = t.replace(sobra, "," if sobra.endswith(",") else ",")
    return " ".join(t.strip(BORDES).split())


def proponer(titulo):
    """(titulo_propuesto, autor, confianza, motivo)."""
    titulo_norm, mapa = normalizar(titulo)
    encontrados = []
    for canonico, variantes in CATALOGO.items():
        for v in variantes:
            parcial = v.endswith("!")
            vn = _normalizar_llano(v.rstrip("!"))
            if not vn:
                continue
            sitio = buscar(vn, titulo_norm)
            if sitio:
                encontrados.append((canonico, vn, sitio, parcial))

    if not encontrados:
        return titulo, "", "sin autor", "ningun autor del catalogo aparece en el titulo"

    # El mas largo gana: «Jorge Luis Borges» antes que un hipotetico «Borges».
    encontrados.sort(key=lambda x: len(x[1]), reverse=True)

    # ¿Varios autores DISTINTOS y que no se solapan? Eso lo mira una persona.
    distintos, ocupado = [], []
    for canonico, vn, (i, f), parcial in encontrados:
        if any(i < hf and f > hi for hi, hf in ocupado):
            continue
        ocupado.append((i, f))
        distintos.append((canonico, vn, (i, f), parcial))

    canonico, vn, (i, f), parcial = distintos[0]
    ini_orig, fin_orig = mapa[i], mapa[f - 1] + 1
    crudo = (titulo[:ini_orig] + "\u0000" + titulo[fin_orig:])
    resto = limpiar(crudo.replace("\u0000", " "))

    # En este catalogo el espacio doble separa de verdad: «B. f. Skinner···
    # Walden Dos», «Juan Rulfo···Pedro Paramo». Si DESPUES de sacar al autor
    # siguen quedando dos trozos separados asi, es que sobra algo —en «Viktor
    # Frankl Neurologo y psiquiatra···El hombre en busca de sentido» sobra la
    # profesion— y eso no lo puede decidir un script.
    sobra_un_trozo = "  " in crudo.replace("\u0000", "").strip()

    if len(distintos) > 1:
        otros = ", ".join(c for c, *_ in distintos[1:])
        return (resto or titulo, canonico, "revisar",
                f"el titulo nombra tambien a: {otros}")
    if parcial:
        return (resto or titulo, canonico, "revisar",
                "solo casa el apellido; podria ser parte del titulo")
    if len(resto) < 3:
        return (titulo, canonico, "revisar",
                "al quitar el autor no queda titulo")
    if sobra_un_trozo:
        return (resto, canonico, "revisar",
                "quedan dos trozos separados: puede que uno no sea del titulo")
    return resto, canonico, "alta", ""


# ─────────────────────────────────────────────────────────────────────────────
# Appwrite
# ─────────────────────────────────────────────────────────────────────────────
def ajustes_appwrite():
    sys.path.insert(0, AQUI)
    from ajustes import obligatoria
    return (
        os.environ.get("APPWRITE_ENDPOINT",
                       "https://nyc.cloud.appwrite.io/v1").rstrip("/"),
        obligatoria("APPWRITE_PROJECT_ID", "el proyecto de Appwrite"),
        obligatoria("APPWRITE_API_KEY", "para leer y escribir hace falta"),
        obligatoria("APPWRITE_DATABASE_ID", "la base de datos"),
    )


def api(metodo, ruta, cuerpo=None, params=None):
    endpoint, proyecto, clave, _ = ajustes_appwrite()
    url = endpoint + ruta
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo, headers={
        "X-Appwrite-Project": proyecto,
        "X-Appwrite-Key": clave,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            crudo = r.read().decode()
            return json.loads(crudo) if crudo else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from None


def catalogo_de_appwrite():
    _, _, _, db = ajustes_appwrite()
    r = api("GET", f"/databases/{db}/collections/{COLL}/documents",
            params={"queries[]": json.dumps({"method": "limit", "values": [500]})})
    return [{"id": d["$id"], "book_id": d.get("book_id", ""),
             "title": d.get("title", ""), "author": d.get("author", "")}
            for d in r.get("documents", [])]


def catalogo_de_archivo(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return [{"id": x.get("id", ""), "book_id": x.get("book_id", ""),
                 "title": x.get("title", ""), "author": x.get("author", "")}
                for x in json.load(fh)]


# ─────────────────────────────────────────────────────────────────────────────
def fase_proponer(libros):
    filas = []
    for libro in sorted(libros, key=lambda x: x["title"].lower()):
        titulo, autor, confianza, motivo = proponer(libro["title"])
        filas.append({
            "aprobar": "si" if confianza == "alta" else "",
            "book_id": libro["book_id"],
            "doc_id": libro["id"],
            "titulo_actual": libro["title"],
            "titulo_propuesto": titulo,
            "autor_propuesto": autor,
            "confianza": confianza,
            "motivo": motivo,
        })

    campos = ["aprobar", "confianza", "autor_propuesto", "titulo_propuesto",
              "titulo_actual", "motivo", "book_id", "doc_id"]
    with open(CSV_SALIDA, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)

    cuenta = {}
    for f in filas:
        cuenta[f["confianza"]] = cuenta.get(f["confianza"], 0) + 1
    print(f"{len(filas)} libros")
    for k in ("alta", "revisar", "sin autor"):
        if k in cuenta:
            print(f"  {cuenta[k]:3d}  {k}")
    print(f"\nEscrito: {CSV_SALIDA}")
    print("Las filas 'alta' vienen ya con aprobar=si. Revisa las demas,")
    print("corrige lo que falte y pon 'si' donde quieras aplicar.")
    print("Nada se ha tocado en Appwrite.")
    for f in filas:
        if f["confianza"] != "alta":
            print(f"\n  {f['confianza'].upper():9s} {f['titulo_actual']}")
            print(f"            -> titulo: {f['titulo_propuesto']!r}")
            print(f"               autor : {f['autor_propuesto']!r}")
            print(f"               porque: {f['motivo']}")
    return 0


def fase_aplicar():
    if not os.path.isfile(CSV_SALIDA):
        sys.exit(f"No encuentro {CSV_SALIDA}. Corre antes la propuesta.")
    _, _, _, db = ajustes_appwrite()
    with open(CSV_SALIDA, encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))

    aprobadas = [f for f in filas if f["aprobar"].strip().lower() in ("si", "sí", "x")]
    print(f"{len(aprobadas)} de {len(filas)} filas aprobadas.\n")
    if not aprobadas:
        return 0

    hechos, fallos = 0, []
    for f in aprobadas:
        if not f["autor_propuesto"].strip():
            fallos.append((f["titulo_actual"], "aprobada pero sin autor"))
            continue
        try:
            api("PATCH", f"/databases/{db}/collections/{COLL}/documents/{f['doc_id']}",
                {"data": {"title": f["titulo_propuesto"],
                          "author": f["autor_propuesto"]}})
            hechos += 1
            print(f"  OK  {f['autor_propuesto']:28s} · {f['titulo_propuesto']}")
        except Exception as e:
            fallos.append((f["titulo_actual"], str(e)[:160]))

    print(f"\n{hechos} actualizados.")
    if fallos:
        print(f"{len(fallos)} fallaron:")
        for t, por in fallos:
            print(f"  {t}\n    {por}")
        return 1
    return 0


def main():
    if "--aplicar" in sys.argv:
        return fase_aplicar()
    if "--desde" in sys.argv:
        ruta = sys.argv[sys.argv.index("--desde") + 1]
        return fase_proponer(catalogo_de_archivo(ruta))
    return fase_proponer(catalogo_de_appwrite())


if __name__ == "__main__":
    raise SystemExit(main())
