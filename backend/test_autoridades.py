# -*- coding: utf-8 -*-
"""El autocompletado de autores: que la lista pequeña acierte.

LO QUE SE VIGILA
----------------
Un autocompletado no falla con un error: falla enseñando la sugerencia
equivocada en el primer puesto, y el usuario la acepta. Asi que lo que se
comprueba no es que devuelva algo, sino QUE DEVUELVE PRIMERO.

Y una cosa mas, que es la que justifica el diseño: la lista tiene que crecer
sola con la biblioteca. Si eso se rompiera, la funcion seguiria respondiendo
—solo que con menos nombres cada vez— y nadie se enteraria.
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

import autoridades                                              # noqa: E402

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


def nombres(sugerencias):
    return [s["nombre"] for s in sugerencias]


def catalogo_real():
    """Los autores de verdad de la biblioteca, si hay un volcado a mano."""
    for ruta in [RAIZ.parents[1] / "libros2.json", RAIZ.parents[1] / "libros.json"]:
        if ruta.is_file():
            with open(ruta, encoding="utf-8") as fh:
                return [x.get("author", "") for x in json.load(fh)], ruta.name
    return None, None


def main() -> int:
    print("La mezcla —semilla mas lo que ya se usa:")
    lista = autoridades.mezclar(
        ["Sigmund Freud", "Sigmund Freud", "Homero", "Desconocido", ""],
        de_semilla=["Jane Austen", "Homero", "sigmund freud"])
    d = {x["nombre"]: x["usos"] for x in lista}
    prueba("«Desconocido» no entra en la lista", "Desconocido" not in d, d)
    prueba("las cadenas vacias tampoco", "" not in d)
    prueba("cuenta los usos", d.get("Sigmund Freud") == 2, d)
    prueba("no repite por mayusculas ni acentos",
           len([k for k in d if k.lower() == "sigmund freud"]) == 1, list(d))
    prueba("gana el nombre que ya se usa, no el de la semilla",
           "Sigmund Freud" in d and "sigmund freud" not in d, list(d))
    prueba("un autor solo de la semilla entra con 0 usos",
           d.get("Jane Austen") == 0, d)
    prueba("lo mas usado va primero", lista[0]["nombre"] == "Sigmund Freud",
           nombres(lista))

    print("\nQue sale PRIMERO, que es lo unico que importa:")
    prueba("sin escribir nada, lo mas usado",
           nombres(autoridades.buscar("", lista, 1)) == ["Sigmund Freud"])
    prueba("«ja» encuentra a Jane Austen",
           "Jane Austen" in nombres(autoridades.buscar("ja", lista)))
    prueba("un prefijo que no casa con nadie devuelve vacio",
           autoridades.buscar("zzzz", lista) == [])

    print("\nContra la biblioteca de verdad:")
    autores, fuente = catalogo_real()
    if autores is None:
        print("  -     se salta: no hay volcado del catalogo")
    else:
        real = autoridades.mezclar(autores)
        print(f"        ({fuente}: {len(autores)} libros -> {len(real)} autores)")
        prueba("hay mas autores que los de la semilla sola",
               len(real) >= len(autoridades.semilla()), len(real))
        prueba("Freud encabeza, que es quien mas libros tiene",
               real[0]["nombre"] == "Sigmund Freud", nombres(real[:3]))

        casos = [
            ("ga",      "Gabriel García Márquez"),
            ("garcia",  "Gabriel García Márquez"),   # sin tilde
            ("GARCÍA",  "Gabriel García Márquez"),   # mayusculas
            ("freud",   "Sigmund Freud"),
            ("seneca",  "Séneca"),
            ("kuang",   "R. F. Kuang"),
            ("bukow",   "Charles Bukowski"),
            ("tolst",   "León Tolstói"),
            ("gab mar", "Gabriel García Márquez"),   # dos trozos
        ]
        for consulta, esperado in casos:
            salida = nombres(autoridades.buscar(consulta, real, 5))
            prueba(f"«{consulta}» -> {esperado}", salida[:1] == [esperado], salida)

        prueba("«mar» ofrece a los cuatro Mar-",
               len([n for n in nombres(autoridades.buscar("mar", real, 8))
                    if autoridades.normalizar(n).startswith("mar")
                    or " mar" in " " + autoridades.normalizar(n)]) >= 3,
               nombres(autoridades.buscar("mar", real, 8)))
        prueba("el limite se respeta",
               len(autoridades.buscar("a", real, 3)) == 3)
        prueba("ningun «Desconocido» se cuela",
               not any(x["nombre"] == "Desconocido" for x in real))

    print("\nLa lista crece con la biblioteca —si esto se rompe, nada avisa:")
    autoridades.olvidar()
    viva = autoridades.lista_viva(lambda: ["Autor Nuevo Inventado"], ahora=1000)
    prueba("un autor nuevo de la biblioteca aparece",
           any(x["nombre"] == "Autor Nuevo Inventado" for x in viva))
    prueba("y la semilla sigue estando",
           any(x["nombre"] == "Allan Kardec" for x in viva))

    print("\nSi la biblioteca no contesta, no se queda en blanco:")
    autoridades.olvidar()

    def rota():
        raise RuntimeError("Appwrite no contesta")

    caida = autoridades.lista_viva(rota, ahora=2000)
    prueba("responde con la semilla en vez de con una lista vacia",
           len(caida) == len(autoridades.semilla()), len(caida))
    prueba("y la semilla no esta vacia", len(autoridades.semilla()) > 50,
           len(autoridades.semilla()))

    print("\nLa cache, que es lo que evita 500 lecturas por palabra tecleada:")
    autoridades.olvidar()
    veces = {"n": 0}

    def contando():
        veces["n"] += 1
        return ["Alguien Contado"]

    autoridades.lista_viva(contando, ahora=3000)
    autoridades.lista_viva(contando, ahora=3000 + autoridades.CACHE_S - 1)
    prueba("dentro del minuto no vuelve a leer", veces["n"] == 1, veces["n"])
    autoridades.lista_viva(contando, ahora=3000 + autoridades.CACHE_S + 1)
    prueba("pasado el minuto si", veces["n"] == 2, veces["n"])
    autoridades.olvidar()

    print("\n" + "=" * 54)
    print(f"{ok} OK · {fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
