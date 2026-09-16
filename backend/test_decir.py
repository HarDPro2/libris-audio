"""Numeros, romanos y abreviaturas — lo que hay que arreglar antes de leer.

EL PRINCIPIO QUE GOBIERNA TODO ESTO: ante la duda, no se toca. Corre sobre el
texto que va a leer el TTS, sin nadie mirando, y un cambio malo no se descubre
hasta que alguien escucha el audiolibro y oye un disparate.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from decir import juntar_tiempos, mapear, normalizar_mapeado, normalizar
from numeros import a_romano, cardinal, desde_romano, ordinal

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


def main():
    print("Los numeros, con las trampas del espanol:")
    for n, esperado in (
        (0, "cero"), (15, "quince"),
        (16, "dieciséis"),          # de 16 a 29 va en UNA palabra
        (21, "veintiuno"), (22, "veintidós"),
        (31, "treinta y uno"),      # de 31 arriba, en tres
        (100, "cien"),              # «cien» a secas
        (101, "ciento uno"),        # «ciento» si le sigue algo
        (500, "quinientos"),        # no «cincocientos»
        (700, "setecientos"),       # no «sietecientos»
        (900, "novecientos"),       # no «nuevecientos»
        (1000, "mil"),              # nunca «un mil»
        (1605, "mil seiscientos cinco"),
        (100_000, "cien mil"),
        (1_000_000, "un millón"),
        (2_000_000, "dos millones"),
        (-5, "menos cinco"),
    ):
        prueba(f"{n:,} -> {esperado}", cardinal(n) == esperado, cardinal(n))

    print("\nOrdinales, y donde dejan de usarse:")
    prueba("1 -> primero", ordinal(1) == "primero")
    prueba("13 -> decimotercero", ordinal(13) == "decimotercero")
    prueba("por encima de 20 se dice el cardinal, que es lo que hace todo el "
           "mundo", ordinal(37) == "treinta y siete", ordinal(37))

    print("\nRomanos — y sobre todo, cuando NO son romanos:")
    for r, v in (("XIX", 19), ("XVI", 16), ("IV", 4), ("MCMLXXXIV", 1984),
                 ("XLII", 42)):
        prueba(f"{r} = {v}", desde_romano(r) == v, desde_romano(r))
    prueba("«IIII» no vale: no esta bien formado",
           desde_romano("IIII") is None)
    prueba("una palabra cualquiera tampoco", desde_romano("abc") is None)
    prueba("ni el vacio", desde_romano("") is None)
    prueba("ida y vuelta", a_romano(1984) == "MCMLXXXIV")

    print("\nEn el texto, un romano solo se convierte si el contexto lo dice:")
    prueba("«el cap. XII» si",
           "capítulo doce" in normalizar("el cap. XII"),
           normalizar("el cap. XII"))
    prueba("«el siglo XIX» si",
           "siglo diecinueve" in normalizar("el siglo XIX"),
           normalizar("el siglo XIX"))
    prueba("«Felipe II» es ORDINAL, como se dice",
           "Felipe segundo" in normalizar("Felipe II"), normalizar("Felipe II"))
    prueba("«Juan XXIII» pasa de diez y vuelve a cardinal",
           "Juan veintitrés" in normalizar("Juan XXIII"),
           normalizar("Juan XXIII"))
    # Lo importante es lo que NO se toca.
    prueba("«MIX poemas» se queda: podria ser una palabra",
           "MIX" in normalizar("escribio MIX poemas"),
           normalizar("escribio MIX poemas"))
    prueba("una letra suelta no se toca NUNCA: puede ser una inicial",
           "V. Quirarte" in normalizar("V. Quirarte escribio"),
           normalizar("V. Quirarte escribio"))
    prueba("ni «C» ni «D» sueltas en mitad de una frase",
           normalizar("la nota C y la D") == "la nota C y la D",
           normalizar("la nota C y la D"))

    print("\nAbreviaturas:")
    for entra, dentro in (("el Dr. Perez", "Doctor"),
                          ("etc., y mas", "etcétera"),
                          ("la pag. 47", "página"),
                          ("Av. Bolivar", "Avenida"),
                          ("el sr. gomez", "señor")):
        prueba(f"{entra} -> {dentro}", dentro in normalizar(entra),
               normalizar(entra))
    prueba("se respeta la mayuscula", normalizar("Sr. X").startswith("Señor"),
           normalizar("Sr. X"))

    print("\nLA UNA SOLA LETRA, que es el caso delicado:")
    # «D.» es «don» en un libro espanol y una inicial en un nombre ingles. Lo
    # que las separa es si detras viene OTRA inicial.
    prueba("«D. Quijote» es don",
           normalizar("D. Quijote") == "Don Quijote", normalizar("D. Quijote"))
    prueba("«D. H. Lawrence» NO es don",
           normalizar("D. H. Lawrence") == "D. H. Lawrence",
           normalizar("D. H. Lawrence"))

    print("\nCifras en contexto:")
    for entra, sale in (
        ("En 1605", "En mil seiscientos cinco"),
        ("el 80%", "el ochenta por ciento"),
        ("3,14", "tres coma catorce"),
        ("1.500 pesos", "mil quinientos pesos"),
        ("paginas 20-25", "paginas veinte a veinticinco"),
        ("la 1.ª edicion", "la primera edicion"),
        ("el 3.º dia", "el tercero dia"),
    ):
        prueba(f"{entra} -> {sale}", normalizar(entra) == sale,
               normalizar(entra))
    prueba("un numero larguisimo se deja: es un codigo, no una cantidad",
           "1234567890123456789" in normalizar("codigo 1234567890123456789"),
           normalizar("codigo 1234567890123456789"))

    print("\nEl orden en que se hacen las cosas, que no es el evidente:")
    # «pag.» tiene que volverse «pagina» ANTES de que el romano busque su
    # palabra de contexto, o «pag. XII» no se convertiria.
    prueba("«pag. XII» sale entero",
           normalizar("pag. XII") == "página doce", normalizar("pag. XII"))
    # Y «º» no puede estar en la lista de simbolos: esa corre antes y lo
    # borraria, dejando «3.» que acaba en «tres.».
    prueba("«3.º» no se queda en «tres.»",
           "tercero" in normalizar("el 3.º"), normalizar("el 3.º"))

    print("\nSe puede apagar por partes:")
    prueba("sin romanos", normalizar("cap. XII", con_romanos=False)
           == "capítulo XII", normalizar("cap. XII", con_romanos=False))
    prueba("sin numeros", "1605" in normalizar("En 1605", con_numeros=False))
    prueba("sin abreviaturas", "Dr." in normalizar("Dr. X",
                                                   con_abreviaturas=False))

    print("\nEL PUENTE entre lo escrito y lo dicho:")
    # Normalizar cambia la CUENTA de palabras, y el karaoke ilumina sobre lo
    # escrito. Sin coser las dos cuentas, el resaltado se corre en cuanto
    # aparece una cifra, y el error crece con cada una.
    for texto, esperado in (
            ("En 1605 vino", [1, 3, 1]),
            ("Nada que normalizar aqui", [1, 1, 1, 1]),
            ("el 80% de 1.500 pesos", [1, 3, 1, 2, 1]),
            ("Vino el Dr. Perez", [1, 1, 1, 1]),
    ):
        dicho, grupos = normalizar_mapeado(texto)
        prueba(f"«{texto[:28]}» -> {esperado}", grupos == esperado, grupos)

    print("  y las dos cuentas siempre cuadran:")
    for texto in ("En 1605 el cap. XII y el 80% de 2.000",
                  "Felipe II nacio el 3.º dia de 1527",
                  "paginas 20-25 del tomo XIV, 1.500 ejemplares",
                  "sin nada raro", "", "1605"):
        dicho, grupos = normalizar_mapeado(texto)
        prueba(f"«{texto[:30]}»",
               len(grupos) == len(texto.split()) and sum(grupos) == len(dicho.split()),
               f"{len(grupos)} grupos, suman {sum(grupos)}, "
               f"escritas {len(texto.split())}, dichas {len(dicho.split())}")

    print("  juntar los tiempos de vuelta:")
    class T:
        def __init__(s, a, b): s.inicio_ms, s.fin_ms = a, b
    tiempos = [T(0, 100), T(100, 250), T(250, 400), T(400, 500), T(500, 600)]
    juntos = juntar_tiempos(tiempos, [1, 3, 1])
    prueba("tres escritas de cinco dichas", len(juntos) == 3)
    prueba("la del medio abarca sus tres",
           juntos[1][0].inicio_ms == 100 and juntos[1][1].fin_ms == 500,
           f"{juntos[1][0].inicio_ms}-{juntos[1][1].fin_ms}")
    prueba("sin tiempos no revienta", juntar_tiempos([], [1, 2]) == [])

    print("\nNada de esto revienta con lo raro:")
    prueba("texto vacio", normalizar("") == "")
    prueba("solo simbolos", normalizar("%%%") != "")
    prueba("un punto suelto", normalizar(".") == ".")

    print("\n" + "=" * 54)
    print(f"{ok} OK · {fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
