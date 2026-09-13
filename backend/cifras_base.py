"""BLOQUE 0.7 — las cifras de HOY, para que el motor nuevo tenga contra que medirse.

POR QUE ESTE ARCHIVO VIVE AQUI Y NO EN QUANTUM TEXT CODEX
---------------------------------------------------------
El plan pedia un `ExtractorPyMuPDF` dentro del repositorio comercial, "lo de
hoy tras la interfaz", para comparar. Pero PyMuPDF es AGPL-3.0 y meterlo alli
—aunque sea solo de referencia— es justo lo que se decidio evitar naciendo
limpios en vez de haciendo fork.

La solucion es esta: se mide AQUI, en el repositorio Personal, donde PyMuPDF
ya vive y no molesta a nadie, y lo que cruza la frontera es un JSON. Numeros y
texto extraido son datos, no codigo: no arrastran licencia.

QUE MIDE
--------
Por cada libro del corpus:

    caracteres      cuanto texto saca el extractor de hoy
    palabras        idem, en palabras
    segundos        lo que tarda
    capitulos       en cuantas piezas lo parte
    necesita_ocr    si el PDF venia escaneado
    idioma          lo que detecto
    sha1_texto      huella del texto, para ver de un vistazo si cambio
    muestra         los primeros 400 caracteres, para comparar a ojo

Y guarda ADEMAS el texto entero de cada libro en una carpeta aparte, porque el
criterio de aceptacion del Bloque 2.2 —99% de caracteres coincidentes— no se
puede comprobar solo con un recuento: hay que comparar el texto de verdad.

USO
---
    cd backend
    python cifras_base.py --corpus "E:\\PROYECTO QUANTUM TEXT CODEX\\Quantum-Text-Codex\\Libros de pruebas"

Escribe `cifras_base.json` y la carpeta `cifras_base_textos/`. El JSON se copia
a `banco/` del repositorio comercial; los textos, solo si se van a comparar
(pesan lo que pesan los libros).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import time

import extractores

EXTENSIONES = {".pdf", ".epub", ".txt", ".md", ".html", ".htm", ".docx", ".fb2"}


def medir(ruta: pathlib.Path, guardar_en: pathlib.Path | None) -> dict:
    datos = ruta.read_bytes()
    t0 = time.monotonic()
    try:
        doc = extractores.extraer(datos, ruta.name)
    except extractores.DocumentoProtegido as e:
        return {"archivo": ruta.name, "error": f"DRM: {e}"}
    except extractores.FormatoNoSoportado as e:
        return {"archivo": ruta.name, "error": f"formato: {e}"}
    except Exception as e:
        return {"archivo": ruta.name, "error": f"{type(e).__name__}: {e}"}
    segundos = time.monotonic() - t0

    texto = doc.texto
    if guardar_en is not None:
        guardar_en.mkdir(parents=True, exist_ok=True)
        (guardar_en / (ruta.stem + ".txt")).write_text(texto, encoding="utf-8")

    return {
        "archivo": ruta.name,
        "bytes_origen": len(datos),
        "caracteres": len(texto),
        "palabras": len(texto.split()),
        "capitulos": len(doc.capitulos),
        "necesita_ocr": doc.necesita_ocr,
        "idioma": doc.idioma,
        "aviso": doc.aviso,
        "segundos": round(segundos, 3),
        "sha1_texto": hashlib.sha1(texto.encode("utf-8")).hexdigest(),
        "muestra": " ".join(texto[:400].split()),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True,
                   help="Carpeta con los libros (se recorre entera).")
    p.add_argument("--salida", default="cifras_base.json")
    p.add_argument("--textos", default="cifras_base_textos",
                   help="Carpeta donde dejar el texto extraido de cada libro.")
    p.add_argument("--sin-textos", action="store_true",
                   help="Solo las cifras, sin guardar el texto.")
    a = p.parse_args()

    raiz = pathlib.Path(a.corpus)
    if not raiz.is_dir():
        print(f"No existe la carpeta: {raiz}")
        return 1

    libros = sorted(x for x in raiz.rglob("*")
                    if x.is_file() and x.suffix.lower() in EXTENSIONES)
    if not libros:
        print(f"No hay libros en {raiz}")
        return 1

    destino_textos = None if a.sin_textos else pathlib.Path(a.textos)
    print(f"Motor de hoy: PyMuPDF {getattr(extractores.fitz, '__doc__', '')}".strip())
    print(f"{len(libros)} libros en {raiz}\n")

    filas = []
    for ruta in libros:
        fila = medir(ruta, destino_textos)
        filas.append(fila)
        if "error" in fila:
            print(f"  !! {fila['archivo'][:60]:60s} {fila['error']}")
        else:
            print(f"  {fila['archivo'][:60]:60s} "
                  f"{fila['caracteres']:>9,} car  "
                  f"{fila['segundos']:>6.2f}s  "
                  f"{fila['capitulos']:>3} cap"
                  + ("  OCR" if fila["necesita_ocr"] else ""))

    buenos = [f for f in filas if "error" not in f]
    informe = {
        "version": 1,
        "generado": time.strftime("%Y-%m-%d"),
        "motor": "pymupdf",
        "extractor": "backend/extractores.py del repositorio Personal",
        "corpus": str(raiz),
        "libros": len(filas),
        "con_texto": len(buenos),
        "caracteres_totales": sum(f["caracteres"] for f in buenos),
        "segundos_totales": round(sum(f["segundos"] for f in buenos), 2),
        "detalle": filas,
    }
    pathlib.Path(a.salida).write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"{len(buenos)} libros con texto · "
          f"{informe['caracteres_totales']:,} caracteres · "
          f"{informe['segundos_totales']}s en total")
    print(f"Cifras en {a.salida}")
    if destino_textos is not None:
        print(f"Textos en {destino_textos}/  "
              f"(copialos al repositorio comercial solo si vas a comparar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
