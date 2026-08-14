"""Pruebas del OCR — META 2. Genera imágenes con texto real y las reconoce."""
import io, sys, zipfile
sys.path.insert(0, '.')
import fitz
from PIL import Image, ImageDraw, ImageFont
from extractores import extraer, ocr_disponible

ok = fallos = 0
def check(n, cond, extra=""):
    global ok, fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  ' + extra if extra else ''}")
    if cond: ok += 1
    else: fallos += 1

print("Tesseract disponible:", ocr_disponible(), "\n")

FRASE1 = "El inconsciente colectivo segun Jung"
FRASE2 = "La teoria del apego de Bowlby"

def pagina_img(texto, w=1240, h=1754):
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 46)
    except Exception:
        f = ImageFont.load_default()
    d.text((90, 200), texto, fill="black", font=f)
    d.text((90, 320), "Texto de prueba para reconocimiento optico.", fill="black", font=f)
    return img

# ── PDF escaneado (imágenes dentro de un PDF, sin capa de texto) ────────────
doc = fitz.open()
for frase in (FRASE1, FRASE2):
    b = io.BytesIO(); pagina_img(frase).save(b, "PNG")
    pg = doc.new_page(width=595, height=842)
    pg.insert_image(fitz.Rect(0, 0, 595, 842), stream=b.getvalue())
pdf = doc.tobytes(); doc.close()

print("PDF escaneado:")
d = extraer(pdf, "apuntes_escaneados.pdf")
check("ya NO pide OCR", not d.necesita_ocr)
check("reconoce la primera frase", "Jung" in d.texto, repr(d.texto[:70]))
check("reconoce la segunda", "Bowlby" in d.texto or "apego" in d.texto.lower())
check("deja aviso al usuario", bool(d.aviso), str(d.aviso))

# ── Foto de una página (JPG) ────────────────────────────────────────────────
print("\nFoto de una página (JPG):")
b = io.BytesIO(); pagina_img(FRASE2).save(b, "JPEG", quality=88)
d = extraer(b.getvalue(), "foto_pagina.jpg")
check("formato conservado", d.formato == "jpg", d.formato)
check("texto reconocido", "Bowlby" in d.texto or "apego" in d.texto.lower(), repr(d.texto[:70]))
check("no pide OCR", not d.necesita_ocr)

# ── PNG ─────────────────────────────────────────────────────────────────────
b = io.BytesIO(); pagina_img(FRASE1).save(b, "PNG")
d = extraer(b.getvalue(), "captura.png")
print("\nPNG:")
check("texto reconocido", "Jung" in d.texto, repr(d.texto[:60]))

# ── CBZ (cómic escaneado) ───────────────────────────────────────────────────
print("\nCBZ:")
cb = io.BytesIO()
with zipfile.ZipFile(cb, "w") as z:
    for i, frase in enumerate((FRASE1, FRASE2)):
        b = io.BytesIO(); pagina_img(frase, 900, 1300).save(b, "PNG")
        z.writestr(f"{i:03}.png", b.getvalue())
d = extraer(cb.getvalue(), "comic.cbz")
check("texto reconocido en el cómic", "Jung" in d.texto or "Bowlby" in d.texto, repr(d.texto[:60]))

# ── Imagen sin texto ────────────────────────────────────────────────────────
print("\nImagen sin texto:")
b = io.BytesIO(); Image.new("RGB", (800, 600), (180, 190, 200)).save(b, "PNG")
d = extraer(b.getvalue(), "paisaje.png")
check("sigue pidiendo OCR", d.necesita_ocr)
check("aviso útil al usuario", d.aviso and "nitida" in d.aviso.lower().replace("í","i"), str(d.aviso)[:60])

# ── El texto normal NO se toca ──────────────────────────────────────────────
print("\nDocumento con texto (no debe pasar por OCR):")
doc = fitz.open(); pg = doc.new_page()
pg.insert_text((72, 100), "Este documento si tiene capa de texto. " * 12, fontsize=11)
d = extraer(doc.tobytes(), "normal.pdf"); doc.close()
check("no pide OCR", not d.necesita_ocr)
check("sin aviso de OCR", d.aviso is None, str(d.aviso))

print(f"\n{'='*54}\n{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
