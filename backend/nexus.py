"""Telemetría hacia Nexus Monitor — fuego y olvido.

QUÉ MIDE Y POR QUÉ
------------------
Nexus vigila los productos del ecosistema. Libris es el único gratuito, así
que aquí no hay ingresos que contar ni apenas coste de IA —el chat va con los
modelos libres de OpenRouter—, pero sí hay una pregunta abierta en el plan de
Codex que estos pulsos responden:

    ¿cuánto cuesta de verdad Cloud Run?

La respuesta no está en la factura de la IA, está en el **tiempo de CPU**, y
en Libris ese tiempo lo gasta casi todo una sola cosa: generar el MP3 de una
parte. Cada generación se mide y se manda con su duración. Con eso se sabe
cuántas se hacen al mes y cuánto duran, que es exactamente lo que multiplica
la factura.

LA REGLA
--------
Esto NUNCA puede tumbar ni frenar a Libris. Sin clave configurada no hace
nada; con clave, un fallo o un servidor caído se tragan en silencio. Un panel
de métricas que deja a alguien sin audiolibro no sirve para nada.
"""
from __future__ import annotations

import asyncio
import os
import time

import httpx

NEXUS_URL = (os.environ.get("NEXUS_MONITOR_URL") or "").rstrip("/")
CLAVE     = os.environ.get("NEXUS_PROJECT_KEY") or ""

# Un pulso no puede hacer esperar a nadie: si Nexus tarda, se abandona.
ESPERA_S = 3.0


def activo() -> bool:
    return bool(NEXUS_URL and CLAVE)


async def pulso(
    usuario: str,
    proveedor: str,
    modelo: str,
    operacion: str,
    entrada: int = 0,
    salida: int = 0,
    duracion_ms: int = 0,
    extra: dict | None = None,
) -> None:
    """Manda un pulso. No lanza nunca, pase lo que pase."""
    if not activo():
        return
    try:
        async with httpx.AsyncClient(timeout=ESPERA_S) as cliente:
            await cliente.post(
                f"{NEXUS_URL}/api/v1/telemetry/pulse",
                headers={"X-Project-Key": CLAVE},
                json={
                    "external_user_id": str(usuario or "anonimo"),
                    "provider":      proveedor,
                    "model":         modelo,
                    "operation":     operacion,
                    "input_tokens":  entrada,
                    "output_tokens": salida,
                    "duration_ms":   duracion_ms,
                    "metadata":      extra,
                },
            )
    except Exception:
        pass


def soltar(*args, **kwargs) -> None:
    """Lanza el pulso sin esperarlo, desde dentro de una ruta async.

    Se usa así para que la respuesta al oyente salga ya, sin quedarse a ver
    si Nexus contesta.
    """
    if not activo():
        return
    try:
        asyncio.get_running_loop().create_task(pulso(*args, **kwargs))
    except RuntimeError:
        pass


class Cronometro:
    """Mide un trozo de trabajo. `with Cronometro() as c: ...` y luego `c.ms`."""

    def __enter__(self) -> "Cronometro":
        self._desde = time.perf_counter()
        self.ms = 0
        return self

    def __exit__(self, *_exc) -> bool:
        self.ms = int((time.perf_counter() - self._desde) * 1000)
        return False
