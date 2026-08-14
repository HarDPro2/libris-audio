"""Pruebas del normalizador con archivos reales generados al vuelo."""
import io, zipfile, sys
sys.path.insert(0, '.')
import fitz
from extractores import extraer, DocumentoProtegido, FormatoNoSoportado, SOPORTADOS

ok = fallos = 0
def check(nombre, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {nombre}{'  ' + extra if extra else ''}")
    if cond: ok += 1
    else: fallos += 1

print("Formatos admitidos:", ", ".join(SOPORTADOS), "\n")

# ── PDF con índice ──────────────────────────────────────────────────────────
d = fitz.open()
for i, t in enumerate(["Capitulo uno. " + "Texto de prueba. "*40,
                       "Capitulo dos. " + "Mas contenido aqui. "*40]):
    p = d.new_page(); p.insert_text((72, 100), t[:900], fontsize=11)
d.set_toc([[1, "Capitulo uno", 1], [1, "Capitulo dos", 2]])
pdf = d.tobytes(); d.close()
doc = extraer(pdf, "libro.pdf")
print("PDF con TOC:")
check("2 capitulos detectados", len(doc.capitulos) == 2, f"({len(doc.capitulos)})")
check("titulos del indice", [c.titulo for c in doc.capitulos] == ["Capitulo uno", "Capitulo dos"],
      str([c.titulo for c in doc.capitulos]))
check("no pide OCR", not doc.necesita_ocr)
check("indice con offsets", doc.indice[1]["offset"] > 0)

# ── PDF escaneado (paginas en blanco = sin capa de texto) ───────────────────
d = fitz.open(); [d.new_page() for _ in range(4)]
doc = extraer(d.tobytes(), "escaneado.pdf"); d.close()
print("\nPDF escaneado:")
check("marca necesita_ocr", doc.necesita_ocr)

# ── EPUB ────────────────────────────────────────────────────────────────────
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("mimetype", "application/epub+zip")
    z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="c.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    z.writestr("c.opf", '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="i"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="i">x</dc:identifier><dc:title>Prueba</dc:title><dc:language>es</dc:language></metadata><manifest><item id="a" href="a.xhtml" media-type="application/xhtml+xml"/><item id="b" href="b.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="a"/><itemref idref="b"/></spine></package>')
    z.writestr("a.xhtml", '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Primero</h1><p>' + "Contenido del primer capitulo. "*30 + '</p></body></html>')
    z.writestr("b.xhtml", '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Segundo</h1><p>' + "Contenido del segundo. "*30 + '</p></body></html>')
epub = buf.getvalue()
doc = extraer(epub, "novela.epub")
print("\nEPUB:")
check("texto extraido", len(doc.texto) > 200, f"{len(doc.texto)} car.")
check("titulo derivado del nombre", doc.titulo == "novela")
check("no pide OCR", not doc.necesita_ocr)

# ── EPUB con DRM ────────────────────────────────────────────────────────────
buf2 = io.BytesIO()
with zipfile.ZipFile(buf2, "w") as z:
    z.writestr("mimetype", "application/epub+zip")
    z.writestr("META-INF/encryption.xml", "<encryption/>")
print("\nEPUB con DRM:")
try:
    extraer(buf2.getvalue(), "protegido.epub"); check("rechazado", False)
except DocumentoProtegido as e:
    check("rechazado con mensaje claro", "protegido" in str(e).lower())

# ── KFX / AZW3 ──────────────────────────────────────────────────────────────
print("\nKindle:")
for n in ("libro.kfx", "libro.azw3"):
    try:
        extraer(b"basura"*100, n); check(n + " rechazado", False)
    except DocumentoProtegido:
        check(n + " rechazado por DRM", True)

# ── FB2, TXT, Markdown, HTML ────────────────────────────────────────────────
fb2 = ('<?xml version="1.0" encoding="utf-8"?><FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">'
       '<body><section><title><p>Uno</p></title><p>' + "Texto fb2 de prueba. "*30 + '</p></section></body></FictionBook>')
doc = extraer(fb2.encode(), "libro.fb2")
print("\nOtros formatos:")
check("FB2", len(doc.texto) > 200, f"{len(doc.texto)} car.")

doc = extraer(("Linea uno.\n42\npagina 7\nLinea dos.\n").encode(), "notas.txt")
check("TXT limpia numeros de pagina", "42" not in doc.texto and "pagina 7" not in doc.texto.lower(),
      repr(doc.texto[:60]))

md = "# Intro\nTexto inicial.\n## Capitulo A\nContenido A.\n## Capitulo B\nContenido B.\n"
doc = extraer(md.encode(), "apuntes.md")
check("Markdown detecta 3 secciones", len(doc.capitulos) == 3, str([c.titulo for c in doc.capitulos]))

html = "<html><head><style>p{}</style></head><body><h1>Titulo</h1><p>Parrafo uno.</p><h2>Sub</h2><p>Parrafo dos.</p></body></html>"
doc = extraer(html.encode(), "articulo.html")
check("HTML sin etiquetas", "<" not in doc.texto and "Parrafo uno" in doc.texto, repr(doc.texto[:60]))
check("HTML descarta <style>", "p{}" not in doc.texto)

# ── CBZ ─────────────────────────────────────────────────────────────────────
from PIL import Image
b = io.BytesIO(); Image.new("RGB", (400, 600), (220, 220, 220)).save(b, "PNG")
cb = io.BytesIO()
with zipfile.ZipFile(cb, "w") as z: z.writestr("001.png", b.getvalue())
doc = extraer(cb.getvalue(), "comic.cbz")
check("CBZ abre y pide OCR", doc.necesita_ocr)

# ── Errores ─────────────────────────────────────────────────────────────────
print("\nErrores:")
for datos, nombre, esperado in ((b"x", "archivo.xyz", "no soportado"),
                                (b"", "vacio.pdf", "vac"),
                                (b"x", "sinextension", "extensi")):
    try:
        extraer(datos, nombre); check(nombre, False)
    except FormatoNoSoportado as e:
        check(f"{nombre} -> {esperado}", esperado.lower() in str(e).lower(), str(e)[:50])

print(f"\n{'='*54}\n{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
