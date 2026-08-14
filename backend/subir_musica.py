#!/usr/bin/env python3
"""
Sube la música de fondo a Cloudflare R2 y regenera el catálogo de la app.

Recorre  MUSICA/<CATEGORIA>/*.mp3  , recomprime cada pista a un bitrate de
fondo, la sube a R2 bajo  music/<categoria>/<archivo>.mp3  y escribe el
BackgroundMusicCatalog.kt con las URLs reales.

SIMULA por defecto. Para hacerlo de verdad: --aplicar

Requisitos:
    pip install boto3
    ffmpeg en el PATH (ya lo tienes)

Uso (PowerShell, desde la raíz del proyecto):
    $env:R2_ACCESS_KEY_ID="..."
    $env:R2_SECRET_ACCESS_KEY="..."
    $env:R2_ENDPOINT_URL="https://<cuenta>.r2.cloudflarestorage.com"
    $env:R2_BUCKET_NAME="libris-audio"
    python backend/subir_musica.py
    python backend/subir_musica.py --aplicar
"""
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

# ── Configuración ───────────────────────────────────────────────────────────
ORIGEN = Path(os.environ.get("MUSICA_DIR", r"E:\PROYECTO LIBRIS AUDIO\MUSICA"))
DESTINO_KT = Path("android/app/src/main/java/com/librisaudio/app/data/model/"
                  "BackgroundMusicCatalog.kt")
R2_PUBLIC = os.environ.get(
    "R2_PUBLIC_URL", "https://pub-7ed2f9cce2d84ce5a6891e1e42008170.r2.dev")

# Bitrate de fondo. La música suena bajo la narración y a volumen 0.25:
# 64 kbps mono es transparente en ese contexto y ahorra ~60% de datos.
BITRATE = os.environ.get("MUSICA_BITRATE", "64k")

APLICAR = "--aplicar" in sys.argv

# Compositor por fragmento del nombre del archivo. Lo que no encaje queda como
# "Dominio público" y se puede corregir a mano en el .kt.
COMPOSITORES = [
    ("arabesque",          "Claude Debussy"),
    ("nocturne",           "Frédéric Chopin"),
    ("nocturnes",          "Frédéric Chopin"),
    ("moonlight",          "Ludwig van Beethoven"),
    ("piano sonata no. 14","Ludwig van Beethoven"),
    ("violin concerto",    "Ludwig van Beethoven"),
    ("partita",            "Johann Sebastian Bach"),
    ("bwv",                "Johann Sebastian Bach"),
    ("juegos prohibidos",  "Anónimo (atrib. Rubira)"),
    ("santa lucia",        "Teodoro Cottrau"),
]


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("♭", "b").replace("♯", "s").replace("#", "s")
    t = re.sub(r"[^\w\s-]", "", t.lower())
    t = re.sub(r"[\s_-]+", "_", t).strip("_")
    return t or "pista"


def compositor(nombre: str) -> str:
    bajo = nombre.lower()
    for clave, autor in COMPOSITORES:
        if clave in bajo:
            return autor
    return "Dominio público"


def titulo_bonito(nombre: str) -> str:
    t = nombre.rsplit(".", 1)[0]
    t = re.sub(r"^[A-Za-z .]+ - ", "", t)        # quita "Paul Pitman - "
    t = re.sub(r"\s*\[[^\]]*\]", "", t)          # quita "[Guitar arrangement]"
    return t.strip()


if not ORIGEN.exists():
    sys.exit(f"No encuentro la carpeta de música: {ORIGEN}\n"
             f"Ajusta MUSICA_DIR si está en otro sitio.")

pistas = []
for carpeta in sorted(p for p in ORIGEN.iterdir() if p.is_dir()):
    categoria = re.sub(r"^musica[\s_-]*", "", carpeta.name, flags=re.I).strip()
    cat_slug = slug(categoria)
    for mp3 in sorted(carpeta.glob("*.mp3")):
        pistas.append({
            "origen": mp3,
            "categoria": categoria.title(),
            "clave": f"music/{cat_slug}/{slug(mp3.stem)}.mp3",
            "titulo": titulo_bonito(mp3.name),
            "compositor": compositor(mp3.name),
            "mb": mp3.stat().st_size / 1024 / 1024,
        })

if not pistas:
    sys.exit("No hay .mp3 en las subcarpetas.")

print(f"{len(pistas)} pistas en {ORIGEN}\n")
total = sum(p["mb"] for p in pistas)
for p in pistas:
    print(f"  {p['mb']:6.1f} MB  {p['titulo'][:44]:<46} {p['compositor'][:24]:<26} -> {p['clave']}")
print(f"\n  Total actual: {total:.0f} MB · se recomprime a {BITRATE} mono")

