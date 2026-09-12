#!/usr/bin/env python3
"""Repara las palabras partidas por guion en los libros YA subidos.

Los libros que entraron antes del arreglo tienen el texto guardado en R2 con
las palabras cortadas ("carac- ter"), y el audio se genero a partir de ese
texto. Arreglar solo el texto no basta: el MP3 cacheado seguiria diciendo
"carac" y "ter" por separado. Por eso este script tambien borra el audio y los
tiempos de karaoke de las partes que cambien, para que se regeneren solos la
proxima vez que alguien las escuche.

SIMULA POR DEFECTO. No toca nada hasta que se le pasa --aplicar.

    python reparar_libros.py                      # simula todos los libros
    python reparar_libros.py --libro 2a31e15dfebd # simula uno
    python reparar_libros.py --libro 2a31e15dfebd --aplicar

QUE CAMBIO EL 12-09-2026, Y POR QUE
-----------------------------------
La primera version corrio sin diccionario y con el informe roto. Dos fallos:

 1. PEGABA LOS GUIONES DE VERDAD. Sin diccionario, "septiembre- octubre" ->
    "septiembreoctubre", y en los libros donde la raya de dialogo llego mal
    codificada, "parece- que" -> "pareceque". Ahora decide con el diccionario
    empaquetado y lo ambiguo NO se toca. 148 casos reales en
    test_guiones_reales.py.
 2. EL INFORME MENTIA. Los ejemplos no venian del cambio: se reconstruian
    buscando el trozo izquierdo por el texto ya reparado, sin limite de
    palabra. De ahi salio «en- contrarla» -> «ento». Ahora los ejemplos son
    los cambios de verdad.

MODOS
-----
    --despegar    deshace los pegotes que dejo la version vieja
    --restaurar   vuelve al texto original de text_original/ (si hay respaldo)

RESPALDO
--------
Desde ahora, antes de sobrescribir una parte se guarda una copia en
    {book_id}/text_original/part_N.txt
y solo la primera vez, para que el original nunca se pierda por re-ejecutar.

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guiones import (                                            # noqa: E402
    CORTE_EN_TEXTO, despegar_texto, reparar_texto_plano, vocabulario_de_textos,
)

API = os.environ.get(
    "LIBRIS_API",
    "https://libris-audio-backend-856706599879.us-west1.run.app",
).rstrip("/")


def diccionario():
    """El diccionario empaquetado. Sin el, el script NO escribe nada: es lo
    unico que distingue un corte de palabra de un guion de verdad."""
    try:
        from calidad import Diccionario
    except Exception as e:
        return None, f"no puedo importar calidad.py ({e})"
    d = Diccionario()
    if not d.disponible:
        return None, d.motivo or "diccionario no disponible"
    return (lambda w: d.existe(w) or d.existe(w.lower())), d.ruta


# ── Comprobaciones antes de tocar nada ──────────────────────────────────────
def cliente_r2():
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3.  Instalalo con:  pip install boto3")

    requeridas = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")
    faltan = [v for v in requeridas if not os.environ.get(v)]
    if faltan:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltan))

    ejemplo = [v for v in requeridas
               if os.environ[v].strip() in ("...", "") or "<" in os.environ[v]]
    if ejemplo:
        sys.exit(
            "Estas variables tienen valores de ejemplo, no los reales: "
            + ", ".join(ejemplo))

    ep = os.environ["R2_ENDPOINT_URL"].strip()
    if not ep.startswith("https://") or not ep.endswith(".r2.cloudflarestorage.com"):
        sys.exit("R2_ENDPOINT_URL no tiene la forma esperada.\n"
                 "  Esperado: https://<id-de-cuenta>.r2.cloudflarestorage.com\n"
                 f"  Recibido: {ep}")

    return boto3.client(
        "s3",
        endpoint_url=ep,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def listar_libros():
    import urllib.request
    with urllib.request.urlopen(f"{API}/api/books", timeout=60) as r:
        return json.load(r)


def claves_con_fecha(s3, bucket, prefijo):
    """Devuelve {clave: LastModified}. La fecha es la unica prueba objetiva de
    que una parte se reescribio: las que no se tocaron conservan la fecha de
    subida original."""
    salida, token = {}, None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefijo}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        for o in r.get("Contents", []):
            salida[o["Key"]] = o.get("LastModified")
        if not r.get("IsTruncated"):
            return salida
        token = r.get("NextContinuationToken")


def claves(s3, bucket, prefijo):
    salida, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefijo}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        salida += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return salida
        token = r.get("NextContinuationToken")


def _num(k):
    return int(re.search(r"part_(\d+)", k).group(1))


def respaldar(s3, bucket, book_id, clave, texto, existentes):
    """Copia la parte a text_original/ la PRIMERA vez que se toca."""
    destino = f"{book_id}/text_original/part_{_num(clave)}.txt"
    if destino in existentes:
        return False
    s3.put_object(Bucket=bucket, Key=destino, Body=texto.encode("utf-8"),
                  ContentType="text/plain; charset=utf-8")
    return True


def invalidar_audio(s3, bucket, book_id, indices):
    borrados = 0
    for prefijo in (f"{book_id}/audio/", f"{book_id}/timing/"):
        for k in claves(s3, bucket, prefijo):
            m = re.search(r"part_(\d+)", k)
            if m and int(m.group(1)) in indices:
                s3.delete_object(Bucket=bucket, Key=k)
                borrados += 1
    return borrados


def escribir(s3, bucket, book_id, cambiadas, originales, ver):
    """Respalda, escribe e invalida el audio. Devuelve archivos invalidados."""
    existentes = set(claves(s3, bucket, f"{book_id}/text_original/"))
    respaldadas = 0
    for k, nuevo in cambiadas:
        if respaldar(s3, bucket, book_id, k, originales[k], existentes):
            respaldadas += 1
    for k, nuevo in cambiadas:
        s3.put_object(Bucket=bucket, Key=k, Body=nuevo.encode("utf-8"),
                      ContentType="text/plain; charset=utf-8")
    borrados = invalidar_audio(s3, bucket, book_id, {_num(k) for k, _ in cambiadas})
    print(f"        aplicado: {len(cambiadas)} partes · {respaldadas} respaldadas "
          f"· {borrados} audio/karaoke invalidados")
    return borrados


def procesar(s3, bucket, libro, args, es_valida):
    book_id = libro.get("book_id")
    titulo  = (libro.get("title") or "")[:44]
    if not book_id:
        return 0, 0, 0

    fechas = claves_con_fecha(s3, bucket, f"{book_id}/text/")
    partes = sorted((k for k in fechas if k.endswith(".txt")), key=_num)
    if not partes:
        print(f"  --  {titulo:46} sin texto en R2")
        return 0, 0, 0

    # --desde: solo las partes reescritas a partir de esa fecha. Es la forma
    # de limitar el despegado a lo que toco una tanda concreta y no andar
    # "arreglando" defectos que el libro ya traia de su PDF.
    tocables = set(partes)
    if args.desde:
        tocables = {k for k in partes
                    if fechas.get(k) and fechas[k].date().isoformat() >= args.desde}
        print(f"  ..  {titulo:46} {len(tocables)} de {len(partes)} partes "
              f"modificadas desde {args.desde}")
        if not tocables:
            return 0, 0, 0

    if args.restaurar:
        return restaurar(s3, bucket, book_id, titulo, partes, args)

    # El vocabulario se construye con el LIBRO ENTERO: cuantas mas paginas,
    # mejores decisiones. Con una sola parte se decide casi a ciegas.
    originales = {}
    for k in partes:
        originales[k] = s3.get_object(Bucket=bucket, Key=k)["Body"] \
                          .read().decode("utf-8", "replace")
    textos = [originales[k] for k in partes]

    cambiadas, total, ejemplos = [], 0, []

    if args.basura:
        import basura as B
        frec_b = B.frecuencias(textos)
        tokens = B.detectar_basura(frec_b, es_valida, args.min_basura)
        cabeceras = B.detectar_cabeceras(textos)
        # Las dos cosas son independientes: "Los Mediums" no tiene NI UN token
        # suelto y sin embargo arrastra 415 cabeceras. Cortar aqui por falta de
        # tokens dejaba ese libro sin limpiar.
        if not tokens and not cabeceras:
            print(f"  --  {titulo:46} sin basura detectada")
            return 0, 0, 0
        ordenados = sorted(tokens, key=lambda w: -frec_b[w])
        if tokens:
            print(f"  ..  {titulo:46} {len(tokens)} tokens sospechosos: "
                  + ", ".join(f"{w}({frec_b[w]})" for w in ordenados[:12])
                  + (" ..." if len(ordenados) > 12 else ""))
        if cabeceras:
            print(f"      {len(cabeceras)} cabeceras repetidas: "
                  + " · ".join(f"«{c}»" for c in cabeceras[:4]))
        encontradas = sum(frec_b[w] for w in tokens)
        for k in partes:
            reg = []
            # Las cabeceras primero: son frases enteras y se comen los tokens
            # que llevan dentro.
            nuevo_txt, n = B.limpiar_cabeceras(originales[k], cabeceras, reg)
            nuevo_txt, n2 = B.limpiar(nuevo_txt, tokens, reg)
            n += n2
            if n:
                total += n
                cambiadas.append((k, nuevo_txt))
                ejemplos += reg
        etiqueta = "quitados de dentro de frases"

    elif args.despegar:
        from collections import Counter
        from guiones import _PALABRA
        frec: Counter = Counter()
        for t in textos:
            for w in _PALABRA.findall(t):
                frec[w.lower()] += 1
        # Las palabras de las partes INTACTAS son coartada: si un supuesto
        # pegote sale tambien ahi, venia del libro y no lo hicimos nosotros.
        intactas = set()
        if args.desde:
            for k in partes:
                if k not in tocables:
                    intactas.update(w.lower() for w in _PALABRA.findall(originales[k]))
            print(f"        {len(intactas)} palabras distintas en las partes "
                  f"intactas sirven de coartada")

        encontradas = 0
        for k in partes:
            if k not in tocables:
                continue
            reg = []
            nuevo, n = despegar_texto(originales[k], frec, es_valida, reg,
                                      evitar=intactas,
                                      estricto=not args.laxo)
            if n:
                total += n
                cambiadas.append((k, nuevo))
                ejemplos += reg
        etiqueta = ("pegotes deshechos" if args.laxo
                    else "pegotes deshechos (estricto)")
    else:
        encontradas = sum(len(CORTE_EN_TEXTO.findall(t)) for t in textos)
        vocab = vocabulario_de_textos(textos)
        for k in partes:
            if k not in tocables:
                continue
            reg = []
            nuevo, n = reparar_texto_plano(originales[k], vocab, es_valida, reg)
            if n:
                total += n
                cambiadas.append((k, nuevo))
                ejemplos += reg
        etiqueta = "palabras reunidas"

    marca = "OK " if total else "-- "
    print(f"  {marca} {titulo:46} {len(partes):4} partes · "
          f"{encontradas:5} partidas · {total:5} {etiqueta} · "
          f"{len(cambiadas):4} partes a reescribir")
    if not args.sin_ejemplos and ejemplos:
        vistos, muestra = set(), []
        for a, b in ejemplos:                 # ejemplos DISTINTOS, no repetidos
            if a.lower() in vistos:
                continue
            vistos.add(a.lower())
            muestra.append((a, b))
            if len(muestra) >= args.ejemplos:
                break
        for a, b in muestra:
            print(f"        «{a}»  ->  «{b}»")
        if len(vistos) < len({a.lower() for a, _ in ejemplos}):
            pass
    sin_tocar = encontradas - total
    if sin_tocar > 0 and not (args.despegar or args.basura):
        print(f"        ({sin_tocar} sin tocar: o eran guiones de verdad, "
              f"o la salvaguarda dijo que no)")

    if not args.aplicar or not cambiadas:
        return encontradas, total, 0
    return encontradas, total, escribir(s3, bucket, book_id, cambiadas,
                                        originales, not args.sin_ejemplos)


def restaurar(s3, bucket, book_id, titulo, partes, args):
    """Devuelve el texto a como estaba, desde text_original/."""
    copias = {_num(k): k for k in claves(s3, bucket, f"{book_id}/text_original/")
              if k.endswith(".txt")}
    if not copias:
        print(f"  --  {titulo:46} sin respaldo (nada que restaurar)")
        return 0, 0, 0
    print(f"  OK  {titulo:46} {len(copias)} partes con respaldo")
    if not args.aplicar:
        return len(copias), 0, 0
    for n, origen in copias.items():
        cuerpo = s3.get_object(Bucket=bucket, Key=origen)["Body"].read()
        s3.put_object(Bucket=bucket, Key=f"{book_id}/text/part_{n}.txt",
                      Body=cuerpo, ContentType="text/plain; charset=utf-8")
    borrados = invalidar_audio(s3, bucket, book_id, set(copias))
    print(f"        restauradas {len(copias)} partes · {borrados} audio invalidados")
    return len(copias), 0, borrados


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--libro", help="book_id concreto; si falta, todos")
    ap.add_argument("--aplicar", action="store_true", help="escribe de verdad")
    ap.add_argument("--despegar", action="store_true",
                    help="deshace los pegotes de la version vieja")
    ap.add_argument("--basura", action="store_true",
                    help="quita encabezados y pies incrustados en las frases")
    ap.add_argument("--min-basura", type=int, default=5,
                    help="apariciones minimas para considerar un token basura")
    ap.add_argument("--restaurar", action="store_true",
                    help="vuelve al texto de text_original/")
    ap.add_argument("--laxo", action="store_true",
                    help="despegar sin exigir palabra de funcion detras; solo "
                         "con muchas partes intactas que sirvan de coartada")
    ap.add_argument("--desde", metavar="AAAA-MM-DD",
                    help="solo las partes reescritas desde esa fecha")
    ap.add_argument("--ejemplos", type=int, default=6,
                    help="cuantos ejemplos distintos ensenar por libro")
    ap.add_argument("--sin-ejemplos", action="store_true")
    args = ap.parse_args()

    modos = sum(bool(x) for x in (args.despegar, args.restaurar, args.basura))
    if modos > 1:
        sys.exit("--despegar, --basura y --restaurar son cosas distintas; "
                 "uno cada vez.")

    es_valida, ruta = (None, None)
    if not args.restaurar:
        es_valida, ruta = diccionario()
        if es_valida is None:
            sys.exit(f"Sin diccionario no escribo nada: {ruta}\n"
                     "Es lo unico que distingue 'espo- sos' (unir) de "
                     "'septiembre- octubre' (no tocar).")

    s3 = cliente_r2()
    bucket = os.environ.get("R2_BUCKET_NAME") or os.environ.get("R2_BUCKET", "libris-audio")

    libros = listar_libros()
    if args.libro:
        libros = [l for l in libros if l.get("book_id") == args.libro]
        if not libros:
            sys.exit(f"No encuentro el libro {args.libro} en {API}/api/books")

    modo = ("RESTAURANDO" if args.restaurar else
            "DESPEGANDO" if args.despegar else
            "QUITANDO BASURA" if args.basura else "REPARANDO")
    print(f"{len(libros)} libro(s) · bucket {bucket} · {modo} · "
          f"{'APLICANDO CAMBIOS' if args.aplicar else 'SIMULACION'}")
    if ruta:
        print(f"diccionario: {ruta}")
    print()

    tot_a = tot_b = tot_c = 0
    for l in libros:
        try:
            a, b, c = procesar(s3, bucket, l, args, es_valida)
            tot_a += a; tot_b += b; tot_c += c
        except KeyboardInterrupt:
            print("\n  interrumpido a mano. Los libros ya procesados quedan hechos.")
            break
        except Exception as e:
            print(f"  !!  {(l.get('title') or '')[:46]:46} error: {e}")

    print(f"\n  palabras partidas encontradas : {tot_a}")
    print(f"  cambios                       : {tot_b}")
    if args.aplicar:
        print(f"  audio/karaoke invalidado      : {tot_c} archivos")
        print("\nHecho. El audio se regenera solo la proxima vez que se escuche.")
        print("El texto de antes queda en {book_id}/text_original/ ; "
              "para volver atras:  python reparar_libros.py --restaurar --aplicar")
    else:
        print("\n[SIMULACION] No se escribio nada. Revisa los ejemplos de arriba.")
        print("Los ejemplos son ahora los cambios de verdad, no una reconstruccion.")


if __name__ == "__main__":
    main()
