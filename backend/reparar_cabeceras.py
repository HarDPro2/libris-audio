#!/usr/bin/env python3
"""Quita las cabeceras de página del texto YA GUARDADO en R2.

EL PROBLEMA, VISTO EN EL TEXTO DE VERDAD. La parte 100 de «El libro de los
espíritus» está guardada así — 3.780 caracteres en tres líneas:

    La identidad necesaria para que se establezca una simpatía absoluta…
    Libro Segundo – Capítulo VI que un día habrán de reunirse fatalmente…
    Vida Espírita “De seguro lo ve y lo comprende mucho mejor que en la vida…

La cabecera NO es una línea suelta: está cosida al principio del párrafo que
venía detrás. El extractor de aquella época unía las líneas en párrafos, y al
unir se llevó la cabecera por delante. Por eso el TTS la lee en cada hoja.

El extractor de hoy ya no hace esto —descarta lo que cae en el borde de la
página, y además `cabeceras.py` lo caza antes de unir nada— pero los libros
subidos antes llevan el texto así guardado, y el audio se generó a partir de él.

LA REGLA, Y POR QUÉ ES SEGURA
-----------------------------
`Introducción` sale 46 veces y `Conclusión` 18: son cabeceras, pero también son
títulos legítimos. Borrarlas a ciegas se lleva el encabezado de verdad.

Lo que las separa está en la forma de la línea:

    "Libro Segundo – Capítulo VI que un día habrán…"  → cabecera pegada: fuera
    "Introducción"                                    → la línea ENTERA: se queda

Una cabecera cosida empieza la línea y la línea sigue. Un título de verdad es
la línea entera. Se exige además que lo que quede detrás sea sustancial, para
no dejar un muñón.

SIMULA POR DEFECTO. No toca nada hasta --aplicar.

    python reparar_cabeceras.py --libro 504691f6cf9e
    python reparar_cabeceras.py --libro 504691f6cf9e --aplicar

RESPALDO
--------
Antes de sobrescribir una parte se guarda copia en `{book_id}/text_original/`,
y solo la primera vez, igual que `reparar_libros.py`. El audio y los tiempos de
las partes que cambian se borran para que se regeneren solos.

Variables de entorno (las mismas del backend):
    R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_ENDPOINT_URL  R2_BUCKET_NAME
"""
import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cabeceras import detectar                                  # noqa: E402

BUCKET = (os.environ.get("R2_BUCKET_NAME") or "").strip() or "libris-audio"
HILOS = 16
_PARTE = re.compile(r"/text/part_(\d+)\.txt$")
# Lo que tiene que quedar detrás de la cabecera para creerse que era una
# cabecera pegada y no el título suelto.
RESTO_MINIMO = 25
# Cuántos caracteres se comparan contra las líneas del original para decidir
# si una línea es legítima o un pegote de dos.
COMPARAR = 50
# Lo mínimo que tiene que medir la segunda línea de un título para salvarlo.
TITULO_MINIMO = 12


# ── R2 ──────────────────────────────────────────────────────────────────────
def cliente_r2():
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3.  Instálalo con:  pip install boto3")
    req = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL")
    faltan = [v for v in req if not (os.environ.get(v) or "").strip()]
    if faltan:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltan))
    ep = os.environ["R2_ENDPOINT_URL"].strip()
    if not ep.endswith(".r2.cloudflarestorage.com"):
        sys.exit(f"R2_ENDPOINT_URL no tiene la forma esperada: {ep}")
    return boto3.client("s3", endpoint_url=ep,
                        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                        region_name="auto")


def claves(s3, prefijo):
    salida, token = [], None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": prefijo}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        salida += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return salida
        token = r.get("NextContinuationToken")


NO_SON_LIBROS = {"music"}


