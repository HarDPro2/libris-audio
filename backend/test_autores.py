# -*- coding: utf-8 -*-
"""Separar el autor del titulo sin inventarse ninguno.

LO QUE SE VIGILA AQUI
---------------------
El fallo peligroso de este script no es equivocarse: es equivocarse con
CONFIANZA ALTA, porque esas filas salen con `aprobar=si` ya puesto y nadie
las mira. Las tres primeras versiones hicieron justo eso:

  1. «Sartre El existencialismo es un humanismo»  ->  «existencialismo...»
     Se comia el articulo inicial.
  2. «De la ira Seneca»                           ->  «la ira»
     Se comia el «De», que es parte del titulo en los clasicos.
  3. «Viktor Frankl Neurologo y psiquiatra  El hombre en busca de sentido»
     Dejaba la profesion dentro del titulo.

Las tres salian como «alta». Cada prueba de abajo marcada REGRESION es una de
esas, para que no vuelvan.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from autores import CATALOGO, limpiar, proponer   # noqa: E402

ok, fallos = 0, 0


def prueba(nombre, cond, extra=""):
    global ok, fallos
    if cond:
        ok += 1
        print(f"  OK    {nombre}")
    else:
        fallos += 1
        print(f"  FALLO {nombre} {extra}")


def igual(titulo, esperado_titulo, esperado_autor, esperada_confianza="alta"):
    t, a, c, _ = proponer(titulo)
    prueba(f"«{titulo[:46]}»",
           (t, a, c) == (esperado_titulo, esperado_autor, esperada_confianza),
           f"\n           salio  -> {t!r} / {a!r} / {c}"
           f"\n           esperaba -> {esperado_titulo!r} / {esperado_autor!r} / {esperada_confianza}")


def main() -> int:
    print("El autor al final:")
    igual("1984 George Orwell", "1984", "George Orwell")
    igual("Analectas Confucio", "Analectas", "Confucio")
    igual("Meditaciones Marco Aurelio", "Meditaciones", "Marco Aurelio")

    print("\nEl autor al principio:")
    igual("Albert Camus El Extranjero", "El Extranjero", "Albert Camus")
    igual("Juan Rulfo   Pedro Páramo", "Pedro Páramo", "Juan Rulfo")

    print("\nApellido primero, con coma y sin ella:")
    igual("Crimen y castigo Dostoyevski Fiodor", "Crimen y castigo", "Fiódor Dostoyevski")
    igual("El gato negro Allan Poe Edgar", "El gato negro", "Edgar Allan Poe")
    igual("Miyamoto, Musashi   El Libro De Los Cinco Anillos",
          "El Libro De Los Cinco Anillos", "Miyamoto Musashi")
    igual("Proust, Marcel   En busca del tiempo I",
          "En busca del tiempo I", "Marcel Proust")

    print("\nEntre parentesis:")
    igual("El dios en llamas (R. F. Kuang)", "El dios en llamas", "R. F. Kuang")

    print("\nCon erratas en el nombre —se reconocen, y se guarda el canonico:")
    igual("Aldous HGuxley Un mundo Feliz", "Un mundo Feliz", "Aldous Huxley")
    igual("charles bukowsky la senda del perdedor",
          "la senda del perdedor", "Charles Bukowski")
    igual("Una nueva tierra EckhartTolle", "Una nueva tierra", "Eckhart Tolle")

    print("\nNexos que sobran al sacar al autor de en medio:")
    igual("Ulises Por James Joyce", "Ulises", "James Joyce")
    igual("el principe de Nicolas Maquiavelo", "el principe", "Nicolás Maquiavelo")

    print("\nREGRESION — el articulo inicial es del titulo:")
    igual("Sartre El existencialismo es un humanismo",
          "El existencialismo es un humanismo", "Jean-Paul Sartre", "revisar")

    print("\nREGRESION — el «De» inicial tambien:")
    igual("De la ira Seneca", "De la ira", "Séneca")
    igual("De la brevedad de la vida Seneca", "De la brevedad de la vida", "Séneca")
    igual("De lo que vive el hombre Tolstoi Leon",
          "De lo que vive el hombre", "León Tolstói")

    print("\nREGRESION — lo que queda entre separadores no se da por bueno:")
    t, a, c, _ = proponer("Viktor Frankl Neurólogo y psiquiatra  El hombre en busca de sentido")
    prueba("la profesion por medio NO sale con confianza alta",
           c == "revisar", f"salio {c} con titulo {t!r}")

    print("\nLo que no se sabe, no se inventa:")
    t, a, c, _ = proponer("cadáver exquisito")
    prueba("sin autor conocido, el titulo no se toca", (t, a) == ("cadáver exquisito", ""))
    prueba("y se marca como «sin autor»", c == "sin autor", c)
    t, a, c, _ = proponer("Nuestro Hogar, Chico Xavier, Andre Luis")
    prueba("dos autores en un titulo piden revision", c == "revisar", c)

    print("\nNunca se inventan palabras:")
    malas = []
    for titulo in ["1984 George Orwell", "De la ira Seneca",
                   "Albert Camus El Extranjero", "Ulises Por James Joyce",
                   "Miyamoto, Musashi   El Libro De Los Cinco Anillos"]:
        t, _, _, _ = proponer(titulo)
        for palabra in t.split():
            if palabra not in titulo:
                malas.append((titulo, palabra))
    prueba("cada palabra del titulo propuesto estaba en el original",
           not malas, malas)

    print("\nEl catalogo esta sano:")
    vacios = [c for c, v in CATALOGO.items() if not v or any(not x.strip("!") for x in v)]
    prueba("ningun autor sin variantes", not vacios, vacios)
    prueba("limpiar() no deja comas sueltas",
           limpiar("Nuestro Hogar, , Andre Luis") == "Nuestro Hogar, Andre Luis",
           limpiar("Nuestro Hogar, , Andre Luis"))

    print("\nEl autor que declara el archivo (para que no vuelva a pasar):")
    _metadatos()

    print("\n" + "=" * 54)
    print(f"{ok} OK · {fallos} fallos")
    return 1 if fallos else 0


def _metadatos():
    """El filtro de `author` de los metadatos.

    Casi todos los PDF traen algo ahi y casi nada es un autor. Lo peligroso no
    es perderse uno bueno: es guardar «Administrador» o «Microsoft Word», que
    en la ficha no se distinguen de un nombre de verdad.
    """
    try:
        from extractores import autor_de_metadatos as autor
    except Exception as e:
        prueba("se puede importar extractores", False, f"{type(e).__name__}: {e}")
        return

    print("  Lo que SI se guarda:")
    for crudo, esperado in [
        ("Allan Kardec", "Allan Kardec"),
        ("  Allan  Kardec  ", "Allan Kardec"),       # espacios de sobra
        ("Garcia Marquez, Gabriel", "Garcia Marquez, Gabriel"),
        ("R. F. Kuang", "R. F. Kuang"),
        ("Émile Zola", "Émile Zola"),
    ]:
        prueba(f"«{crudo.strip()}»", autor(crudo) == esperado, f"-> {autor(crudo)!r}")

    print("  Lo que NO, porque no es un autor:")
    for crudo, porque in [
        ("", "vacio"),
        ("   ", "solo espacios"),
        ("unknown", "la palabra unknown"),
        ("Desconocido", "ya es el valor por defecto"),
        ("Administrador", "la cuenta de Windows de quien escaneo"),
        ("usuario", "igual"),
        ("Microsoft Word", "el programa que genero el archivo"),
        ("calibre", "el conversor"),
        ("ABBYY FineReader", "el OCR"),
        ("Created by Adobe Acrobat", "una firma de herramienta"),
        ("C:\\Users\\alber\\libro.pdf", "una ruta"),
        ("alguien@correo.com", "un correo"),
        ("http://ejemplo.com", "una url"),
        ("1234567890", "solo numeros"),
        ("A", "demasiado corto"),
        ("x" * 120, "demasiado largo"),
        ("!!! ???", "sin letras"),
    ]:
        prueba(f"«{crudo[:34]}» ({porque})", autor(crudo) == "", f"-> {autor(crudo)!r}")

    print("  Formato de catalogo —las fechas de vida sobran:")
    for crudo, esperado in [
        ("Hernández Gilabert, Miguel, 1910-1942", "Hernández Gilabert, Miguel"),
        ("Cervantes Saavedra, Miguel de, 1547-1616", "Cervantes Saavedra, Miguel de"),
        ("Kardec, Allan (1804-1869)", "Kardec, Allan"),
        ("Taylor, Laini, 1971-", "Taylor, Laini"),
        ("León, Luis de", "León, Luis de"),          # sin fechas, se deja igual
    ]:
        prueba(f"«{crudo}»", autor(crudo) == esperado, f"-> {autor(crudo)!r}")
    prueba("el apellido delante NO se invierte (seria adivinar)",
           autor("León, Luis de") == "León, Luis de")

    print("  Y el caso del EPUB mal generado:")
    prueba("el autor igual que el titulo no vale",
           autor("Cien años de soledad", titulo="Cien años de soledad") == "")
    prueba("pero el mismo nombre con otro titulo si",
           autor("Gabriel García Márquez", titulo="Cien años de soledad")
           == "Gabriel García Márquez")


if __name__ == "__main__":
    sys.exit(main())
