"""Interruptores de comportamiento del backend.

Aparte y sin dependencias, para que se puedan leer y probar sin levantar el
backend entero.
"""
import os


class FaltaVariable(RuntimeError):
    """Una variable sin la que NO se puede seguir."""


def obligatoria(nombre: str, para: str = "") -> str:
    """El valor de la variable, o se para aqui diciendo cual falta.

    POR QUE NO HAY VALOR POR DEFECTO. El 5 de octubre de 2026 se descubrio un
    backend de Libris corriendo en Render que nadie recordaba. No tenia NINGUNA
    variable de Appwrite configurada y aun asi servia 126 libros con sus ids
    reales: los valores por defecto del codigo —el id del proyecto y
    `libris_db`— le bastaron para conectarse a una base de verdad.

    El mismo defecto vive en `resetear_libros.py`, que borra. Un script
    destructivo con destino por defecto es un script que, sin configurar,
    parece configurado.

    Un defecto que FUNCIONA es peor que uno que falla, porque no se nota. Aqui
    se prefiere que el proceso se niegue a arrancar: en Cloud Run las variables
    estan puestas, asi que esto solo lo ve un despliegue mal configurado — que
    es justo quien tiene que enterarse.
    """
    valor = (os.environ.get(nombre) or "").strip()
    if not valor:
        raise FaltaVariable(
            f"Falta la variable de entorno {nombre}"
            + (f" ({para})" if para else "")
            + ". No hay valor por defecto a proposito: sin ella no se sabe "
              "contra que base se estaria trabajando.")
    return valor


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
