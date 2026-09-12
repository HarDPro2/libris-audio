"""Interruptores de comportamiento del backend.

Aparte y sin dependencias, para que se puedan leer y probar sin levantar el
backend entero.
"""
import os


def _activo(nombre: str, por_defecto: str = "1") -> bool:
    return os.environ.get(nombre, por_defecto).strip().lower() not in (
        "0", "false", "no", "off"
    )


# MODO COMUNIDAD — Libris Audio
# -----------------------------
# Libris es la version gratuita de uso personal: lo que sube uno lo ven todos,
# estilo biblioteca compartida entre amigos y familia. Encendido, cada libro
# nuevo entra al catalogo comun y el filtro de privacidad no se aplica al leer.
#
# El aislamiento por usuario NO se ha borrado: sigue entero detras de este
# interruptor. Apagarlo (MODO_COMUNIDAD=0) devuelve el comportamiento privado,
# que es el que necesita la version comercial (Quantum Text Codex), donde cada
# usuario solo ve los documentos que subio el.
MODO_COMUNIDAD = _activo("MODO_COMUNIDAD")

VISIBILIDAD_AL_SUBIR = "catalog" if MODO_COMUNIDAD else "private"


def visible_para(visibility: str | None, propietario: str | None,
                 solicitante: str | None) -> bool:
    """Si un libro del catalogo debe aparecer para quien pregunta."""
    if MODO_COMUNIDAD:
        return True
    return (visibility or "catalog") != "private" or propietario == solicitante
