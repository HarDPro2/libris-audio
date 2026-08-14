"""
Extracción y normalización de documentos — META 1 / META 2.

Punto de encuentro de ambas metas: TODO formato de entrada (y también el OCR)
desemboca en la misma estructura `Documento`. El resto del backend —TTS,
karaoke, índice de capítulos, copiloto de IA— trabaja solo contra ella y no
sabe de qué formato venía el archivo.

Añadir un formato nuevo = escribir un extractor que devuelva `Documento`.
No hay que tocar nada más.

Dependencias: PyMuPDF (ya en requirements). `python-docx` es opcional; si no
está instalado, los .docx se rechazan con un mensaje claro en vez de romper.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# Estructura normalizada
# ---------------------------------------------------------------------------

@dataclass
class Capitulo:
    titulo: str
    indice: int
    bloques: list[str] = field(default_factory=list)

    @property
    def texto(self) -> str:
        return "\n".join(self.bloques)


@dataclass
class Documento:
    titulo: str
    formato: str
    capitulos: list[Capitulo] = field(default_factory=list)
    necesita_ocr: bool = False          # META 2 lo usará como disparador
    aviso: str | None = None
    idioma: str | None = None           # 'es' | 'en' | None (META 3.9)

    @property
    def texto(self) -> str:
        return "\n".join(c.texto for c in self.capitulos)

    @property
    def indice(self) -> list[dict]:
        """Índice navegable: [{titulo, capitulo, offset_caracteres}]"""
        salida, cursor = [], 0
        for c in self.capitulos:
            salida.append({"titulo": c.titulo, "capitulo": c.indice, "offset": cursor})
            cursor += len(c.texto) + 1
        return salida


# ---------------------------------------------------------------------------
# Detección de idioma — META 3.9 (karaoke para aprender idiomas)
#
# Sin dependencias: cuenta palabras vacías características de cada idioma.
# Solo distingue español e inglés, que es lo que soportan las voces.
# ---------------------------------------------------------------------------

_VACIAS_ES = {"de","la","que","el","en","y","a","los","del","se","las","por",
              "un","para","con","no","una","su","al","es","lo","como","más",
              "pero","sus","le","ya","o","este","sí","porque","esta","son",
              "entre","cuando","muy","sin","sobre","también","me","hasta",
              "hay","donde","quien","desde","todo","nos","durante","todos"}
_VACIAS_EN = {"the","of","and","to","in","is","it","you","that","he","was",
              "for","on","are","as","with","his","they","at","be","this",
              "have","from","or","one","had","by","word","but","not","what",
              "all","were","we","when","your","can","said","there","use",
              "each","which","she","do","how","their","if","will","about"}


def detectar_idioma(texto: str) -> str | None:
    """Devuelve 'es', 'en' o None si no hay señal suficiente."""
    palabras = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ']+", texto[:20000].lower())
    if len(palabras) < 30:
        return None
    es = sum(1 for p in palabras if p in _VACIAS_ES)
    en = sum(1 for p in palabras if p in _VACIAS_EN)
    if es == en == 0:
        return None
    # Se exige una diferencia clara para no adivinar a ciegas.
    if es >= en * 1.4:
        return "es"
    if en >= es * 1.4:
        return "en"
    return None


class DocumentoProtegido(Exception):
    """El archivo tiene DRM. No se procesa: se avisa y punto."""


class FormatoNoSoportado(Exception):
    pass


# ---------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------

# Los que MuPDF abre de forma nativa. Verificado con archivos reales.
MUPDF = {
    "pdf": "pdf", "epub": "epub", "mobi": "mobi", "fb2": "fb2",
    "xps": "xps", "cbz": "cbz", "txt": "txt",
}
# Foto de una página del libro hecha con el móvil. Siempre pasa por OCR.
IMAGENES = {"jpg", "jpeg", "png", "webp", "tif", "tiff", "bmp"}
# Texto plano que tratamos nosotros para conservar la estructura.
PLANOS = {"txt", "md", "markdown", "html", "htm", "xhtml"}
# Kindle: en la práctica siempre llevan DRM. Solo pasan los que no lo tengan.
KINDLE = {"azw", "azw3", "azw4", "kfx", "prc"}
OTROS  = {"docx"}

SOPORTADOS = sorted(set(MUPDF) | PLANOS | KINDLE | OTROS | IMAGENES)


def extension(nombre: str) -> str:
    return nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""


# ---------------------------------------------------------------------------
# Detección de DRM
# ---------------------------------------------------------------------------

_MARCAS_DRM = (b"EncryptedContent", b"encryption.xml", b"DRMedBook",
               b"MSDRM", b"Adept", b"adobe.com/adept")


def detectar_drm(datos: bytes, ext: str) -> bool:
    """
    True si el archivo está protegido. Conservador: ante la duda, en los
    formatos Kindle asumimos DRM, que es lo que ocurre casi siempre.
    """
    if ext in ("azw", "azw3", "azw4", "prc"):
        # Los MOBI/AZW sin DRM llevan 0 en el campo de cifrado de la cabecera
        # PalmDOC (offset 12 del record 0). Si no se puede leer, asumimos DRM.
        try:
            if datos[60:68] in (b"BOOKMOBI", b"TEXtREAd"):
                inicio = int.from_bytes(datos[78:82], "big")
                cifrado = int.from_bytes(datos[inicio + 12:inicio + 14], "big")
                return cifrado != 0
        except Exception:
            return True
        return True
    if ext == "kfx":
        return True                      # formato cerrado, siempre protegido
    if ext == "epub":
        try:
            with zipfile.ZipFile(io.BytesIO(datos)) as z:
                return "META-INF/encryption.xml" in z.namelist()
        except Exception:
            return False
    if ext == "pdf":
        try:
            d = fitz.open(stream=datos, filetype="pdf")
            protegido = d.needs_pass or (d.is_encrypted and not d.authenticate(""))
            d.close()
            return bool(protegido)
        except Exception:
            return False
    return any(m in datos[:200_000] for m in _MARCAS_DRM)


# ---------------------------------------------------------------------------
# Limpieza (semilla del filtro académico de la META 3)
# ---------------------------------------------------------------------------

_SOLO_NUMERO   = re.compile(r"^\d+$")
_PAGINA        = re.compile(r"(p[áa]gina|page|pág\.?)\s*\d+$", re.IGNORECASE)
_GUION_NUMERO  = re.compile(r"^[-–—\s]*\d+[-–—\s]*$")

# ── Filtro de ruido académico (META 3.1) ────────────────────────────────────
# Escuchar un PDF universitario sin esto es una tortura: la voz lee en alto
# cada cita bibliográfica, cada URL y cada número de nota al pie.
# ES CONFIGURABLE a propósito: un investigador puede querer oír las citas que
# un estudiante quiere saltarse.

# (Freud, 1915, p. 43) · (cf. Lacan 1966) · (2020) · (ibíd., p. 12) · [12]
_CITA_PARENTESIS = re.compile(
    r"\(\s*(?:cf\.|véase|vease|ver|see|ibid\.?|ibíd\.?|op\.\s*cit\.?|et\s*al\.?)?[^()]{0,80}?"
    r"(?:\b\d{4}[a-z]?\b|\bp{1,2}\.\s*\d+|\bpág{1,2}\.?\s*\d+)[^()]{0,40}\)",
    re.IGNORECASE)
_CITA_CORCHETES  = re.compile(r"\[\s*\d+(?:\s*[,–-]\s*\d+)*\s*\]")
_URL             = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
_DOI             = re.compile(r"\bdoi:\s*\S+|\b10\.\d{4,}/\S+", re.IGNORECASE)
_CORREO          = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
# Línea que es solo la marca de una nota al pie: "12 Ibíd., p. 44."
_NOTA_PIE        = re.compile(r"^\d{1,3}\s+(ib[íi]d|op\.\s*cit|v[ée]ase|cf\.|\[)", re.IGNORECASE)
_ESPACIO_ANTES   = re.compile(r"\s+([,.;:!?])")


def _quitar_ruido_academico(texto: str) -> str:
    texto = _URL.sub(" ", texto)
    texto = _DOI.sub(" ", texto)
    texto = _CORREO.sub(" ", texto)
    texto = _CITA_PARENTESIS.sub(" ", texto)
    texto = _CITA_CORCHETES.sub(" ", texto)
    texto = _ESPACIO_ANTES.sub(r"\1", texto)
    return texto


def limpiar_bloque(texto: str, filtro_academico: bool = True,
                   repetidas: set | None = None) -> str:
    """
    `repetidas` son las líneas que aparecen en casi todas las páginas
    (encabezados y pies de página); se calculan a nivel de documento.
    """
    lineas = []
    for linea in texto.splitlines():
        s = linea.strip()
        if not s or _SOLO_NUMERO.match(s) or _PAGINA.search(s) or _GUION_NUMERO.match(s):
            continue
        if repetidas and s in repetidas:
            continue
        if filtro_academico and _NOTA_PIE.match(s):
            continue
        lineas.append(s)
    salida = " ".join(lineas)
    if filtro_academico:
        salida = _quitar_ruido_academico(salida)
    return re.sub(r"  +", " ", salida).strip()


def _lineas_repetidas(paginas_crudas: list[str], umbral: float = 0.5) -> set:
    """Encabezados y pies: líneas cortas que salen en más de la mitad de las páginas."""
    if len(paginas_crudas) < 4:
        return set()
    from collections import Counter
    c = Counter()
    for pagina in paginas_crudas:
        vistas = {l.strip() for l in pagina.splitlines()
                  if 3 < len(l.strip()) < 90}
        c.update(vistas)
    minimo = max(3, int(len(paginas_crudas) * umbral))
    return {linea for linea, n in c.items() if n >= minimo}


# ---------------------------------------------------------------------------
# OCR — META 2
#
# Se activa solo cuando el documento no trae capa de texto. Rellena el MISMO
# `Documento` que el resto de extractores, así que nada del pipeline cambia.
# ---------------------------------------------------------------------------

OCR_IDIOMAS   = "spa+eng"
# Medido: ~6.7 s por página densa a 200 DPI. 20 páginas ≈ 135 s, que cabe
# holgadamente en el timeout de 300 s de Cloud Run. Con 60 páginas se iba a
# 404 s y la petición moría. Subir este número exige mover el OCR a una tarea
# en segundo plano con consulta de estado.
OCR_MAX_PAGS  = 20
OCR_DPI       = 200     # suficiente para texto impreso; 300 casi no mejora


def ocr_disponible() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ocr_pagina(pagina) -> str:
    """Rasteriza una página y la pasa por Tesseract."""
    import pytesseract
    from PIL import Image
    pix = pagina.get_pixmap(dpi=OCR_DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return pytesseract.image_to_string(img, lang=OCR_IDIOMAS)


def _ocr_documento(datos: bytes, tipo: str) -> tuple[list[str], int, bool]:
    """Devuelve (textos_por_pagina, paginas_procesadas, se_trunco)."""
    doc = fitz.open(stream=datos, filetype=tipo)
    total = doc.page_count
    limite = min(total, OCR_MAX_PAGS)
    textos = []
    for i in range(limite):
        try:
            textos.append(limpiar_bloque(_ocr_pagina(doc.load_page(i))))
        except Exception:
            textos.append("")
    doc.close()
    return textos, limite, total > limite


# ---------------------------------------------------------------------------
# Extractores
# ---------------------------------------------------------------------------

_MIN_CARACTERES_POR_PAGINA = 25   # por debajo de esto, es un escaneo


def _extraer_mupdf(datos: bytes, ext: str, titulo: str,
                   permitir_ocr: bool = True,
                   filtro_academico: bool = True) -> Documento:
    tipo = MUPDF.get(ext, ext)
    doc = fitz.open(stream=datos, filetype=tipo)

    toc = []
    try:
        toc = doc.get_toc() or []
    except Exception:
        pass

    # Página en la que empieza cada capítulo, según el índice del propio archivo
    inicios = {}
    for nivel, nombre, pagina in toc:
        if nivel <= 2 and pagina >= 1:
            inicios.setdefault(pagina - 1, nombre.strip() or f"Capítulo {len(inicios)+1}")

    crudas   = [doc.load_page(i).get_text() for i in range(doc.page_count)]
    repetidas = _lineas_repetidas(crudas)
    paginas  = [limpiar_bloque(t, filtro_academico, repetidas) for t in crudas]
    total_paginas = doc.page_count
    doc.close()

    caracteres = sum(len(p) for p in paginas)
    necesita_ocr = total_paginas > 0 and (caracteres / total_paginas) < _MIN_CARACTERES_POR_PAGINA
    aviso = None

    # AQUÍ es donde META 2 rellena el hueco que dejó META 1.
    if necesita_ocr and permitir_ocr and ocr_disponible():
        textos, procesadas, truncado = _ocr_documento(datos, tipo)
        if sum(len(t) for t in textos) > 0:
            paginas = textos + [""] * (total_paginas - len(textos))
            necesita_ocr = False
            aviso = (f"Texto reconocido por OCR de las primeras {procesadas} páginas."
                     if truncado else "Texto reconocido por OCR.")

    capitulos: list[Capitulo] = []
    actual = Capitulo(titulo=inicios.get(0, "Inicio"), indice=0)
    for i, texto in enumerate(paginas):
        if i in inicios and i != 0:
            if actual.bloques:
                capitulos.append(actual)
            actual = Capitulo(titulo=inicios[i], indice=len(capitulos))
        if texto:
            actual.bloques.append(texto)
    if actual.bloques or not capitulos:
        capitulos.append(actual)

    return Documento(titulo=titulo, formato=ext, capitulos=capitulos,
                     necesita_ocr=necesita_ocr, aviso=aviso)


_ETIQUETAS = re.compile(r"<[^>]+>")
_ENCABEZADO = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)


def _extraer_plano(datos: bytes, ext: str, titulo: str) -> Documento:
    texto = datos.decode("utf-8", errors="replace")
    capitulos: list[Capitulo] = []

    if ext in ("html", "htm", "xhtml"):
        texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", texto,
                       flags=re.IGNORECASE | re.DOTALL)
        trozos = _ENCABEZADO.split(texto)
        if len(trozos) > 1:
            cuerpo = trozos[0]
            if limpiar_bloque(_ETIQUETAS.sub(" ", cuerpo)):
                capitulos.append(Capitulo("Inicio", 0,
                                          [limpiar_bloque(_ETIQUETAS.sub(" ", cuerpo))]))
            for i in range(1, len(trozos), 2):
                nombre = limpiar_bloque(_ETIQUETAS.sub(" ", trozos[i])) or f"Sección {i//2+1}"
                cuerpo = limpiar_bloque(_ETIQUETAS.sub(" ", trozos[i + 1])) if i + 1 < len(trozos) else ""
                capitulos.append(Capitulo(nombre, len(capitulos), [cuerpo] if cuerpo else []))
        else:
            capitulos.append(Capitulo("Documento", 0,
                                      [limpiar_bloque(_ETIQUETAS.sub(" ", texto))]))
    elif ext in ("md", "markdown"):
        actual = Capitulo("Inicio", 0)
        for linea in texto.splitlines():
            m = re.match(r"^(#{1,3})\s+(.*)", linea)
            if m:
                if actual.bloques:
                    capitulos.append(actual)
                actual = Capitulo(m.group(2).strip(), len(capitulos))
            elif linea.strip():
                actual.bloques.append(linea.strip())
        capitulos.append(actual)
    else:
        capitulos.append(Capitulo("Documento", 0, [limpiar_bloque(texto)]))

    capitulos = [c for c in capitulos if c.texto.strip()] or [Capitulo("Documento", 0, [])]
    return Documento(titulo=titulo, formato=ext, capitulos=capitulos)


def _extraer_docx(datos: bytes, titulo: str) -> Documento:
    try:
        import docx  # python-docx
    except ImportError:
        raise FormatoNoSoportado(
            "El servidor no tiene soporte para .docx todavía. "
            "Conviértelo a PDF o EPUB mientras tanto."
        )
    d = docx.Document(io.BytesIO(datos))
    capitulos: list[Capitulo] = []
    actual = Capitulo("Inicio", 0)
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if (p.style.name or "").lower().startswith("heading"):
            if actual.bloques:
                capitulos.append(actual)
            actual = Capitulo(t, len(capitulos))
        else:
            actual.bloques.append(t)
    capitulos.append(actual)
    capitulos = [c for c in capitulos if c.texto.strip()] or [Capitulo("Documento", 0, [])]
    return Documento(titulo=titulo, formato="docx", capitulos=capitulos)


# ---------------------------------------------------------------------------
# Entrada única
# ---------------------------------------------------------------------------

def extraer(datos: bytes, nombre_archivo: str, titulo: str | None = None,
            filtro_academico: bool = True) -> Documento:
    """
    Convierte cualquier archivo soportado en un `Documento` normalizado.

    Lanza DocumentoProtegido si tiene DRM y FormatoNoSoportado si no sabemos
    abrirlo. Si el texto extraído es demasiado escaso marca `necesita_ocr`,
    que es el disparador de la META 2.
    """
    ext = extension(nombre_archivo)
    if not ext:
        raise FormatoNoSoportado("El archivo no tiene extensión.")
    if ext not in SOPORTADOS:
        raise FormatoNoSoportado(
            f"Formato .{ext} no soportado. Admitidos: {', '.join(SOPORTADOS)}."
        )
    if not datos:
        raise FormatoNoSoportado("El archivo está vacío.")

    if detectar_drm(datos, ext):
        raise DocumentoProtegido(
            "Este archivo está protegido con DRM y no se puede procesar. "
            "Reprodúcelo en la aplicación donde lo compraste."
        )

    titulo = (titulo or "").strip() or \
        nombre_archivo.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip() or \
        "Documento sin título"

    doc = _extraer_segun_formato(datos, ext, titulo, filtro_academico)
    if doc.idioma is None:
        doc.idioma = detectar_idioma(doc.texto)
    return doc


def _extraer_segun_formato(datos: bytes, ext: str, titulo: str,
                           filtro_academico: bool) -> Documento:
    if ext == "docx":
        return _extraer_docx(datos, titulo)
    if ext in PLANOS and ext != "txt":
        return _extraer_plano(datos, ext, titulo)
    if ext in KINDLE:
        # Sin DRM, un AZW3/PRC es un MOBI: MuPDF lo abre.
        return _extraer_mupdf(datos, "mobi", titulo, filtro_academico=filtro_academico)
    if ext in IMAGENES:
        doc = _extraer_mupdf(datos, "jpeg" if ext in ("jpg", "jpeg") else ext, titulo)
        doc.formato = ext
        if doc.necesita_ocr:
            doc.aviso = ("No se pudo reconocer texto en la imagen. "
                         "Prueba con una foto más nítida y bien iluminada.")
        return doc
    if ext in MUPDF:
        return _extraer_mupdf(datos, ext, titulo, filtro_academico=filtro_academico)
    return _extraer_plano(datos, ext, titulo)
