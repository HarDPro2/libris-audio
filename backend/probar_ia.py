#!/usr/bin/env python3
"""Prueba la cascada de modelos de OpenRouter, uno a uno, y dice que responde.

POR QUE
-------
En la primera subida con el motor completo, el informe dijo "la IA no devolvio
nada" y en los logs no habia ni una linea de error: `_pedir_openrouter` solo
registraba las EXCEPCIONES, y un 429 o un 402 no lo es. Este script hace una
llamada minima a cada modelo y ensena el codigo de estado y la respuesta.

    set OPENROUTER_API_KEY=...   (o $env:OPENROUTER_API_KEY en PowerShell)
    python probar_ia.py

No toca R2, ni Appwrite, ni ningun libro.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calidad_ia import MODELOS   # noqa: E402

PREGUNTA = ('Responde SOLO con este JSON, sin texto alrededor: '
            '[{"palabra":"carpirulo","correcta":"capitulo",'
            '"destino_correcto":"capitulo","confianza":"alta"}]')


def probar(modelo: str, clave: str):
    cuerpo = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": PREGUNTA}],
        "max_tokens": 120,
        "temperature": 0,
    }).encode()
    pet = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=cuerpo,
        headers={"Authorization": f"Bearer {clave}",
                 "HTTP-Referer": "https://libris-audio.vercel.app",
                 "X-Title": "Libris Audio - QuantumLabs",
                 "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(pet, timeout=60) as r:
            datos = json.load(r)
        tarda = time.time() - t0
        mensaje = (datos.get("choices") or [{}])[0].get("message", {})
        texto = mensaje.get("content") or ""
        if not texto.strip():
            # El caso de "openrouter/free": HTTP 200 y contenido vacio. Sin
            # esto parece que funciona y en realidad no sirve para nada.
            otros = [k for k, v in mensaje.items() if v] or list(datos)
            return False, tarda, f"HTTP 200 pero CONTENIDO VACIO (campos: {otros})"
        return True, tarda, " ".join(texto.split())[:120]
    except urllib.error.HTTPError as e:
        tarda = time.time() - t0
        detalle = e.read().decode("utf-8", "replace")[:200]
        try:
            detalle = json.loads(detalle).get("error", {}).get("message", detalle)
        except Exception:
            pass
        return False, tarda, f"HTTP {e.code}: {detalle}"
    except Exception as e:
        return False, time.time() - t0, f"{type(e).__name__}: {e}"


def main():
    clave = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not clave or clave in ("...", "…") or "<" in clave:
        sys.exit("Falta OPENROUTER_API_KEY (o tiene un valor de ejemplo).\\n"
                 "  Esta en las variables de Cloud Run, empieza por 'sk-or-v1-'.")
    if not clave.startswith("sk-or-"):
        print("  aviso: la clave no empieza por 'sk-or-'\\n")

    print(f"{len(MODELOS)} modelos en la cascada de calidad_ia.py\n")
    vivos = 0
    for modelo in MODELOS:
        ok, tarda, detalle = probar(modelo, clave)
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca}  {modelo:44} {tarda:5.1f}s  {detalle}")
        vivos += ok

    print(f"\n  {vivos} de {len(MODELOS)} responden con contenido util.")
    if not vivos:
        print("  Con ninguno vivo, la capa de IA no puede hacer nada y solo")
        print("  gasta tiempo en cada subida. Conviene apagarla:")
        print("    gcloud run services update libris-audio-backend "
              "--region us-west1 --update-env-vars REVISION_IA=0")


if __name__ == "__main__":
    main()
