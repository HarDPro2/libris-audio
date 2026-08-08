"""
crear_coleccion_user_state.py
Crea la colección 'user_state' en Appwrite (base libris_db) con los atributos
necesarios para sincronizar el progreso y las preferencias de cada usuario.

Ejecutar UNA sola vez:
    APPWRITE_API_KEY (tu key con scope databases.write) por variable de entorno.

    PowerShell:
        $env:APPWRITE_API_KEY="TU_API_KEY"
        python crear_coleccion_user_state.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

APPWRITE_ENDPOINT = "https://nyc.cloud.appwrite.io/v1"
APPWRITE_PROJECT  = "6a72f5d6002eeff78bc2"
DATABASE_ID       = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")
COLLECTION_ID     = "user_state"
API_KEY           = os.environ.get("APPWRITE_API_KEY", "")


def _req(method, path, payload=None):
    url = f"{APPWRITE_ENDPOINT}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Appwrite-Project", APPWRITE_PROJECT)
    req.add_header("X-Appwrite-Key", API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def main():
    if not API_KEY:
        print("ERROR: falta APPWRITE_API_KEY en el entorno.")
        sys.exit(1)

    print(f"=== Creando colección '{COLLECTION_ID}' en base '{DATABASE_ID}' ===\n")

    # 1. Crear colección
    code, body = _req("POST", f"/databases/{DATABASE_ID}/collections", {
        "collectionId": COLLECTION_ID,
        "name": "user_state",
        "permissions": [],
        "documentSecurity": False,
    })
    if code in (200, 201):
        print("  [OK] Colección creada.")
    elif code == 409:
        print("  [--] La colección ya existía (ok).")
    else:
        print(f"  [!] Colección: HTTP {code}: {body[:200]}")

    # 2. Atributo user_id (string, requerido)
    code, body = _req("POST", f"/databases/{DATABASE_ID}/collections/{COLLECTION_ID}/attributes/string", {
        "key": "user_id", "size": 64, "required": True,
    })
    print(f"  user_id: HTTP {code}" + ("" if code in (200, 201, 409) else f" -> {body[:150]}"))

    # 3. Atributo data (string grande, opcional) — guarda el JSON del estado
    code, body = _req("POST", f"/databases/{DATABASE_ID}/collections/{COLLECTION_ID}/attributes/string", {
        "key": "data", "size": 500000, "required": False,
    })
    print(f"  data:    HTTP {code}" + ("" if code in (200, 201, 409) else f" -> {body[:150]}"))

    print("\n  Esperando a que los atributos queden disponibles...")
    time.sleep(3)
    print("\nListo. La colección 'user_state' está preparada para la sincronización.")


if __name__ == "__main__":
    main()
