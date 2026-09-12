"""Revision de calidad AL SUBIR el libro — un solo punto de entrada.

POR QUE AQUI Y NO DESPUES
-------------------------
El texto que se guarda en R2 es el que va a leer el TTS durante anos. Si sube
con las palabras partidas por guiones de maquina de escribir, o con "carirulo"
donde decia "capitulo", cada escucha arrastra el error. Corregirlo despues
obliga a borrar el audio ya generado (eso es `reparar_libros.py`, el remiendo).
Corregirlo al subir cuesta segundos y solo pasa una vez.

QUE HACE, EN ORDEN
------------------
  1. GUIONES  — une las palabras cortadas a final de linea usando el propio
                libro como diccionario. Sin red, instantaneo.
  2. DETECCION — los tres filtros de `calidad.py`: rara + a una letra de una
                frecuente + no es espanol. Sin red, decimas de segundo.
  3. IA       — solo sobre las candidatas que quedan (decenas, no miles), para
                elegir el destino correcto y cazar los errores sistematicos.
                Con red, y por eso con presupuesto de tiempo.
  4. MIXTO    — se aplican las sistematicas y las de confianza alta; el resto
                queda en el informe para que lo mire una persona.

EL PRESUPUESTO DE TIEMPO
------------------------
Cloud Run corta la peticion a los 300 s por defecto, y un PDF escaneado ya
gasta ~134 s solo en OCR. Por eso `revisar` recibe los segundos que le quedan
y, si no alcanzan, SE SALTA LA IA en vez de que la subida entera falle. Los
pasos 1 y 2 no se saltan nunca: no dependen de la red y tardan menos de un
segundo.
"""
from __future__ import annotations

import time

import calidad
import calidad_ia
import guiones

# Cuantas candidatas se le mandan a la IA como mucho. Cada lote son 15 y tarda
# unos segundos; mas alla de esto el rendimiento decae y el coste sube.
MAX_CANDIDATAS_IA = 60
# Segundos que hay que tener libres para siquiera empezar con la IA.
MINIMO_PARA_IA = 25.0

# El diccionario tarda ~0,7 s en cargarse y ocupa poco: se carga una vez por
# proceso y se reutiliza en todas las subidas.
_DIC: calidad.Diccionario | None = None


def diccionario() -> calidad.Diccionario:
    global _DIC
    if _DIC is None:
        _DIC = calidad.Diccionario()
        print(f"[Revision] diccionario: {_DIC.ruta or 'NO ENCONTRADO'}", flush=True)
    return _DIC


def arreglar_guiones(texto: str, es_valida=None) -> tuple[str, int]:
    """Une las palabras cortadas, venga el texto como venga.

    Hay dos formas del mismo mal y aqui llegan las dos:
      - con salto de linea, "inge-\nnioso", tal como sale de un TXT o un EPUB;
      - ya aplanado, "inge- nioso", cuando otra capa junto las lineas antes.
    `guiones.py` tiene una funcion para cada caso; esta las encadena para no
    tener que adivinar de donde viene el texto.
    """
    total = 0
    if "\n" in texto:
        lineas = texto.splitlines()
        vocab  = guiones.vocabulario([texto])
        unidas = guiones.unir_palabras_cortadas(lineas, vocab, es_valida)
        total += len(lineas) - len(unidas)      # cada union se come una linea
        texto  = "\n".join(unidas)
    vocab = guiones.vocabulario_de_textos([texto])
    texto, n = guiones.reparar_texto_plano(texto, vocab, es_valida)
    return texto, total + n


def _sin_ia(motivo: str, texto: str, n_guiones: int,
            cands: list, t0: float) -> tuple[str, dict]:
    return texto, _informe(texto, n_guiones, cands, [], None, motivo, t0)


