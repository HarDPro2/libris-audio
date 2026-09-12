"""Capa de IA del motor de calidad.

La IA NO lee el libro ni lo reescribe. Solo decide sobre las palabras que los
filtros mecanicos de `calidad.py` ya marcaron — en la medicion real, 11 de 874
palabras distintas. El 99% del texto es intocable por construccion.

QUE APORTA LA IA QUE LO MECANICO NO PUEDE
-----------------------------------------
1. Elegir bien el destino. Lo mecanico propone "dias -> dios" porque "dios" es
   frecuente; la IA lee "Era de veinte dias como los demas" y responde "dias".

2. Errores SISTEMATICOS. "carirulo" sale 80 veces y es el mismo un error de
   OCR de "capitulo". Como es frecuente, la frecuencia jamas lo delata. La IA
   lo ve a la primera, y esa unica decision arregla las 80 ocurrencias.

LAS BARANDILLAS
---------------
- La IA responde JSON, nunca prosa. Si devuelve otra cosa, se descarta el lote.
- Solo se acepta una correccion a distancia <= MAX_DISTANCIA de la original.
- La correccion tiene que ser espanol valido, o aparecer ya en el libro
  (para nombres propios como "Motecuhzoma").
- Nunca se toca una palabra que no venga de `calidad.detectar()`.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from calidad import Candidata, Diccionario

MAX_DISTANCIA   = 3      # "carirulo" -> "capitulo" son 2; 3 da margen
LOTE            = 15     # candidatas por llamada
# Probado el 12-09-2026 con probar_ia.py: los cuatro modelos ":free" que habia
# aqui devuelven HTTP 404 — "This model is unavailable for free. The paid
# version is available now - use this slug instead: <slug>". Y "openrouter/free"
# responde 200 con contenido VACIO, que es lo que hacia que el informe dijera
# "la IA no devolvio nada" sin un solo error en los logs.
#
# Estos son los slugs que el propio error de OpenRouter recomienda. Son de
# pago, pero el gasto es ridiculo: unas 5.000 fichas por libro, asi que los 83
# de la biblioteca salen por centimos. Ordenados de mas barato y mas apto para
# espanol a mas caro.
# Medido con probar_ia.py el 12-09-2026:
#   meta-llama/llama-3.3-70b-instruct   3,9 s  y devuelve el JSON pedido
#   qwen/qwen-2.5-coder-32b-instruct   60,1 s  TIMEOUT
#   deepseek/deepseek-r1                0,7 s  HTTP 402, sin saldo
# Un modelo colgado dentro de la cascada se come el presupuesto de tiempo de
# la subida, asi que aqui solo entra lo que esta probado. Para anadir otro:
# pasarlo antes por probar_ia.py.
MODELOS = [
    "meta-llama/llama-3.3-70b-instruct",
]

INSTRUCCIONES = """Eres un corrector de errores de OCR en libros escaneados en español.

Te doy palabras sospechosas de un libro. De cada una sabes:
- la palabra tal como aparece y cuántas veces sale
- una palabra parecida que sale mucho en ese mismo libro
- una o dos frases donde aparece

Para cada una decide la forma CORRECTA en español.

REGLAS ESTRICTAS:
1. Responde SOLO un array JSON. Nada de explicaciones ni texto fuera del JSON.
2. La corrección debe parecerse mucho a la palabra original: es un error de
   escaneo, no una palabra distinta.
3. Si la palabra frecuente TAMBIÉN está mal escaneada, corrígela igualmente en
   "destino_correcto". Ejemplo: "carírulo" que sale 80 veces es "capítulo".
4. Si no estás seguro, pon confianza "baja". No inventes.
5. Respeta los nombres propios indígenas o históricos: si "Motecuhzoma" es el
   nombre correcto, no lo castellanices.

Formato de cada elemento:
{"palabra":"...", "correcta":"...", "destino_correcto":"...", "confianza":"alta|baja"}

- "correcta": la forma correcta de la palabra sospechosa
- "destino_correcto": la forma correcta de la palabra frecuente. Si ya está
  bien, repítela igual.
- "confianza": "alta" solo si no hay ninguna duda."""


@dataclass
class Decision:
    palabra:          str
    correcta:         str
    destino:          str
    destino_correcto: str
    confianza:        str
    aceptada:         bool
    motivo:           str = ""

    @property
    def sistematica(self) -> bool:
        return self.destino_correcto != self.destino


def _distancia(a: str, b: str) -> int:
    """Levenshtein sencilla; las palabras son cortas."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _prompt(cands: list[Candidata]) -> str:
    lineas = []
    for c in cands:
        ctx = c.contextos[0][:160] if c.contextos else "(sin contexto)"
        lineas.append(
            f'- palabra: "{c.palabra}" ({c.usos} veces)\n'
            f'  parecida frecuente: "{c.destino}" ({c.usos_destino} veces)\n'
            f'  contexto: «{ctx}»'
        )
    return "\n".join(lineas)


def _extraer_json(texto: str):
    """Los modelos pequenos envuelven el JSON en texto o en ```json."""
    texto = texto.strip()
    m = re.search(r"```(?:json)?\s*(.+?)```", texto, re.S)
    if m:
        texto = m.group(1).strip()
    i, j = texto.find("["), texto.rfind("]")
    if i == -1 or j == -1:
        return None
    try:
        return json.loads(texto[i:j + 1])
    except Exception:
        return None


