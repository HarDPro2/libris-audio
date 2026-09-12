"""catalogo.py con los datos REALES: 97 fichas y los 100 archivos de
E:\\PROYECTO LIBRIS AUDIO\\LIBROS.

Lo que hay que garantizar:
  1. Cada libro del catalogo encuentra su archivo.
  2. Los archivos que NO son libros del catalogo (extractos bancarios,
     apuntes, duplicados) quedan FUERA. Es la salvaguarda que impide subir
     documentos personales a una biblioteca compartida.
"""
import sys

from catalogo import emparejar

ARCHIVOS = [
 "1984 George Orwell.pdf", "Albert Camus El Extranjero.pdf",
 "Aldous HGuxley Un mundo Feliz.pdf", "Ana_Karenina-Tolstoi_Leon.pdf",
 "Analectas-Confucio.pdf", "Arte_del_buen_vivir-Arthur_Schopenhauer.pdf",
 "Asi_hablo_Zaratustra-Friedrich_Nietzsche.pdf", "B_HC (1).pdf", "B_HC.pdf",
 "B. f. Skinner - Walden Dos.pdf", "B5A-2618-00.pdf", "cadáver exquisito.pdf",
 "Carl Jung El hombre y sus símbolos.pdf", "cartero Charles Bukowski.pdf",
 "charles-bukowsky-la-senda-del-perdedor.pdf",
 "Cien años de soledad Gabriel Garcia Marquez.pdf",
 "cien-aos-de-soledad-realidad-total-novela-total-0.pdf", "Clase.pdf",
 "Confianza_en_uno_mismo-Ralph_Waldo_Emerson.pdf",
 "Consideraciones_intempestivas-Friedrich_Nietzsche.pdf",
 "Crimen_y_castigo-Dostoyevski_Fiodor.pdf",
 "Critica_de_la_razon_pura-Immanuel_Kant.pdf",
 "Daniel Kahneman Pensar rápido, pensar despacio.pdf",
 "De_la_brevedad_de_la_vida-Seneca.pdf",
 "De_la_constancia_del_sabio-Seneca.pdf", "De_la_felicidad-Seneca.pdf",
 "De_la_ira-Seneca.pdf", "De_lo_que_vive_el_hombre-Tolstoi_Leon.pdf",
 "descubrimiento-de-la-realidad-en-el-aleph-de-jorge-luis-borges.pdf",
 "Discurso_del_metodo-Rene_Descartes.pdf",
 "Don_Quijote_de_la_Mancha-Cervantes_Miguel.pdf",
 "El_arte_de_la_guerra-Sun_Tzu.pdf",
 "El_arte_de_vivir_Manual_de_vida-Epicteto.pdf",
 "El_Blanco_y_el_Negro-Voltaire.pdf", "El_castillo-Kafka_Franz.pdf",
 "El_disco_de_la_muerte-Mark_Twain.pdf",
 "El_escarabajo_de_oro-Allan_Poe_Edgar.pdf",
 "El_forastero_misterioso-Mark_Twain.pdf",
 "El_gato_negro-Allan_Poe_Edgar.pdf", "El_gigante_egoista-Wilde_Oscar.pdf",
 "El_gran_Gatsby-Francis_Scott_Fitzgerald.pdf", "El_Kybalion-Anonimo.pdf",
 "El_libro_de_Enoc-Anonimo.pdf", "El_libro_de_Los_Mediums-Allan_Kardec.pdf",
 "el_principe de Nicolas Maquiavelo.pdf",
 "El_retrato_de_Dorian_Gray-Wilde_Oscar.pdf",
 "El_yo_y_el_ello-Sigmund_Freud.pdf", "Emily Bronté Cumbres Borrascosas.pdf",
 "Epicuro Carta a Meneceo.pdf",
 "Escritos de un viejo indecente  Charles Bukowski.pdf",
 "ESTADO DE CUENTA BANESCO ENERO.pdf", "ESTADO DE CUENTA BANESCO FEBRERO.pdf",
 "ESTADO DE CUENTA BANESCO MARZO.pdf", "ESTADO DE CUENTA BDV.pdf",
 "Etica_a_Nicomaco-Aristoteles.pdf", "Evangelio_de_Judas-Anonimo.pdf",
 "factotum Charles Bukowski.pdf", "Hamlet-Shakespeare_William.pdf",
 "Hija de Humo y Hueso - Laini Taylor.pdf",
 "Introduccion_del_narcisismo-Sigmund_Freud.pdf",
 "Isaac Asimov - La Última Pregunta.pdf",
 "Jean Piaget Seis estudios de psicología.pdf",
 "JORGE LUIS BORGES El Aleph.pdf", "Jorge_Luis_Borges_ficciones.pdf",
 "Juan Rulfo - Pedro Páramo.pdf", "La_divina_comedia-Dante_Alighieri.pdf",
 "La_Iliada-Homero.pdf", "La_interpretacion_de_los_suenos-Sigmund_Freud.pdf",
 "La_Odisea-Homero.pdf", "La_Republica-Platon.pdf",
 "León Tolstoi Guerra y Paz.pdf",
 "Los_crimenes_de_la_calle_Morgue-Allan_Poe_Edgar.pdf",
 "Los_hermanos_Karamazov-Dostoyevski_Fiodor.pdf",
 "Los_Miserables-Hugo_Victor.pdf",
 "Mas_alla_del_principio_del_placer-Sigmund_Freud.pdf", "Medea-Euripides.pdf",
 "Meditaciones-Marco-Aurelio.pdf",
 "Miyamoto, Musashi - El Libro De Los Cinco Anillos.pdf",
 "Noches_blancas-Dostoyevski_Fiodor.pdf", "Orgullo_y_prejuicio-Jane_Austen.pdf",
 "Pedro-Paramo.pdf", "Pensamientos-Jean-Jacques_Rousseau.pdf",
 "Proust, Marcel - En busca del tiempo I.pdf",
 "Psicologia_de_las_masas_y_analisis_del_yo-Sigmund_Freud.pdf",
 "Psicologia_de_las_masas-Gustave_Le_Bon.pdf",
 "Psicopatologia_de_la_vida_cotidiana-Sigmund_Freud.pdf",
 "Ray-Bradbury-Fahrenheit-451.pdf", "Rayuela julio Cortazar.pdf",
 "rayuela-poetica-y-practica-de-un-lector-libre.pdf",
 "Sartre-El_existencialismo_es_un_humanismo.pdf",
 "Segunda_parte_del_ingenioso_caballero_don_Quijote_de_la_Mancha-Cervantes_Miguel.pdf",
 "Sigmund Freud Introducción al psicoanálisis.pdf", "steven-pinker-la-tabla-rasa.pdf",
 "Totem_y_tabu-Sigmund_Freud.pdf", "Ulises Por James Joyce.pdf",
 "Vidas_de_filosofos_ilustres-Diogenes_Laercio.pdf",
 "Viktor Frankl Neurólogo y psiquiatra  El hombre en busca de sentido.pdf",
]