def _informe(texto: str, n_guiones: int, cands: list, aplicadas: list,
             pendientes, motivo_ia: str, t0: float) -> dict:
    """Solo tipos simples: esto se guarda como JSON junto al libro."""
    return {
        "version": 1,
        "guiones_unidos": n_guiones,
        "candidatas": calidad.resumen(cands),
        "ia": {
            "ejecutada": motivo_ia == "",
            "motivo_omitida": motivo_ia,
            "aplicadas": [
                {"palabra": d.palabra, "correcta": d.correcta,
                 "destino": d.destino, "destino_correcto": d.destino_correcto,
                 "confianza": d.confianza, "sistematica": d.sistematica}
                for d in aplicadas
            ],
            "pendientes": [
                {"palabra": d.palabra, "propuesta": d.correcta,
                 "confianza": d.confianza, "motivo": d.motivo}
                for d in (pendientes or [])
            ],
        },
        "segundos": round(time.monotonic() - t0, 2),
    }


async def revisar(texto: str, *, presupuesto_s: float = 90.0,
                  con_ia: bool = True, api_key: str | None = None,
                  pedir=None, dic: calidad.Diccionario | None = None
                  ) -> tuple[str, dict]:
    """Devuelve (texto_corregido, informe). Nunca lanza: si algo falla,
    devuelve el texto tal cual y lo dice en el informe.

    `pedir` se inyecta en las pruebas para no depender de la red.
    """
    t0 = time.monotonic()

    # El diccionario primero: tambien mejora el arreglo de guiones (es lo que
    # impide pegar "septiembre- octubre").
    dic = dic or diccionario()
    ev = (lambda w: dic.existe(w) or dic.existe(w.lower())) if dic.disponible else None

    # 1. Guiones — siempre, es gratis.
    try:
        texto, n_guiones = arreglar_guiones(texto, ev)
    except Exception as e:
        print(f"[Revision] guiones fallo: {e}", flush=True)
        n_guiones = 0

    # 2. Deteccion — tambien gratis, pero necesita diccionario.
    if not dic.disponible:
        return _sin_ia("sin diccionario espanol", texto, n_guiones, [], t0)

    try:
        cands = calidad.detectar([texto], dic)
    except Exception as e:
        print(f"[Revision] deteccion fallo: {e}", flush=True)
        return _sin_ia(f"fallo la deteccion: {e}", texto, n_guiones, [], t0)

    if not cands:
        return _sin_ia("", texto, n_guiones, cands, t0)
    if not con_ia:
        return _sin_ia("desactivada", texto, n_guiones, cands, t0)

    restante = presupuesto_s - (time.monotonic() - t0)
    if restante < MINIMO_PARA_IA:
        return _sin_ia(f"sin tiempo ({restante:.0f}s de margen)",
                       texto, n_guiones, cands, t0)

    # 3. IA — solo las mas rentables, que ya vienen ordenadas por `detectar`.
    lote = cands[:MAX_CANDIDATAS_IA]
    try:
        frec = calidad.frecuencias([texto])
        decisiones = await calidad_ia.revisar(lote, dic, frec,
                                              api_key=api_key, pedir=pedir)
    except Exception as e:
        print(f"[Revision] IA fallo: {e}", flush=True)
        return _sin_ia(f"fallo la IA: {e}", texto, n_guiones, cands, t0)

    if not decisiones:
        return _sin_ia("la IA no devolvio nada", texto, n_guiones, cands, t0)

    # 4. Mixto.
    textos, res = calidad_ia.aplicar([texto], decisiones, solo_alta=True)
    texto = textos[0]
    inf = _informe(texto, n_guiones, cands, res["aplicadas"],
                   res["pendientes"], "", t0)
    inf["ia"]["ocurrencias_sustituidas"] = res["ocurrencias"]
    return texto, inf


def resumen_humano(inf: dict) -> str:
    """Una linea para el log de la subida."""
    c = inf.get("candidatas", {})
    ia = inf.get("ia", {})
    partes = [f"{inf.get('guiones_unidos', 0)} guiones unidos",
              f"{c.get('candidatas', 0)} sospechosas"]
    if ia.get("ejecutada"):
        partes.append(f"{len(ia.get('aplicadas', []))} corregidas "
                      f"({ia.get('ocurrencias_sustituidas', 0)} veces)")
        pend = len(ia.get("pendientes", []))
        if pend:
            partes.append(f"{pend} para revisar")
    else:
        partes.append(f"IA omitida: {ia.get('motivo_omitida') or 'nada que hacer'}")
    return " · ".join(partes) + f" · {inf.get('segundos', 0)}s"
