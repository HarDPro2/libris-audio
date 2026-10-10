#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vigilante de los servicios del ecosistema.

POR QUE VIVE EN GITHUB Y NO EN GOOGLE CLOUD
-------------------------------------------
El 09-10-2026 se desactivo la facturacion del proyecto y cayeron SEIS
servicios a la vez durante dos dias. Nexus Monitor no aviso por dos razones
que son la misma: no vigilaba esto, y estaba caido tambien, porque vive en el
mismo proyecto que vigila.

Un vigilante dentro de lo que vigila se calla justo cuando hace falta que
grite. Este corre en GitHub Actions: otra empresa, otra factura, otra cuenta.
Si Google entero se apaga, esto sigue despierto y lo dice.

QUE DETECTA, Y POR QUE ESTAS REGLAS
-----------------------------------
No basta con mirar el codigo HTTP. Lo aprendimos ese dia:

  * Un 503 que llega en 0,2 s con HTML de Google NO es tu aplicacion
    fallando: es que la peticion no entra al contenedor. Facturacion,
    despliegue roto o cuota. El cuerpo lo delata, no el codigo.
  * Un 200 puede estar mintiendo. `/api/books` INVENTA dos libros —La Odisea
    y Don Quijote, con `added_by: Libris`— cuando Appwrite no contesta. La
    app recibe 200 y una biblioteca falsa. Eso se busca a proposito.
  * Un arranque en frio tarda 10-30 s y es normal. Lento no es caido.

Sin dependencias: solo la libreria estandar.

    python vigilancia/comprobar.py          # comprueba y sale 1 si algo falla
    python vigilancia/comprobar.py --json   # ademas, el detalle en JSON