TITULOS = [
 "1984 George Orwell", "Albert Camus El Extranjero",
 "Aldous HGuxley Un mundo Feliz", "Ana Karenina Tolstoi Leon",
 "Analectas Confucio", "Arte del buen vivir Arthur Schopenhauer",
 "Asi hablo Zaratustra Friedrich Nietzsche", "B. f. Skinner   Walden Dos",
 "cadáver exquisito", "cartero Charles Bukowski",
 "charles bukowsky la senda del perdedor",
 "Cien años de soledad Gabriel Garcia Marquez",
 "Confianza en uno mismo Ralph Waldo Emerson",
 "Consideraciones intempestivas Friedrich Nietzsche",
 "Crimen y castigo Dostoyevski Fiodor", "Critica de la razon pura Immanuel Kant",
 "Daniel Kahneman Pensar rápido, pensar despacio",
 "De la brevedad de la vida Seneca", "De la constancia del sabio Seneca",
 "De la felicidad Seneca", "De la ira Seneca",
 "De lo que vive el hombre Tolstoi Leon", "Dias de sangre y resplandor   Laini Taylor",
 "Discurso del metodo Rene Descartes", "Don Quijote de la Mancha Cervantes Miguel",
 "El arte de la guerra Sun Tzu", "El arte de vivir Manual de vida Epicteto",
 "El Blanco y el Negro Voltaire", "El castillo Kafka Franz",
 "El dios en llamas (R. F. Kuang)", "El disco de la muerte Mark Twain",
 "El escarabajo de oro Allan Poe Edgar", "El forastero misterioso Mark Twain",
 "El gato negro Allan Poe Edgar", "El gigante egoista Wilde Oscar",
 "El gran Gatsby Francis Scott Fitzgerald", "El Kybalion Anonimo",
 "El libro de Enoc Anonimo", "El libro de los espiritus Allan Kardec",
 "El libro de Los Mediums Allan Kardec", "El Poder del Ahora Eckhart Tolle",
 "el principe de Nicolas Maquiavelo", "El retrato de Dorian Gray Wilde Oscar",
 "El yo y el ello Sigmund Freud", "Emily Bronté Cumbres Borrascosas",
 "Epicuro Carta a Meneceo", "Escritos de un viejo indecente  Charles Bukowski",
 "Etica a Nicomaco Aristoteles", "Evangelio de Judas Anonimo",
 "factotum Charles Bukowski", "HÁBITOS ATÓMICOS James Clear",
 "Hamlet Shakespeare William", "Hija de Humo y Hueso   Laini Taylor",
 "Introduccion del narcisismo Sigmund Freud", "Isaac Asimov   La Última Pregunta",
 "Jean Piaget Seis estudios de psicología", "JORGE LUIS BORGES El Aleph",
 "Jorge Luis Borges ficciones", "Juan Rulfo   Pedro Páramo",
 "La divina comedia Dante Alighieri", "LA GUERRA DE LA AMAPOLA R. F. Kuang",
 "La Iliada Homero", "La interpretacion de los suenos Sigmund Freud",
 "La Odisea Homero", "La república del dragón (R. F. Kuang)",
 "La Republica Platon", "Las leyes espirituales   Vicent Guillem.",
 "León Tolstoi Guerra y Paz", "Los crimenes de la calle Morgue Allan Poe Edgar",
 "Los Miserables Hugo Victor", "Mas alla del principio del placer Sigmund Freud",
 "Medea Euripides", "Meditaciones Marco Aurelio",
 "Miyamoto, Musashi   El Libro De Los Cinco Anillos",
 "Noches blancas Dostoyevski Fiodor", "Nuestro Hogar, Chico Xavier, Andre Luis",
 "Orgullo y prejuicio Jane Austen", "Pensamientos Jean Jacques Rousseau",
 "Penúltima tarde y otras tardes   Earle Herrera",
 "Proust, Marcel   En busca del tiempo I", "Psicologia de las masas Gustave Le Bon",
 "Psicologia de las masas y analisis del yo Sigmund Freud",
 "Psicopatologia de la vida cotidiana Sigmund Freud",
 "Ray Bradbury Fahrenheit 451", "Rayuela julio Cortazar",
 "Roger Zelazny   Los Nueve Principes de Ámbar",
 "Sartre El existencialismo es un humanismo",
 "Segunda parte del ingenioso caballero don Quijote de la Mancha Cervantes Miguel",
 "Sigmund Freud Introducción al psicoanálisis", "steven pinker la tabla rasa",
 "Sueños de dioses y monstruos   Laini Taylor", "Totem y tabu Sigmund Freud",
 "Ulises Por James Joyce", "Una nueva tierra EckhartTolle",
 "Vidas de filosofos ilustres Diogenes Laercio",
 "Viktor Frankl Neurólogo y psiquiatra  El hom",
 "Wilhelm Wundt Compendio de psicología",
]

