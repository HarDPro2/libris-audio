"""Numeros a palabras — la parte del espanol que tiene mas trampas de las que
parece.

POR QUE HACE FALTA
------------------
Kokoro no lee cifras: lee fonemas. «1605» tiene que llegar al fonemizador
convertido en «mil seiscientos cinco», o el TTS se lo salta o lo deletrea.

LAS TRAMPAS DEL ESPANOL, que son las que hacen esto menos trivial de lo que
parece:

    16-29   se escriben en UNA palabra: «dieciseis», «veintidos»
    31+     se escriben en TRES: «treinta y uno»
    100     es «cien» a secas, pero «ciento uno» si le sigue algo
    500     es «quinientos», no «cincocientos»
    700     es «setecientos», no «sietecientos»
    900     es «novecientos», no «nuevecientos»
    1000    es «mil», nunca «un mil»
    1000000 es «un millon», y el plural es «millones»

Y el genero: «veintiun libros» pero «veintiuna casas». Eso depende del
sustantivo que venga detras, que aqui no se conoce, asi que se usa el
masculino — que es lo que hace cualquier lector cuando la cifra va sola.
"""
from __future__ import annotations

UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
            "ocho", "nueve", "diez", "once", "doce", "trece", "catorce",
            "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
            "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
            "veinticinco", "veintiséis", "veintisiete", "veintiocho",
            "veintinueve"]
DECENAS = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
           70: "setenta", 80: "ochenta", 90: "noventa"}
CENTENAS = {100: "ciento", 200: "doscientos", 300: "trescientos",
            400: "cuatrocientos", 500: "quinientos", 600: "seiscientos",
            700: "setecientos", 800: "ochocientos", 900: "novecientos"}

ORDINALES = ["", "primero", "segundo", "tercero", "cuarto", "quinto", "sexto",
             "séptimo", "octavo", "noveno", "décimo", "undécimo",
             "duodécimo", "decimotercero", "decimocuarto", "decimoquinto",
             "decimosexto", "decimoséptimo", "decimoctavo", "decimonoveno",
             "vigésimo"]

ROMANOS = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def cardinal(n: int) -> str:
    """El numero en palabras. Solo enteros, positivos o negativos."""
    if n < 0:
        return "menos " + cardinal(-n)
    if n < 30:
        return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        base = DECENAS[d * 10]
        return base if u == 0 else f"{base} y {UNIDADES[u]}"
    if n < 1000:
        c, r = divmod(n, 100)
        if n == 100:
            return "cien"          # «cien» a secas; «ciento uno» si sigue algo
        return CENTENAS[c * 100] + ("" if r == 0 else " " + cardinal(r))
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        miles = "mil" if m == 1 else f"{cardinal(m)} mil"   # nunca «un mil»
        return miles + ("" if r == 0 else " " + cardinal(r))
    if n < 1_000_000_000_000:
        m, r = divmod(n, 1_000_000)
        millon = "un millón" if m == 1 else f"{cardinal(m)} millones"
        return millon + ("" if r == 0 else " " + cardinal(r))
    b, r = divmod(n, 1_000_000_000_000)
    billon = "un billón" if b == 1 else f"{cardinal(b)} billones"
    return billon + ("" if r == 0 else " " + cardinal(r))


def ordinal(n: int) -> str:
    """«primero», «segundo»... Por encima de 20 se lee el cardinal, que es lo
    que hace todo el mundo: nadie dice «trigesimo septimo capitulo»."""
    if 1 <= n < len(ORDINALES):
        return ORDINALES[n]
    return cardinal(n)


def desde_romano(s: str) -> int | None:
    """El valor de un numero romano, o None si no lo es.

    Se exige la forma CANONICA: «IIII» no vale aunque se entienda, porque una
    palabra como «iii» de un indice mal extraido no debe convertirse en nada.
    """
    t = s.lower()
    if not t or any(c not in ROMANOS for c in t):
        return None
    total, anterior = 0, 0
    for c in reversed(t):
        v = ROMANOS[c]
        if v < anterior:
            total -= v
        else:
            total += v
            anterior = v
    if total <= 0 or total > 3999:
        return None
    # La comprobacion que lo hace seguro: si al volver a escribirlo no sale lo
    # mismo, es que no era un romano bien formado.
    return total if a_romano(total) == t.upper() else None


def a_romano(n: int) -> str:
    tabla = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
             (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
             (5, "V"), (4, "IV"), (1, "I")]
    salida = []
    for valor, letra in tabla:
        while n >= valor:
            salida.append(letra)
            n -= valor
    return "".join(salida)