def _prefijos(s3) -> list[str]:
    """Las carpetas de primer nivel del bucket: un libro cada una."""
    salida, token = [], None
    while True:
        kw = {"Bucket": BUCKET, "Delimiter": "/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        salida += [p["Prefix"] for p in r.get("CommonPrefixes", [])]
        if not r.get("IsTruncated"):
            return sorted(salida)
        token = r.get("NextContinuationToken")


def bajar(s3, clave):
    return s3.get_object(Bucket=BUCKET, Key=clave)["Body"].read()


def subir(s3, clave, datos, tipo="text/plain; charset=utf-8"):
    s3.put_object(Bucket=BUCKET, Key=clave, Body=datos, ContentType=tipo)


# ── Lo único que piensa ─────────────────────────────────────────────────────
def _paginas_del_original(datos: bytes) -> list[list[str]]:
    """Las líneas del archivo original, página a página.

    Se extrae SIN el filtro de márgenes a propósito: así es como se extrajo
    cuando se subió el libro, y son esas líneas —no las de hoy— las que hay
    que comparar con el texto guardado.
    """
    import fitz
    doc = fitz.open(stream=datos, filetype="pdf")
    paginas = []
    for i in range(len(doc)):
        lineas = []
        for b in doc[i].get_text("dict").get("blocks", []):
            if b.get("type", 1) != 0:
                continue
            for linea in b.get("lines", []):
                t = "".join(s.get("text", "") for s in linea.get("spans", [])).strip()
                if t:
                    lineas.append(t)
        paginas.append(lineas)
    doc.close()
    return paginas


def _aplanar(texto: str) -> str:
    return " ".join(texto.split())


def _lineas_que_siguen(paginas: list[list[str]], cabeceras) -> set:
    """Líneas del original que EMPIEZAN por una cabecera y continúan.

    Si el original tiene «Introducción al Estudio de la Doctrina Espírita» en
    una sola línea, entonces la línea guardada que empieza así no es un pegote
    de dos: es esa línea. Solo se guardan las que empiezan por una cabecera,
    que son un puñado, para poder comparar por prefijo sin recorrer el libro.
    """
    salida = set()
    for lineas in paginas:
        for linea in lineas:
            plano = _aplanar(linea)
            for cab in cabeceras:
                if plano.startswith(cab) and len(plano) > len(cab) + 5:
                    salida.add(plano)
                    break
    return salida


def _titulos_legitimos(paginas: list[list[str]], cabeceras) -> set:
    """Comienzos que vienen DETRÁS de la cabecera y no son cabecera pegada.

    LA SEÑAL, MEDIDA SOBRE EL ORIGINAL: una cabecera corrida lleva SIEMPRE el
    número de página detrás. Las 46 apariciones de «Introducción» en el borde
    de página van seguidas de «20», «21», «22»… sin una excepción.

    Un título no. «Introducción» / «al Estudio de la Doctrina Espírita» son dos
    líneas seguidas sin número en medio, y al unirse en párrafo quedan
    exactamente igual que una cabecera pegada:

        Introducción al Estudio de la Doctrina Espírita I Para las cosas…

    Sin esto, el script se llevaba por delante el título de la introducción del
    libro. La forma de la línea no los distingue; lo que los distingue es que
    el original tiene un número en medio de una y no de la otra.
    """
    legitimos = set()
    for lineas in paginas:
        utiles = [l for l in lineas if l.strip()]
        for j, linea in enumerate(utiles):
            if linea not in cabeceras:
                continue
            siguiente = utiles[j + 1] if j + 1 < len(utiles) else ""
            plano = _aplanar(siguiente)
            # Entero, sin recortar: la comparación es «empieza por», y con el
            # texto recortado a 50 caracteres nunca coincidía con la línea
            # guardada, que sigue más allá. Y con un mínimo de longitud, para
            # que un resto de dos palabras no salve cualquier cosa.
            if plano and not plano.isdigit() and len(plano) >= TITULO_MINIMO:
                legitimos.add(plano)
    return legitimos


def cabeceras_del_original(datos: bytes) -> dict:
    """Las cadenas de cabecera, sacadas del archivo original.

    Se extrae SIN el filtro de márgenes a propósito: así es como se extrajo
    cuando se subió el libro, y son esas cadenas —no las de hoy— las que hay
    que buscar en el texto guardado.
    """
    return detectar(_paginas_del_original(datos))


def limpiar_parte(texto: str, cabeceras,
                  legitimas: set = frozenset(),
                  titulos: set = frozenset()
                  ) -> tuple[str, list[tuple[str, str]]]:
    """Quita las cabeceras cosidas al principio de una línea.

    `legitimas` son los comienzos de línea que EXISTEN tal cual en el archivo
    original. Sin eso, «Introducción a la doctrina espírita, por Allan
    Kardec…» se quedaba en «a la doctrina espírita…»: ahí «Introducción» es el
    principio de un título de verdad, no una cabecera pegada.

    Una cabecera cosida es un pegote de DOS líneas del original, así que su
    comienzo no aparece en ninguna. Un título sí aparece, entero.

    Devuelve el texto y los cambios, cada uno como (cabecera, cómo quedó), para
    poder enseñarlos antes de escribir nada.
    """
    cambios = []
    salida = []
    for linea in texto.splitlines():
        limpia = linea
        for cab in cabeceras:
            if not limpia.startswith(cab):
                continue
            # LA CABECERA TIENE QUE ACABAR EN LÍMITE DE PALABRA.
            #
            # Sin esto, «M» —el ornamento que sale 34 veces en Kardec— se
            # llevaba por delante la primera letra de CUALQUIER línea que
            # empezara por M: «Muchos hombres» -> «uchos hombres», «María» ->
            # «aría». Y en la simulación no se veía, porque los ejemplos salen
            # por orden de parte y los primeros eran todos de «Introducción».
            #
            # Vale para todas, no solo para las de una letra: «Conclusión» no
            # puede comerse el principio de «Conclusiones».
            siguiente_char = limpia[len(cab):len(cab) + 1]
            if siguiente_char and not siguiente_char.isspace():
                continue
            resto = limpia[len(cab):].lstrip()
            # La línea ENTERA siendo la cabecera es un título de verdad.
            if len(resto) < RESTO_MINIMO:
                continue
            # Y si el original tiene una línea que empieza igual y sigue,
            # tampoco es un pegote: es esa línea.
            plano_linea = _aplanar(limpia)
            if any(plano_linea.startswith(x) for x in legitimas):
                continue
            # Ni si lo que sigue es la segunda línea de un título: en el
            # original no había número de página en medio. Ver
            # `_titulos_legitimos`.
            plano = _aplanar(resto)
            if any(plano.startswith(t) for t in titulos):
                continue
            cambios.append((cab, resto[:60]))
            limpia = resto
            break
        salida.append(limpia)
    return "\n".join(salida), cambios


# ── Un libro ────────────────────────────────────────────────────────────────
def procesar(s3, libro, aplicar, ver, rehacer=False):
    todas = claves(s3, f"{libro}/")
    originales = [k for k in todas if k.startswith(f"{libro}/original/")]
    if not originales:
        # Sin el archivo original no hay de dónde sacar las cabeceras: el texto
        # guardado ya no sabe dónde acababa cada página. Los libros que
        # entraron antes de que se guardara el original están así.
        return {"estado": "sin archivo original"}
    if not rehacer and any(k.startswith(f"{libro}/text_original/") for k in todas):
        # Ya se reparó: text_original/ es el respaldo que deja este script.
        return {"estado": "ya reparado"}

    paginas = _paginas_del_original(bajar(s3, originales[0]))
    cabs = detectar(paginas)
    # Los comienzos de línea que existen de verdad en el original.
    legitimas = _lineas_que_siguen(paginas, cabs)
    titulos = _titulos_legitimos(paginas, cabs)
    # De la más larga a la más corta: si no, «Libro Segundo – Capítulo VI»
    # nunca gana contra una hipotética «Libro Segundo».
    orden = sorted(cabs, key=len, reverse=True)
    if not orden:
        return {"estado": "sin cabeceras en el original", "cabeceras": 0}

    partes = sorted(((int(m.group(1)), k) for k in todas
                     if (m := _PARTE.search(k))), key=lambda x: x[0])
    if not partes:
        return {"estado": "sin texto"}

    with ThreadPoolExecutor(max_workers=HILOS) as pool:
        textos = list(pool.map(
            lambda k: bajar(s3, k).decode("utf-8", "replace"),
            [k for _, k in partes]))

    cambiadas, total, ejemplos = {}, 0, []
    for (i, clave), texto in zip(partes, textos):
        nuevo, cambios = limpiar_parte(texto, orden, legitimas, titulos)
        if cambios:
            cambiadas[i] = (clave, nuevo)
            total += len(cambios)
            for c in cambios:
                if len(ejemplos) < 6:
                    ejemplos.append((i, c[0], c[1]))

    if aplicar and cambiadas:
        copias = set(claves(s3, f"{libro}/text_original/"))
        for i, (clave, nuevo) in cambiadas.items():
            destino = f"{libro}/text_original/part_{i}.txt"
            if destino not in copias:
                subir(s3, destino, bajar(s3, clave))
            subir(s3, clave, nuevo.encode("utf-8"))
        # El audio de esas partes se generó con la cabecera dentro.
        borrados = 0
        for k in todas:
            m = re.search(r"/(?:audio|timing)/part_(\d+)_", k)
            if m and int(m.group(1)) in cambiadas:
                s3.delete_object(Bucket=BUCKET, Key=k)
                borrados += 1
    else:
        borrados = sum(1 for k in todas
                       if (m := re.search(r"/(?:audio|timing)/part_(\d+)_", k))
                       and int(m.group(1)) in cambiadas)

    return {"estado": "aplicado" if aplicar else "simulado",
            "cabeceras": len(orden), "partes": len(partes),
            "cambiadas": len(cambiadas), "quitadas": total,
            "audio": borrados, "ejemplos": ejemplos,
            "lista": [(t, cabs[t]) for t in orden[:6]]}


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--libro", help="solo este identificador; sin esto, todos")
    p.add_argument("--rehacer", action="store_true",
                   help="mirar también los que ya se repararon")
    p.add_argument("--aplicar", action="store_true",
                   help="escribe de verdad (por defecto solo simula)")
    p.add_argument("--ver", type=int, default=6, help="cuántos ejemplos enseñar")
    p.add_argument("--porque", metavar="CADENA",
                   help="enseña el ORIGINAL alrededor de esa cadena, para ver "
                        "por qué se quita o por qué no")
    a = p.parse_args()

    s3 = cliente_r2()
    print(f"{'APLICANDO' if a.aplicar else 'SIMULACIÓN'} · libro {a.libro} "
          f"· bucket {BUCKET}\n")

    if a.porque:
        originales = [k for k in claves(s3, f"{a.libro}/")
                      if k.startswith(f"{a.libro}/original/")]
        if not originales:
            sys.exit("Ese libro no tiene el archivo original guardado.")
        paginas = _paginas_del_original(bajar(s3, originales[0]))
        vistas = 0
        for n, lineas in enumerate(paginas):
            utiles = [l for l in lineas if l.strip()]
            for j, linea in enumerate(utiles):
                if a.porque not in linea:
                    continue
                vistas += 1
                if vistas > 8:
                    break
                print(f"  pág {n + 1}, línea {j} de {len(utiles)}:")
                for k in range(max(0, j - 1), min(len(utiles), j + 3)):
                    marca = ">>" if k == j else "  "
                    print(f"     {marca} [{k}] {utiles[k][:72]!r}")
                print()
            if vistas > 8:
                break
        print(f"  {vistas} apariciones (se enseñan las primeras 8)")
        return
    if not a.libro:
        if a.aplicar:
            sys.exit("Sobre toda la biblioteca solo se simula. Para escribir, "
                     "un libro cada vez con --libro.")
        revisar_todos(s3, a.rehacer)
        return

    r = procesar(s3, a.libro, a.aplicar, a.ver, a.rehacer)

    if "cambiadas" not in r:
        print(f"  {r['estado']}")
        return

    print(f"  {r['cabeceras']} cabeceras encontradas en el original:")
    for t, n in r["lista"]:
        print(f"      {n:4d}x  {t[:56]}")
    print(f"\n  {r['quitadas']} apariciones quitadas en "
          f"{r['cambiadas']} de {r['partes']} partes\n")
    for i, cab, resto in r["ejemplos"][:a.ver]:
        print(f"      parte {i:3d}  «{cab[:40]}» → …{resto[:52]}")
    if r["audio"]:
        print(f"\n  {r['audio']} archivos de audio y tiempos "
              + ("BORRADOS: se regeneran solos"
                 if a.aplicar else "se borrarán (--aplicar)"))
    if not a.aplicar:
        print("\n  No se ha escrito nada. Para hacerlo: --aplicar")


def revisar_todos(s3, rehacer: bool) -> None:
    """Pasa la simulación por toda la biblioteca y ordena por lo que más duele.

    NUNCA escribe. Reparar se hace libro a libro y mirando los ejemplos: la
    señal se saca del archivo original de CADA libro, y un libro raro puede
    dar cabeceras raras. Un lote a ciegas sobre 97 libros no es una comodidad,
    es una forma de romper muchos a la vez.
    """
    libros = [p.rstrip("/") for p in _prefijos(s3) if p.rstrip("/") not in NO_SON_LIBROS]
    print(f"{len(libros)} libros · solo simulación\n")

    tocados, resumen = [], {}
    for n, libro in enumerate(libros, 1):
        print(f"  [{n:3d}/{len(libros)}] {libro}", end="\r", flush=True)
        try:
            r = procesar(s3, libro, False, 1, rehacer)
        except Exception as e:
            resumen["error"] = resumen.get("error", 0) + 1
            print(f"  {libro}  ERROR  {type(e).__name__}: {e}")
            continue
        resumen[r["estado"]] = resumen.get(r["estado"], 0) + 1
        if r.get("quitadas"):
            tocados.append((r["quitadas"], r["cambiadas"], r["partes"], libro,
                            r["ejemplos"][0] if r["ejemplos"] else None))

    print(" " * 40, end="\r")
    if tocados:
        print("  LIBROS CON CABECERAS EN EL TEXTO GUARDADO:\n")
        for quitadas, cambiadas, partes, libro, ejemplo in sorted(tocados,
                                                                  reverse=True):
            print(f"  {libro}  {quitadas:4d} apariciones en "
                  f"{cambiadas:3d} de {partes:3d} partes")
            if ejemplo:
                print(f"               «{ejemplo[1][:38]}» → …{ejemplo[2][:44]}")
    print("\n" + "=" * 60)
    for estado, n in sorted(resumen.items()):
        print(f"  {estado:24s} {n}")
    if tocados:
        print(f"\n  {sum(t[0] for t in tocados)} apariciones en "
              f"{len(tocados)} libros")
        print("\n  Para reparar uno:")
        print(f"      python reparar_cabeceras.py --libro {max(tocados)[3]}")
        print(f"      python reparar_cabeceras.py --libro {max(tocados)[3]} --aplicar")


if __name__ == "__main__":
    main()
