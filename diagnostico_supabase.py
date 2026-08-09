"""
diagnostico_supabase.py  —  SOLO LECTURA, no modifica nada.

Lee las credenciales de Supabase desde .env.local, consulta la tabla
global_books y lista todos los libros que quedaron en el respaldo.

Uso:
    cd "E:\\PROYECTO LIBRIS AUDIO\\libris-audio-main"
    python diagnostico_supabase.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env.local")


def load_env(path):
    """Lee un archivo .env sencillo y devuelve un dict."""
    env = {}
    if not os.path.exists(path):
        print(f"ERROR: no se encontró {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            env[key.strip()] = val
    return env


def main():
    env = load_env(ENV_PATH)
    url = env.get("VITE_SUPABASE_URL") or env.get("SUPABASE_URL")
    key = env.get("VITE_SUPABASE_ANON_KEY") or env.get("SUPABASE_ANON_KEY")

    if not url or not key:
        print("ERROR: faltan VITE_SUPABASE_URL o VITE_SUPABASE_ANON_KEY en .env.local")
        sys.exit(1)

    url = url.rstrip("/")
    print("=== Diagnóstico Supabase (solo lectura) ===")
    print(f"URL: {url}\n")

    # PostgREST: leer todos los registros de global_books
    endpoint = (
        f"{url}/rest/v1/global_books"
        "?select=book_id,title,author,category,parts_count,cover_url"
        "&order=title.asc"
    )
    req = urllib.request.Request(endpoint)
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"ERROR HTTP {e.code}: {body[:300]}")
        print("\nSi es 401/403, la tabla tiene RLS y la anon key no puede leer.")
        print("Si es 404, la tabla 'global_books' ya no existe en este proyecto.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR de red: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("Respuesta inesperada:", str(data)[:300])
        sys.exit(1)

    print(f"LIBROS ENCONTRADOS: {len(data)}\n")
    if not data:
        print("La tabla existe pero está VACÍA. No hay respaldo que recuperar aquí.")
        return

    # Contar por categoría
    por_cat = {}
    con_cover = 0
    total_partes = 0
    for b in data:
        cat = b.get("category") or "Sin categoría"
        por_cat[cat] = por_cat.get(cat, 0) + 1
        if b.get("cover_url"):
            con_cover += 1
        total_partes += int(b.get("parts_count") or 0)

    # Listado
    print(f"{'TÍTULO':<45} {'CATEGORÍA':<16} {'PARTES':>6}")
    print("-" * 70)
    for b in data:
        titulo = (b.get("title") or "(sin título)")[:44]
        cat = (b.get("category") or "-")[:15]
        partes = b.get("parts_count") or 0
        print(f"{titulo:<45} {cat:<16} {partes:>6}")

    print("\n=== RESUMEN ===")
    print(f"Total libros:      {len(data)}")
    print(f"Con portada:       {con_cover}")
    print(f"Total de partes:   {total_partes}")
    print("\nPor categoría:")
    for cat, n in sorted(por_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat:<20} {n}")

    # Guardar copia completa para el siguiente paso (migración a Appwrite)
    out_path = os.path.join(HERE, "respaldo_libros_supabase.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nCopia completa guardada en: {out_path}")
    print("(La usaremos para recrear el catálogo en Appwrite.)")


if __name__ == "__main__":
    main()