# Archivos que NO deben emparejar con nada: no son libros del catalogo.
PROHIBIDOS = {
 "ESTADO DE CUENTA BANESCO ENERO.pdf", "ESTADO DE CUENTA BANESCO FEBRERO.pdf",
 "ESTADO DE CUENTA BANESCO MARZO.pdf", "ESTADO DE CUENTA BDV.pdf",
 "Clase.pdf", "B_HC.pdf", "B_HC (1).pdf", "B5A-2618-00.pdf",
 "Carl Jung El hombre y sus símbolos.pdf",      # no esta en el catalogo
 "Los_hermanos_Karamazov-Dostoyevski_Fiodor.pdf",
 "descubrimiento-de-la-realidad-en-el-aleph-de-jorge-luis-borges.pdf",
 "rayuela-poetica-y-practica-de-un-lector-libre.pdf",
 "cien-aos-de-soledad-realidad-total-novela-total-0.pdf",
}

fichas = [{"book_id": f"id{i:03d}", "title": t, "category": "General"}
          for i, t in enumerate(TITULOS)]

emparejados, sueltos, sin_archivo = emparejar(ARCHIVOS, fichas)

print(f"{len(ARCHIVOS)} archivos · {len(fichas)} fichas del catalogo\n")
print(f"  emparejados      : {len(emparejados)}")
print(f"  archivos sueltos : {len(sueltos)}")
print(f"  fichas sin archivo: {len(sin_archivo)}")

colados = sorted(PROHIBIDOS & set(emparejados))
print(f"\nDocumentos que NO son libros y se habrian subido: {len(colados)}")
for c in colados:
    print(f"   COLADO  {c}  ->  {emparejados[c]['title']!r}")

print("\nLos 4 libros danados encuentran su archivo:")
falla = 0
for archivo, titulo in [
    ("Ana_Karenina-Tolstoi_Leon.pdf", "Ana Karenina Tolstoi Leon"),
    ("Analectas-Confucio.pdf", "Analectas Confucio"),
    ("Arte_del_buen_vivir-Arthur_Schopenhauer.pdf", "Arte del buen vivir Arthur Schopenhauer"),
    ("Asi_hablo_Zaratustra-Friedrich_Nietzsche.pdf", "Asi hablo Zaratustra Friedrich Nietzsche"),
]:
    got = emparejados.get(archivo, {}).get("title")
    bien = got == titulo
    falla += not bien
    print(f"   {'OK   ' if bien else 'FALLO'} {archivo[:46]:46} -> {got!r}")

print("\nArchivos sueltos (hay que mirarlos a mano):")
for a in sorted(sueltos):
    print(f"   -  {a}")
print("\nFichas sin archivo en disco:")
for f in sorted(sin_archivo, key=lambda x: x["title"]):
    print(f"   -  {f['title']}")

sys.exit(1 if (colados or falla) else 0)
