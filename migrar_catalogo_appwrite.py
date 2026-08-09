"""
migrar_catalogo_appwrite.py
Recrea el catálogo de libros en Appwrite (colección global_books),
apuntando las portadas a Cloudflare R2. Los archivos de texto ya están en R2.

Lee la lista de libros desde 'respaldo_libros_supabase.json' (el JSON que
sacaste del SQL Editor de Supabase).

── ANTES DE CORRER, RELLENA ESTOS 2 VALORES ──────────────────────────
"""

import json
import os
import sys
import uuid
import urllib.request
import urllib.error

# Se leen desde variables de entorno (las pasas en el comando de PowerShell).
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY", "")
DATABASE_ID      = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")

# ──────────────────────────────────────────────────────────────────────
# No hace falta tocar nada debajo de esta línea.

APPWRITE_ENDPOINT = "https://nyc.cloud.appwrite.io/v1"
APPWRITE_PROJECT  = "6a72f5d6002eeff78bc2"
COLLECTION_ID     = "global_books"
R2_PUBLIC         = "https://pub-7ed2f9cce2d84ce5a6891e1e42008170.r2.dev"

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "respaldo_libros_supabase.json")


def crear_documento(book):
    """Crea un documento en Appwrite global_books para un libro."""
    book_id = book["book_id"]
    data = {
        "book_id":     book_id,
        "title":       book.get("title", "Sin título"),
        "category":    book.get("category", "General"),
        "added_by":    "biblioteca",
        "cover_url":   f"{R2_PUBLIC}/{book_id}/cover.png",
        "parts_count": int(book.get("parts_count") or 1),
    }
    payload = json.dumps({
        "documentId": uuid.uuid4().hex,
        "data": data,
    }).encode("utf-8")

    url = f"{APPWRITE_ENDPOINT}/databases/{DATABASE_ID}/collections/{COLLECTION_ID}/documents"
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Appwrite-Project", APPWRITE_PROJECT)
    req.add_header("X-Appwrite-Key", APPWRITE_API_KEY)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True, None
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}"
    except Exception as e:
        return False, str(e)


def main():
    if APPWRITE_API_KEY.startswith("PEGA_AQUI"):
        print("ERROR: Falta rellenar APPWRITE_API_KEY arriba en el script.")
        sys.exit(1)
    if not os.path.exists(JSON_PATH):
        print(f"ERROR: no se encontró {JSON_PATH}")
        print("Guarda el JSON de libros del SQL Editor en ese archivo.")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        libros = json.load(f)

    if not isinstance(libros, list) or not libros:
        print("ERROR: el JSON está vacío o no es una lista.")
        sys.exit(1)

    print(f"=== Importando {len(libros)} libros a Appwrite (base: {DATABASE_ID}) ===\n")

    ok, fallos = 0, []
    for i, book in enumerate(libros, 1):
        titulo = book.get("title", "?")[:40]
        exito, err = crear_documento(book)
        if exito:
            ok += 1
            print(f"  [{i:>3}/{len(libros)}] OK   {titulo}")
        else:
            fallos.append((titulo, err))
            print(f"  [{i:>3}/{len(libros)}] FALLO {titulo}  ->  {err}")
            # Si el PRIMER libro falla, casi seguro es la API key o el DATABASE_ID.
            if i == 1:
                print("\n  El primer libro falló. Revisa API key y DATABASE_ID antes de seguir.")
                print("  (Deteniendo para no llenar de errores.)")
                sys.exit(1)

    print(f"\n=== RESUMEN ===")
    print(f"Importados: {ok}/{len(libros)}")
    if fallos:
        print(f"Fallos: {len(fallos)}")
        for t, e in fallos[:10]:
            print(f"  - {t}: {e}")
    else:
        print("Todos los libros se importaron correctamente.")
    print("\nAbre la app (o recárgala) y deberían aparecer todos los libros.")


if __name__ == "__main__":
    main()
