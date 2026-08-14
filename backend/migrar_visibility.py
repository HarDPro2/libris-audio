#!/usr/bin/env python3
"""
Migración META 0 — visibilidad de libros (Appwrite).

Qué hace:
  1. Crea el atributo `visibility` en la colección global_books (si no existe).
  2. Clasifica los libros existentes: los que subió un usuario -> "private",
     el catálogo de dominio público -> "catalog".

SIMULA por defecto: lista lo que haría sin tocar nada.
Para aplicar de verdad hay que pasar --aplicar.

Solo usa la librería estándar de Python: no hay que instalar nada.

Uso (PowerShell):
    $env:APPWRITE_API_KEY="<tu api key de servidor>"
    python migrar_visibility.py            # simulación
    python migrar_visibility.py --aplicar  # aplica
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://nyc.cloud.appwrite.io/v1").rstrip("/")
PROJECT  = os.environ.get("APPWRITE_PROJECT_ID", "6a72f5d6002eeff78bc2")
API_KEY  = os.environ.get("APPWRITE_API_KEY", "")
DB_ID    = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")
COLL     = "global_books"

APLICAR = "--aplicar" in sys.argv

if not API_KEY:
    sys.exit("Falta APPWRITE_API_KEY en el entorno.")


def api(method: str, path: str, body=None, params=None):
    url = f"{ENDPOINT}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "X-Appwrite-Project": PROJECT,
        "X-Appwrite-Key": API_KEY,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {detalle[:300]}") from None


print(f"Proyecto {PROJECT} · base {DB_ID} · colección {COLL}\n")

# ── 1. Atributo visibility ───────────────────────────────────────────────────
try:
    api("POST", f"/databases/{DB_ID}/collections/{COLL}/attributes/string",
        {"key": "visibility", "size": 16, "required": False})
    print("[1] Atributo 'visibility' creado. Esperando a que Appwrite lo active...")
    time.sleep(6)
except RuntimeError as e:
    if "already exists" in str(e).lower() or "attribute_already_exists" in str(e).lower():
        print("[1] El atributo 'visibility' ya existía. Sigo.")
    else:
        sys.exit(f"[1] Error creando el atributo: {e}")

# ── 2. Leer todos los documentos ─────────────────────────────────────────────
docs, offset = [], 0
while True:
    params = [("queries[]", json.dumps({"method": "limit",  "values": [100]})),
              ("queries[]", json.dumps({"method": "offset", "values": [offset]}))]
    lote = api("GET", f"/databases/{DB_ID}/collections/{COLL}/documents",
               params=params).get("documents", [])
    docs.extend(lote)
    if len(lote) < 100:
        break
    offset += 100

print(f"[2] {len(docs)} documentos encontrados.\n")

# ── 3. Clasificar ────────────────────────────────────────────────────────────
# Un userId de Appwrite es una cadena alfanumérica de ~20 caracteres.
# Los valores de relleno son del catálogo antiguo, cuando added_by lo mandaba
# el cliente y por defecto valía "upload".
ID_USUARIO = re.compile(r"^[A-Za-z0-9]{16,36}$")
RELLENO    = {"", "upload", "admin", "system", "seed", "catalogo", "catalog",
              "libris", "biblioteca", "library"}

privados, catalogo = [], []
for d in docs:
    added = (d.get("added_by") or "").strip()
    if added.lower() not in RELLENO and ID_USUARIO.match(added):
        privados.append(d)
    else:
        catalogo.append(d)

print(f"    private : {len(privados)}")
print(f"    catalog : {len(catalogo)}\n")

# Verificación: qué valores de added_by hay realmente. Si aparece alguno que
# parezca un userId y esté cayendo en "catalog", la regla de clasificación se
# quedó corta y hay que ampliarla ANTES de aplicar.
from collections import Counter
conteo = Counter((d.get("added_by") or "(vacío)").strip() for d in docs)
print("    Valores distintos de added_by:")
for valor, n in conteo.most_common(30):
    marca = "  <-- parece un userId" if (
        valor.lower() not in RELLENO
        and valor != "(vacío)"
        and len(valor) >= 8
        and not valor.isspace()
    ) else ""
    print(f"      {n:>4} x  {valor!r}{marca}")
print()

if privados:
    print("    Estos DEJARÁN de verse en el catálogo público:")
    for d in privados:
        titulo = (d.get("title") or "(sin título)")[:52]
        print(f"      · {titulo:<54} added_by={d.get('added_by')}")
    print()

if not APLICAR:
    print("[SIMULACIÓN] No se cambió nada.")
    print("Revisa la lista de arriba. Si es correcta:")
    print("    python migrar_visibility.py --aplicar")
    sys.exit(0)

# ── 4. Aplicar ───────────────────────────────────────────────────────────────
cambiados, errores = 0, 0
for destino, grupo in (("private", privados), ("catalog", catalogo)):
    for d in grupo:
        if (d.get("visibility") or "") == destino:
            continue
        try:
            api("PATCH",
                f"/databases/{DB_ID}/collections/{COLL}/documents/{d['$id']}",
                {"data": {"visibility": destino}})
            cambiados += 1
        except RuntimeError as e:
            errores += 1
            print(f"    ! {(d.get('title') or '?')[:40]}: {e}")

print(f"\n[OK] {cambiados} documentos actualizados, {errores} errores.")
if errores == 0:
    print("Meta 0 lista en Appwrite. Ya puedes desplegar el backend.")
