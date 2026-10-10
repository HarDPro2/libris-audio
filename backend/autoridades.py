#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autocompletado de autores: la lista pequeña que acierta.

LA IDEA, Y POR QUE NO ES «MILLONES DE AUTORES»
----------------------------------------------
Un autocompletado sobre diez millones de nombres **empeora** segun crece: quien
sube un libro ya sabe de quien es, y lo que necesita no es descubrirlo sino
escribirlo IGUAL QUE LA VEZ ANTERIOR. Eso es normalizar, no sugerir. Contra
sesenta nombres, teclear «ga» devuelve «Gabriel Garcia Marquez». Contra diez
millones devuelve miles de autores de catalogo de biblioteca que no son.

Asi que la lista es pequeña a proposito, y sale de dos sitios:

  1. La SEMILLA, `autoridades_semilla.json`: los nombres canonicos ya escritos
     y revisados a mano al separar autor y titulo del catalogo (ver autores.py).
  2. Los autores EN USO, que son los valores distintos de `author` en
     `global_books`.

El segundo es la parte importante y es la que hace que esto crezca solo: cada
libro que se sube con autor lo mete en la lista sin que nadie sincronice nada.
No hay tabla nueva, no hay escritura, no hay nada que se desincronice.

Lo cual importa porque **Cloud Run es efimero**: una lista que creciera en un
archivo del contenedor se perderia al reiniciar, y nadie se enteraria —la
funcion seguiria respondiendo, solo que cada vez con menos nombres—.

LO QUE NO HACE, TODAVIA
-----------------------
Consultar Wikidata para un autor que no esta en la lista. Se escribira cuando
se pueda PROBAR contra la API de verdad; escribir un parser de JSON contra una
forma supuesta es como empezamos el dia. Wikidata es CC0, asi que cuando llegue
se podra empaquetar hasta en un producto comercial.
"""
import json
import os
import time
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
SEMILLA = os.path.join(AQUI, "autoridades_semilla.json")

# Cuanto vale la pena recordar la lista antes de volver a pedirla. Un minuto:
# el autocompletado teclea rapido y la biblioteca cambia despacio.
CACHE_S = 60
_cache = {"cuando": 0.0, "lista": None}


def normalizar(texto):
    """Minusculas y sin acentos, para que «garcia» encuentre «García»."""
    base = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in base if not unicodedata.combining(c)).lower().strip()


def semilla():
    try:
        with open(SEMILLA, encoding="utf-8") as fh:
            return [n for n in json.load(fh) if isinstance(n, str) and n.strip()]
    except Exception:
        # Sin semilla el autocompletado sigue funcionando con los autores en
        # uso. Que falte el archivo no puede tumbar una subida.
        return []


def _clave(nombre):
    return normalizar(nombre)


def mezclar(en_uso, de_semilla=None):
    """Una lista de {nombre, usos}, sin repetidos, lo mas usado primero.

    `en_uso` son los valores de `author` tal como estan en la biblioteca, con
    repeticiones: ocho libros de Freud traen «Sigmund Freud» ocho veces, y eso
    es justo lo que lo sube en el orden.
    """
    cuenta, canon = {}, {}
    for nombre in en_uso or []:
        n = (nombre or "").strip()
        if not n or _clave(n) == "desconocido":
            continue
        k = _clave(n)
        cuenta[k] = cuenta.get(k, 0) + 1
        canon.setdefault(k, n)
    for nombre in (semilla() if de_semilla is None else de_semilla):
        k = _clave(nombre)
        if k and k not in cuenta:
            cuenta[k] = 0
            canon[k] = nombre
    return sorted(({"nombre": canon[k], "usos": v} for k, v in cuenta.items()),
                  key=lambda x: (-x["usos"], normalizar(x["nombre"])))


def _rango(nombre, consulta):
    """Como de bien casa. Menor es mejor; None es que no casa.

    0  el nombre entero empieza por lo tecleado      «gab» -> Gabriel...
    1  alguna palabra empieza por lo tecleado        «mar» -> Gabriel García Márquez
    2  lo tecleado aparece dentro                    «arquez»
    """
    n, q = normalizar(nombre), normalizar(consulta)
    if not q:
        return 3
    if n.startswith(q):
        return 0
    if any(p.startswith(q) for p in n.split()):
        return 1
    if q in n:
        return 2
    # Varias palabras: «gab mar» tiene que encontrar a García Márquez.
    trozos = [t for t in q.split() if t]
    if len(trozos) > 1:
        palabras = n.split()
        if all(any(p.startswith(t) for p in palabras) for t in trozos):
            return 1
    return None


def buscar(consulta, lista, limite=8):
    """Los que casan, ordenados por lo bien que casan y por lo usados que son."""
    salida = []
    for item in lista:
        r = _rango(item["nombre"], consulta)
        if r is not None:
            salida.append((r, -item["usos"], normalizar(item["nombre"]), item))
    salida.sort(key=lambda x: x[:3])
    return [x[3] for x in salida[:max(1, int(limite or 8))]]


def lista_viva(leer_autores, ahora=None):
    """La lista completa, recordada un minuto.

    `leer_autores` es una funcion que devuelve los `author` de la biblioteca.
    Se pasa desde fuera para que esto se pueda probar sin Appwrite y sin red.
    """
    t = ahora if ahora is not None else time.time()
    if _cache["lista"] is not None and t - _cache["cuando"] < CACHE_S:
        return _cache["lista"]
    try:
        en_uso = list(leer_autores() or [])
    except Exception:
        # Si la biblioteca no contesta, el autocompletado se queda con la
        # semilla en vez de quedarse vacio y parecer que no hay autores.
        en_uso = []
    lista = mezclar(en_uso)
    _cache.update({"cuando": t, "lista": lista})
    return lista


def olvidar():
    _cache.update({"cuando": 0.0, "lista": None})