"""
import json
import sys
import time
import urllib.error
import urllib.request

ESPERA_S = 90          # un arranque en frio puede tardar; no hay prisa
LENTO_S = 35           # por encima de esto, se avisa sin declararlo caido

# Los servicios del proyecto 856706599879 («My First Project»).
#
# `libris-backend` NO esta aqui: en Cloud Run figura como «Necesita
# autenticacion», asi que sin credenciales siempre daria 403 y el vigilante
# gritaria todos los dias por algo que esta bien. Ademas es el viejo que
# queda por borrar.
SERVICIOS = [
    {
        "nombre": "libris-audio-backend",
        "producto": "Libris Audio",
        "url": "https://libris-audio-backend-856706599879.us-west1.run.app/api/health",
        "catalogo": "https://libris-audio-backend-856706599879.us-west1.run.app/api/books",
    },
    {
        "nombre": "nexus-monitor-engine",
        "producto": "Nexus Monitor",
        "url": "https://nexus-monitor-engine-856706599879.us-west1.run.app/",
    },
    {
        "nombre": "quantum-opto-ai",
        "producto": "Opto AI",
        "url": "https://quantum-opto-ai-856706599879.us-west1.run.app/",
    },
    {
        "nombre": "quantum-vault-licensing",
        "producto": "Quantum Vault · licencias",
        "url": "https://quantum-vault-licensing-856706599879.us-central1.run.app/",
    },
    {
        "nombre": "scribe-backend-v1",
        "producto": "Scribe Judicial",
        "url": "https://scribe-backend-v1-856706599879.us-west1.run.app/",
    },
]

BIEN, LENTO, DEGRADADO, CAIDO, PLATAFORMA = \
    "BIEN", "LENTO", "DEGRADADO", "CAIDO", "PLATAFORMA"

# Lo que aparece en las paginas de error de la propia Google, no en las tuyas.
_SENALES_GOOGLE = (
    "the service you requested is not available yet",
    "the server encountered an error and could not complete your request",
    "<title>500 server error",
    "<title>503 server error",
    "error: server error",
)
# Los dos libros que /api/books se inventa cuando Appwrite no contesta.
_SENALES_INVENTADO = ('"added_by":"libris"', '"added_by": "libris"')


def clasificar(estado, cuerpo, segundos, es_catalogo=False):
    """(situacion, explicacion). Funcion pura: se puede probar sin red."""
    texto = (cuerpo or "")
    bajo = texto.lower()

    if estado == 0:
        return CAIDO, f"no contesta ({texto[:90] or 'sin respuesta'})"

    if estado >= 500:
        if any(s in bajo for s in _SENALES_GOOGLE):
            return PLATAFORMA, (
                f"HTTP {estado} con pagina de error de Google en {segundos:.1f}s: "
                "la peticion no llega al contenedor. Facturacion, despliegue o cuota")
        return CAIDO, f"HTTP {estado}: la aplicacion contesta, pero con error"

    if estado in (401, 403):
        return CAIDO, f"HTTP {estado}: no deja entrar (¿cambio de permisos?)"

    if estado >= 400 and estado != 404:
        return CAIDO, f"HTTP {estado}"

    # 404 de la propia aplicacion significa que esta viva: contesta ella.
    if es_catalogo and any(s in bajo.replace(" ", "") for s in
                           (x.replace(" ", "") for x in _SENALES_INVENTADO)):
        return DEGRADADO, (
            "HTTP 200 pero el catalogo trae los libros INVENTADOS: Appwrite no "
            "contesta y el backend esta rellenando. La app ve una biblioteca falsa")

    if segundos > LENTO_S:
        return LENTO, f"HTTP {estado}, pero tardo {segundos:.0f}s"

    return BIEN, f"HTTP {estado} en {segundos:.1f}s"


def pedir(url, espera=ESPERA_S):
    """(estado, cuerpo, segundos). Nunca lanza: un fallo de red es un dato."""
    arranque = time.time()
    req = urllib.request.Request(url, headers={
        "User-Agent": "QuantumLabs-Vigilancia/1.0",
        "Accept": "application/json, text/html",
    })
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            return r.status, r.read(60000).decode("utf-8", "replace"), time.time() - arranque
    except urllib.error.HTTPError as e:
        return e.code, e.read(60000).decode("utf-8", "replace"), time.time() - arranque
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", time.time() - arranque


def revisar(servicios=None, pedir_fn=pedir):
    servicios = servicios if servicios is not None else SERVICIOS
    informe = []
    for s in servicios:
        estado, cuerpo, seg = pedir_fn(s["url"])
        situacion, porque = clasificar(estado, cuerpo, seg)
        fila = {"nombre": s["nombre"], "producto": s["producto"],
                "url": s["url"], "situacion": situacion, "porque": porque,
                "http": estado, "segundos": round(seg, 2)}
        # Al servicio que tiene catalogo se le mira tambien el contenido: un
        # 200 con libros inventados es el fallo que no da error.
        if s.get("catalogo") and situacion == BIEN:
            e2, c2, s2 = pedir_fn(s["catalogo"])
            sit2, por2 = clasificar(e2, c2, s2, es_catalogo=True)
            if sit2 != BIEN:
                fila.update({"situacion": sit2, "porque": por2})
        informe.append(fila)
    return informe


def diagnostico(informe):
    """Una linea con la conclusion. Hoy nos habria ahorrado media hora."""
    malos = [f for f in informe if f["situacion"] in (CAIDO, PLATAFORMA)]
    if not malos:
        return ""
    if len(malos) == len(informe) and all(f["situacion"] == PLATAFORMA for f in malos):
        return ("TODOS caidos a la vez y con error de plataforma. "
                "Mira la FACTURACION del proyecto antes que el codigo: "
                "gcloud billing accounts list  (columna OPEN)")
    if len(malos) == len(informe):
        return ("TODOS caidos a la vez. Eso no es un fallo de un servicio: "
                "mira facturacion, cuota o la region.")
    return f"{len(malos)} de {len(informe)} caidos."


def main():
    informe = revisar()
    ancho = max(len(f["nombre"]) for f in informe)
    print("Vigilancia de Quantum Labs — %s\n" % time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
    for f in informe:
        marca = {BIEN: "  ok  ", LENTO: " lento", DEGRADADO: " RARO ",
                 CAIDO: " CAIDO", PLATAFORMA: " CAIDO"}[f["situacion"]]
        print(f"[{marca}] {f['nombre']:<{ancho}}  {f['producto']}")
        if f["situacion"] != BIEN:
            print(f"           {f['porque']}")

    conclusion = diagnostico(informe)
    if conclusion:
        print("\n>>> " + conclusion)
    if "--json" in sys.argv:
        print("\n" + json.dumps(informe, ensure_ascii=False, indent=1))

    hay_problema = any(f["situacion"] in (CAIDO, PLATAFORMA, DEGRADADO)
                       for f in informe)
    print("\n%s" % ("ALGO VA MAL" if hay_problema else "Todo en pie."))
    return 1 if hay_problema else 0


if __name__ == "__main__":
    raise SystemExit(main())