def validar(cand: Candidata, cruda: dict, dic: Diccionario,
            frec: dict | None = None) -> Decision:
    """Aplica las barandillas a lo que respondio la IA."""
    correcta = str(cruda.get("correcta", "")).strip()
    destino_c = str(cruda.get("destino_correcto", cand.destino)).strip()
    conf = str(cruda.get("confianza", "baja")).strip().lower()
    conf = conf if conf in ("alta", "baja") else "baja"

    d = Decision(cand.palabra, correcta, cand.destino, destino_c, conf,
                 aceptada=False)

    if not correcta:
        d.motivo = "la IA no propuso correccion"
        return d
    if correcta.lower() == cand.palabra.lower():
        d.motivo = "la IA dice que ya esta bien"
        return d

    dist = _distancia(cand.palabra.lower(), correcta.lower())
    if dist > MAX_DISTANCIA:
        d.motivo = f"demasiado lejos de la original (distancia {dist})"
        return d

    # La correccion tiene que existir: en espanol, o en el propio libro
    en_libro = bool(frec and frec.get(correcta.lower(), 0) >= 2)
    if not dic.existe(correcta) and not en_libro:
        d.motivo = "la correccion no es espanol ni aparece en el libro"
        return d

    # Y si dice que el destino frecuente tambien esta mal, la misma vara
    if destino_c.lower() != cand.destino.lower():
        dd = _distancia(cand.destino.lower(), destino_c.lower())
        if dd > MAX_DISTANCIA or not dic.existe(destino_c):
            d.destino_correcto = cand.destino     # se ignora esa parte
            d.motivo = "correccion del destino descartada"

    d.aceptada = True
    return d


async def revisar(cands: list[Candidata], dic: Diccionario,
                  frec: dict | None = None, api_key: str | None = None,
                  pedir=None) -> list[Decision]:
    """Pasa las candidatas por la IA en lotes. `pedir` se inyecta en pruebas."""
    if not cands:
        return []
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if pedir is None:
        if not api_key:
            return []
        pedir = _pedir_openrouter(api_key)

    decisiones: list[Decision] = []
    for i in range(0, len(cands), LOTE):
        lote = cands[i:i + LOTE]
        bruto = await pedir(INSTRUCCIONES, _prompt(lote))
        datos = _extraer_json(bruto or "")
        if not isinstance(datos, list):
            print(f"[Calidad] lote {i // LOTE + 1}: la respuesta no traia JSON "
                  f"({(bruto or '')[:120]!r})", flush=True)
            continue                      # lote perdido, no se inventa nada
        por_palabra = {str(x.get("palabra", "")).lower(): x
                       for x in datos if isinstance(x, dict)}
        for c in lote:
            cruda = por_palabra.get(c.palabra.lower())
            if cruda:
                decisiones.append(validar(c, cruda, dic, frec))
    return decisiones


def _pedir_openrouter(api_key: str):
    async def _pedir(sistema: str, usuario: str) -> str | None:
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer":  "https://libris-audio.vercel.app",
            "X-Title":       "Libris Audio - QuantumLabs",
            "Content-Type":  "application/json",
        }
        cuerpo = {
            "messages": [{"role": "system", "content": sistema},
                         {"role": "user",   "content": usuario}],
            "max_tokens": 1200,
            "temperature": 0,      # correccion, no creatividad
        }
        # 25 s y no 60: un modelo que tarda mas de eso no cabe en el
        # presupuesto de una subida, y colgarse es peor que fallar.
        async with httpx.AsyncClient(timeout=25.0) as cli:
            for modelo in MODELOS:
                try:
                    r = await cli.post("https://openrouter.ai/api/v1/chat/completions",
                                       headers=headers, json={**cuerpo, "model": modelo})
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"]
                    # Un 429 o un 402 NO son excepciones: antes se pasaba al
                    # siguiente modelo en silencio y el informe decia "la IA no
                    # devolvio nada" sin una sola linea que explicara por que.
                    print(f"[Calidad] {modelo} -> HTTP {r.status_code}: "
                          f"{r.text[:160]}", flush=True)
                except Exception as e:
                    print(f"[Calidad] {modelo} fallo: {e}", flush=True)
        print("[Calidad] ningun modelo de la cascada respondio", flush=True)
        return None
    return _pedir


def aplicar(textos: list[str], decisiones: list[Decision],
            solo_alta: bool = True) -> tuple[list[str], dict]:
    """Sustituye las palabras aprobadas. Devuelve (textos, informe).

    MIXTO: se aplican las sistematicas y las de confianza alta; las de
    confianza baja se dejan en el informe para que las mire una persona.
    """
    cambios: dict[str, str] = {}
    aplicadas, pendientes = [], []
    for d in decisiones:
        if not d.aceptada:
            pendientes.append(d)
            continue
        if solo_alta and d.confianza != "alta" and not d.sistematica:
            pendientes.append(d)
            continue
        cambios[d.palabra.lower()] = d.correcta
        if d.sistematica:
            cambios[d.destino.lower()] = d.destino_correcto
        aplicadas.append(d)

    if not cambios:
        return textos, {"aplicadas": [], "pendientes": pendientes, "ocurrencias": 0}

    patron = re.compile(r"\b(" + "|".join(re.escape(k) for k in
                        sorted(cambios, key=len, reverse=True)) + r")\b",
                        re.IGNORECASE | re.UNICODE)

    total = 0
    def _rep(m):
        nonlocal total
        total += 1
        nueva = cambios[m.group(0).lower()]
        # Respetar la mayuscula inicial del original
        return nueva[:1].upper() + nueva[1:] if m.group(0)[:1].isupper() else nueva

    salida = [patron.sub(_rep, t) for t in textos]
    return salida, {"aplicadas": aplicadas, "pendientes": pendientes,
                    "ocurrencias": total}