if not APLICAR:
    print("\n[SIMULACIÓN] No se subió nada ni se tocó el catálogo.")
    print("Revisa los títulos y compositores de arriba. Si están bien:")
    print("    python backend/subir_musica.py --aplicar")
    sys.exit(0)

# ── Subida ──────────────────────────────────────────────────────────────────
try:
    import boto3
except ImportError:
    sys.exit("Falta boto3.  Instálalo con:  pip install boto3")

_REQUERIDAS = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")

faltan = [v for v in _REQUERIDAS if not os.environ.get(v)]
if faltan:
    sys.exit("Faltan variables de entorno: " + ", ".join(faltan))

# Detectar valores de ejemplo pegados tal cual desde la documentacion.
_ejemplo = [v for v in _REQUERIDAS
            if os.environ[v].strip() in ("...", "") or "<" in os.environ[v]]
if _ejemplo:
    sys.exit(
        "Estas variables tienen valores de ejemplo, no los reales: "
        + ", ".join(_ejemplo)
        + "\nSacalos de Cloud Run (son las mismas que ya usa el backend):\n"
        "    gcloud run services describe libris-backend --region us-central1 "
        "--format=\"value(spec.template.spec.containers[0].env)\""
    )

_ep = os.environ["R2_ENDPOINT_URL"].strip()
if not _ep.startswith("https://") or not _ep.endswith(".r2.cloudflarestorage.com"):
    sys.exit(
        "R2_ENDPOINT_URL no tiene la forma esperada.\n"
        "  Esperado: https://<id-de-cuenta>.r2.cloudflarestorage.com\n"
        f"  Recibido: {_ep}"
    )

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["R2_ENDPOINT_URL"],
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
)
bucket = os.environ.get("R2_BUCKET_NAME", "libris-audio")

import shutil
if not shutil.which("ffmpeg"):
    sys.exit(
        "No encuentro ffmpeg en el PATH.\n"
        "  Windows:  winget install Gyan.FFmpeg   (y reabre PowerShell)\n"
        "  Comprueba con:  ffmpeg -version"
    )

tmp = Path(tempfile.mkdtemp(prefix="musica_"))
subido = 0
for p in pistas:
    salida = tmp / Path(p["clave"]).name
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(p["origen"]),
         "-ac", "1", "-b:a", BITRATE, "-map_metadata", "-1", str(salida)],
        capture_output=True)
    if r.returncode != 0 or not salida.exists():
        print(f"  ! ffmpeg falló en {p['titulo']}")
        continue
    nuevo_mb = salida.stat().st_size / 1024 / 1024
    with open(salida, "rb") as f:
        s3.put_object(Bucket=bucket, Key=p["clave"], Body=f.read(),
                      ContentType="audio/mpeg")
    print(f"  OK  {p['mb']:6.1f} -> {nuevo_mb:5.1f} MB   {p['clave']}")
    p["mb_final"] = nuevo_mb
    p["ok"] = True
    subido += 1
    salida.unlink(missing_ok=True)

print(f"\n{subido}/{len(pistas)} pistas subidas. "
      f"{total:.0f} MB -> {sum(p.get('mb_final', 0) for p in pistas):.0f} MB")

# ── Catálogo Kotlin ─────────────────────────────────────────────────────────
subidas = [p for p in pistas if p.get("ok")]
if not subidas:
    sys.exit("No se subio ninguna pista; no toco el catalogo.")
if len(subidas) < len(pistas):
    print(f"  AVISO: {len(pistas) - len(subidas)} pista(s) fallaron y "
          "quedan fuera del catalogo.")

lineas = []
for i, p in enumerate(subidas, start=1):
    ruta = p["clave"][len("music/"):]
    lineas.append(
        f'        MusicTrack("m{i}", "{p["titulo"]}", "{p["compositor"]}", '
        f'"{p["categoria"]}", "$'
        f'{{R2}}/{ruta}"),')
lineas[-1] = lineas[-1].rstrip(",")

kt = '''package com.librisaudio.app.data.model

data class MusicTrack(
    val id: String,
    val title: String,
    val composer: String,
    val category: String,
    val streamUrl: String
)

object BackgroundMusicCatalog {
    // GENERADO por backend/subir_musica.py — no editar a mano salvo para
    // corregir títulos o compositores. Todas las pistas existen en R2.
    private const val R2 = "''' + R2_PUBLIC + '''/music"

    val tracks = listOf(
''' + "\n".join(lineas) + '''
    )

    val categorias: List<String> = tracks.map { it.category }.distinct()
}
'''
if DESTINO_KT.parent.exists():
    DESTINO_KT.write_text(kt, encoding="utf-8")
    print(f"Catálogo escrito: {DESTINO_KT}")
else:
    alt = Path("BackgroundMusicCatalog.kt")
    alt.write_text(kt, encoding="utf-8")
    print(f"No encontré {DESTINO_KT}; lo dejé en {alt.resolve()}")
