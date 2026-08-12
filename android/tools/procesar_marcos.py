#!/usr/bin/env python3
"""
procesar_marcos.py — Pipeline reutilizable de MARCOS ILUSTRADOS (Libris Audio).

Convierte una imagen de referencia con CENTRO VERDE (chroma) y fondo plano
(blanco o negro) en un PNG listo para la app:
  1. Quita el verde chroma (centro + spill) -> transparente.
  2. Quita el fondo exterior (blanco o negro) por relleno desde los bordes.
  3. Recorta al contenido (bbox alfa) y limita el tamaño.
  4. Guarda frame_<genero>.png (PNG-32 con alfa).

Respeta el verde de la vegetación (hiedra/hojas) usando un umbral estricto:
solo el verde MUY saturado y brillante (chroma) se elimina.

Uso:
  python procesar_marcos.py ENTRADA.png SALIDA_frame_medieval.png
  python procesar_marcos.py --batch carpeta_entrada/ carpeta_salida/
    (en batch, el nombre de salida = nombre de entrada con prefijo frame_)

Requiere: pillow, numpy, scipy
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

MAX_W = 1600  # ancho máximo de salida (controla el peso del APK)

def process(in_path, out_path, max_w=MAX_W):
    im = Image.open(in_path).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    alpha = np.full((h, w), 255, np.uint8)

    # ── 1. Chroma verde (estricto: no toca hiedra/hojas) ────────────────
    greenness = g - np.maximum(r, b)
    chroma = (g > 200) & (b < 90) & (r < 150) & (greenness > 90)
    alpha[chroma] = 0

    # ── 2. Fondo exterior (blanco o negro) por componentes en el borde ──
    corners = np.array([a[2, 2], a[2, w-3], a[h-3, 2], a[h-3, w-3]])
    bg = np.median(corners, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    bg_mask = dist < 45
    lbl, n = ndimage.label(bg_mask)          # 4-conectividad
    border = set(np.unique(np.concatenate([
        lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]])))
    border.discard(0)
    exterior = np.isin(lbl, list(border))
    alpha[exterior] = 0

    # ── 3. Despill: reduce el tinte verde en píxeles semitransparentes ──
    spill = (greenness > 25) & (alpha > 0)
    g2 = g.copy()
    g2[spill] = np.minimum(g[spill], np.maximum(r[spill], b[spill]) + 15)
    rgb = np.dstack([r, g2, b]).astype(np.uint8)

    out = np.dstack([rgb, alpha]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")

    # ── 4. Recorte al contenido + límite de tamaño ─────────────────────
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    if img.width > max_w:
        nh = round(img.height * max_w / img.width)
        img = img.resize((max_w, nh), Image.LANCZOS)

    img.save(out_path, "PNG", optimize=True)
    op = 100.0 * (np.asarray(img)[..., 3] > 10).mean()
    print(f"  OK {os.path.basename(out_path)}  {img.width}x{img.height}  "
          f"opaco={op:.0f}%  {os.path.getsize(out_path)//1024}KB")

def main():
    args = sys.argv[1:]
    if args and args[0] == "--batch":
        indir, outdir = args[1], args[2]
        os.makedirs(outdir, exist_ok=True)
        for f in sorted(os.listdir(indir)):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                base = os.path.splitext(f)[0].lower()
                name = base if base.startswith("frame_") else "frame_" + base
                process(os.path.join(indir, f), os.path.join(outdir, name + ".png"))
    else:
        process(args[0], args[1])

if __name__ == "__main__":
    main()
