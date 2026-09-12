#!/usr/bin/env python3
"""Cuentas de usuario de Appwrite: listar y poner contrasena nueva.

POR QUE EXISTE
--------------
Las contrasenas NO se pueden leer: Appwrite guarda un hash, y ni con la API
key del proyecto hay forma de recuperarlas. Lo unico posible es ponerlas de
nuevo, que es lo que hace esto.

    python cuentas.py --listar
    python cuentas.py --clave alberto.javier.gonzalez@gmail.com
    python cuentas.py --clave otro@correo.com --nueva "la-que-quieras"

Sin --nueva, genera una aleatoria y la imprime UNA vez. Apuntala en el acto:
no queda guardada en ningun sitio, ni aqui ni en Appwrite en claro.

Necesita APPWRITE_API_KEY.
"""
import argparse
import json
import os
import secrets
import string
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resetear_libros as reset                                  # noqa: E402

# Appwrite exige 8 caracteres como minimo; 16 es comodo de teclear una vez y
# suficiente para una cuenta familiar que se cambiara desde la app.
LARGO_CLAVE = 16
ALFABETO = string.ascii_letters + string.digits


def _pedir(ruta: str, cuerpo=None, metodo="GET"):
    url = f"{reset.AW_ENDPOINT}{ruta}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(url, data=datos, method=metodo, headers={
        "Content-Type": "application/json",
        "X-Appwrite-Project": reset.AW_PROJECT,
        "X-Appwrite-Key": reset.AW_KEY,
    })
    try:
        with urllib.request.urlopen(pet, timeout=30) as r:
            texto = r.read()
            return json.loads(texto) if texto else {}
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:300]
        try:
            detalle = json.loads(detalle).get("message", detalle)
        except Exception:
            pass
        raise SystemExit(f"Appwrite: HTTP {e.code}: {detalle}")


def usuarios():
    return _pedir("/users").get("users", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--clave", metavar="EMAIL",
                    help="pone una contrasena nueva a esa cuenta")
    ap.add_argument("--nueva", help="la contrasena; si falta, se genera")
    args = ap.parse_args()

    reset.comprobar_aw_key()
    lista = usuarios()

    if args.listar or not args.clave:
        print(f"{len(lista)} cuentas:")
        for u in lista:
            print(f"  {u['$id']}  {u.get('email') or '(sin email)':38} "
                  f"{u.get('name') or ''}")
        if not args.clave:
            print("\nPara poner una contrasena nueva:")
            print("  python cuentas.py --clave <email de la lista>")
        return

    elegidos = [u for u in lista
                if (u.get("email") or "").lower() == args.clave.lower()]
    if not elegidos:
        sys.exit(f"No hay ninguna cuenta con el email {args.clave}.")
    usuario = elegidos[0]

    nueva = args.nueva or "".join(secrets.choice(ALFABETO)
                                  for _ in range(LARGO_CLAVE))
    if len(nueva) < 8:
        sys.exit("Appwrite pide 8 caracteres como minimo.")

    _pedir(f"/users/{usuario['$id']}/password", {"password": nueva}, "PATCH")
    print(f"\n  cuenta : {usuario.get('email')}")
    print(f"  clave  : {nueva}")
    print("\n  Apuntala AHORA: no queda guardada en ningun sitio.")
    print("  Y cambiala desde la app cuando entres, si quieres una tuya.")


if __name__ == "__main__":
    main()
