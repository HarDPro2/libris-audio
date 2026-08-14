from __future__ import annotations
import sys
import logging
from typing import List, Optional
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
print("=== STARTING LIBRIS AUDIO BACKEND — Google Cloud Run ===", flush=True)

import asyncio
import os
import re
import uuid
import json
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import edge_tts

from extractores import (
    extraer as extraer_documento,
    DocumentoProtegido,
    FormatoNoSoportado,
    SOPORTADOS as FORMATOS_SOPORTADOS,
)

try:
    import fitz  # PyMuPDF
except ImportError as ex:
    fitz = None
    print(f"Warning: PyMuPDF not available: {ex}")

import uvicorn
import httpx
from gtts import gTTS
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, PlainTextResponse
from appwrite.client import Client as AppwriteClient
from appwrite.services.databases import Databases as AppwriteDatabases

# ---------------------------------------------------------------------------
# Appwrite — base de datos principal (24/7, sin pausas)
# ---------------------------------------------------------------------------
APPWRITE_ENDPOINT   = os.environ.get("APPWRITE_ENDPOINT", "https://nyc.cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID", "6a72f5d6002eeff78bc2")
APPWRITE_API_KEY    = os.environ.get("APPWRITE_API_KEY")  # obligatorio en Cloud Run env vars
APPWRITE_DB_ID      = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")

if not APPWRITE_API_KEY:
    print("WARNING: APPWRITE_API_KEY no configurada en variables de entorno.", flush=True)

appwrite_client = AppwriteClient()
appwrite_client.set_endpoint(APPWRITE_ENDPOINT)
appwrite_client.set_project(APPWRITE_PROJECT_ID)
if APPWRITE_API_KEY:
    appwrite_client.set_key(APPWRITE_API_KEY)

appwrite_db = AppwriteDatabases(appwrite_client)

# ---------------------------------------------------------------------------
# Cloudflare R2 — almacenamiento de portadas, texto y audio MP3
# ---------------------------------------------------------------------------
R2_ACCESS_KEY_ID     = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT_URL      = os.environ.get("R2_ENDPOINT_URL", "")
R2_BUCKET            = os.environ.get("R2_BUCKET_NAME", "libris-audio")
R2_PUBLIC_URL        = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")

_r2_client = None


def get_r2():
    """Lazy singleton para el cliente boto3 apuntando a R2."""
    global _r2_client
    if _r2_client is None:
        _r2_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _r2_client


def r2_upload(key: str, data: bytes, content_type: str) -> None:
    get_r2().put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=content_type)


def r2_public_url(key: str) -> str:
    return f"{R2_PUBLIC_URL}/{key}"


def r2_exists(key: str) -> bool:
    try:
        get_r2().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def r2_download(key: str) -> bytes:
    obj = get_r2().get_object(Bucket=R2_BUCKET, Key=key)
    return obj["Body"].read()


def r2_delete(keys: list[str]) -> None:
    if not keys:
        return
    get_r2().delete_objects(
        Bucket=R2_BUCKET,
        Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
    )


def r2_list_prefix(prefix: str) -> list[str]:
    paginator = get_r2().get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
BASE_DIR  = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "static" / "audio"
BOOKS_DIR = BASE_DIR / "static" / "books"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
BOOKS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="LibrisAudio API — Google Cloud Run")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers de texto
# ---------------------------------------------------------------------------
def clean_text_for_tts(raw: str) -> str:
    """Limpia texto extraído de PDF para edge-tts."""
    lines = raw.splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r'\d+', stripped):
            continue
        if re.search(r'(p[áa]gina|page|pág\.?)\s*\d+$', stripped, re.IGNORECASE):
            continue
        if re.fullmatch(r'[-–—\s]*\d+[-–—\s]*', stripped):
            continue
        cleaned.append(stripped)

    text = ' '.join(cleaned)
    text = re.sub(r'  +', ' ', text)
    if text and text[-1] not in '.!?':
        text += '.'
    return text.strip()


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 1000) -> str:
    """Extrae texto limpio del PDF usando análisis de tamaño de fuente."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = min(len(doc), max_pages)

    font_counts = {}
    sample_pages = min(20, num_pages)
    for i in range(sample_pages):
        page = doc[i]
        for b in page.get_text("dict").get("blocks", []):
            if b.get("type", 1) != 0:
                continue
            for line in b.get("lines", []):
                for s in line.get("spans", []):
                    size = round(s.get("size", 0), 1)
                    text = s.get("text", "").strip()
                    if len(text) > 2:
                        font_counts[size] = font_counts.get(size, 0) + len(text)

    if not font_counts:
        return ""

    main_font_size = max(font_counts, key=font_counts.get)
    print(f"[PDF] Tamaño fuente dominante: {main_font_size}")

    extracted_lines = []
    for i in range(num_pages):
        page = doc[i]
        page_height = page.rect.height
        top_margin    = page_height * 0.06
        bottom_margin = page_height * 0.94

        for b in page.get_text("dict").get("blocks", []):
            if b.get("type", 1) != 0:
                continue
            bbox = b.get("bbox")
            if bbox:
                y0, y1 = bbox[1], bbox[3]
                if y1 < top_margin or y0 > bottom_margin:
                    continue
            for line in b.get("lines", []):
                line_text = ""
                for s in line.get("spans", []):
                    size = round(s.get("size", 0), 1)
                    if size >= main_font_size * 0.7:
                        line_text += s.get("text", "")
                line_text = line_text.strip()
                if line_text:
                    extracted_lines.append(line_text)

    doc.close()
    raw_text = "\n".join(extracted_lines)
    print(f"[PDF] {len(extracted_lines)} líneas extraídas.")
    return clean_text_for_tts(raw_text)


def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    """Divide texto en chunks en límites de oración."""
    chunks = []
    while len(text) > max_chars:
        sub   = text[:max_chars]
        match = None
        for m in re.finditer(r'[.!?]\s+', sub):
            match = m
        split_idx = match.end() if match else (sub.rfind(' ') or max_chars)
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
    if text:
        chunks.append(text)
    return chunks


def sanitize_filename(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name).strip()
    slug = re.sub(r"[\s]+", "_", slug)
    return slug[:80] or "libro"


def _split_for_tts(text: str, max_chars: int = 1200) -> list[str]:
    """Divide en segmentos pequeños para evitar que edge-tts corte audio."""
    text = (text or "").strip()
    if not text:
        return []

    sentences = re.findall(r'[^.!?]*[.!?]+|\S[^.!?]*$', text)
    segments: list[str] = []
    current = ""

    def flush():
        nonlocal current
        if current.strip():
            segments.append(current.strip())
        current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_chars:
            flush()
            buf = ""
            for w in s.split(' '):
                if len(buf) + len(w) + 1 > max_chars:
                    if buf:
                        segments.append(buf.strip())
                    buf = w
                else:
                    buf = f"{buf} {w}".strip()
            if buf:
                current = buf
            continue
        if len(current) + len(s) + 1 > max_chars:
            flush()
            current = s
        else:
            current = f"{current} {s}".strip()

    flush()
    return [seg for seg in segments if seg]


async def _edge_tts_bytes_and_words(text: str, voice: str):
    """Genera audio y captura los tiempos de cada palabra.
    Robusto a cambios de formato de edge-tts: acepta chunks como dict u objeto,
    y trata como 'palabra' cualquier metadato con texto + offset (WordBoundary,
    SentenceBoundary, etc.). Devuelve (audio_bytes, words) con
    words = [{"w":str,"s":ms,"e":ms}, ...] relativos al inicio del segmento."""
    communicate = edge_tts.Communicate(text, voice)
    audio = bytearray()
    words = []
    type_counts = {}

    async for chunk in communicate.stream():
        if isinstance(chunk, dict):
            ctype = chunk.get("type")
            def get(k, d=None, _c=chunk): return _c.get(k, d)
        else:
            ctype = getattr(chunk, "type", None)
            def get(k, d=None, _c=chunk): return getattr(_c, k, d)

        type_counts[ctype] = type_counts.get(ctype, 0) + 1

        if ctype == "audio":
            data = get("data")
            if data:
                audio.extend(data)
            continue

        # Cualquier metadato con texto y offset lo tratamos como palabra.
        txt = get("text")
        offset = get("offset")
        if txt and offset is not None:
            try:
                start_ms = float(offset) / 10000.0            # ticks de 100 ns -> ms
                dur_ms   = float(get("duration", 0) or 0) / 10000.0
                words.append({"w": str(txt), "s": start_ms, "e": start_ms + dur_ms})
            except Exception:
                pass

    if not words:
        # Diagnóstico: qué tipos de chunk emitió edge-tts (para ver el formato real)
        print(f"[TTS] Sin tiempos de palabra. Tipos de chunk vistos: {type_counts}", flush=True)

    return bytes(audio), words


def _split_entry_to_words(text, s, e):
    """Divide un tramo de tiempo (frase o palabra) en palabras individuales,
    repartiendo [s, e] proporcional al largo de cada palabra. Así el resaltado
    avanza palabra por palabra aunque edge-tts entregue límites por frase."""
    parts = str(text).split()
    if len(parts) <= 1:
        return [{"w": str(text).strip(), "s": int(s), "e": int(e)}]
    total = sum(len(p) for p in parts) or 1
    out = []
    cur = float(s)
    span = max(0.0, float(e) - float(s))
    for p in parts:
        frac = len(p) / total
        w_end = cur + span * frac
        out.append({"w": p, "s": int(cur), "e": int(w_end)})
        cur = w_end
    return out


async def text_to_mp3(text: str, output_path: Path, voice: str = "es-MX-JorgeNeural",
                      timing_path: Path | None = None):
    """Genera MP3 completo con reintentos y fallback a gTTS por segmento.
    Si timing_path se indica, guarda un JSON con los tiempos de cada palabra
    (para el resaltado sincronizado tipo karaoke en la app)."""
    segments = _split_for_tts(text)
    if not segments:
        segments = [(text or ".").strip() or "."]

    out = bytearray()
    timings = []
    base_ms = 0.0   # desplazamiento acumulado por segmentos previos

    for seg in segments:
        min_expected = max(800, len(seg) * 8)
        seg_bytes = b""
        seg_words = []

        for attempt in range(3):
            try:
                seg_bytes, seg_words = await _edge_tts_bytes_and_words(seg, voice)
            except Exception as e:
                print(f"[TTS] edge-tts error (intento {attempt + 1}/3): {e}")
                seg_bytes, seg_words = b"", []
            if len(seg_bytes) >= min_expected:
                break
            print(f"[TTS] Segmento muy corto ({len(seg_bytes)}B < {min_expected}B); reintento {attempt + 1}/3")
            await asyncio.sleep(0.4)

        if len(seg_bytes) < min_expected:
            print(f"[TTS] Fallback a gTTS para segmento (len={len(seg)}).")
            def generate_gtts_bytes():
                import io
                buf = io.BytesIO()
                gTTS(text=seg, lang="es", tld="com.mx").write_to_fp(buf)
                return buf.getvalue()
            try:
                seg_bytes = await asyncio.to_thread(generate_gtts_bytes)
                seg_words = []   # gTTS no entrega tiempos de palabra
            except Exception as e:
                print(f"[TTS] gTTS fallback también falló: {e}")
                seg_bytes, seg_words = b"", []

        # Acumular tiempos desplazados por la duración de segmentos anteriores,
        # dividiendo cada tramo (frase) en palabras individuales.
        for w in seg_words:
            for ww in _split_entry_to_words(w["w"], w["s"] + base_ms, w["e"] + base_ms):
                timings.append(ww)
        if seg_words:
            base_ms += seg_words[-1]["e"] + 120.0    # pequeño gap entre segmentos
        else:
            base_ms += max(600.0, len(seg) * 55.0)   # estimación si no hubo tiempos

        out.extend(seg_bytes)

    if not out:
        raise RuntimeError("No se pudo generar audio (TTS vacío).")

    with open(output_path, "wb") as f:
        f.write(out)

    if timing_path is not None:
        try:
            with open(timing_path, "w", encoding="utf-8") as f:
                json.dump(timings, f, ensure_ascii=False)
        except Exception as e:
            print(f"[TTS] No se pudo escribir el archivo de tiempos: {e}")


# ---------------------------------------------------------------------------
# Helper: verificar sesión Appwrite (async, no bloquea el event loop)
# ---------------------------------------------------------------------------
async def _verify_appwrite_session(session_id: str) -> str:
    """
    Llama a Appwrite con httpx async y retorna el userId.
    Lanza HTTPException 401 si la sesión es inválida.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{APPWRITE_ENDPOINT}/account",
                headers={
                    "X-Appwrite-Project": APPWRITE_PROJECT_ID,
                    "Cookie": f"a_session_{APPWRITE_PROJECT_ID}={session_id}",
                }
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Error verificando sesión: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    user_id = resp.json().get("$id", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="No se pudo obtener el userId de la sesión")
    return user_id


# ---------------------------------------------------------------------------
# Propiedad y visibilidad de libros
#
# visibility = "catalog"  -> dominio público / CC. Lo ve todo el mundo.
# visibility = "private"  -> subido por un usuario. SOLO su propietario.
#
# Los libros sin el campo (los de antes de esta versión) se tratan como
# "catalog" para no romper el catálogo existente. La migración de los que
# subieron usuarios se hace marcándolos como private en Appwrite.
# ---------------------------------------------------------------------------

_BOOK_META_CACHE: dict = {}


async def _get_book_meta(book_id: str):
    """Devuelve {owner_id, visibility, doc_id} o None. Cacheado en memoria."""
    if book_id in _BOOK_META_CACHE:
        return _BOOK_META_CACHE[book_id]
    try:
        docs = await _appwrite_list_documents(
            "global_books",
            queries=[{"method": "equal", "attribute": "book_id", "values": [book_id]}]
        )
    except Exception as e:
        print(f"[Acceso] Error consultando {book_id}: {e}", flush=True)
        return None
    if not docs:
        return None
    d = docs[0]
    meta = {
        "owner_id":   d.get("added_by") or "",
        "visibility": d.get("visibility") or "catalog",
        "doc_id":     d.get("$id"),
    }
    _BOOK_META_CACHE[book_id] = meta
    return meta


def _invalidate_book_meta(book_id: str) -> None:
    _BOOK_META_CACHE.pop(book_id, None)


async def _user_from_header(authorization: str):
    """userId si viene un Bearer válido, None si no viene cabecera."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return await _verify_appwrite_session(authorization.split(" ", 1)[1])


async def _assert_can_read(book_id: str, authorization: str):
    """
    Deja pasar si el libro es de catálogo. Si es privado, exige sesión válida
    y que el solicitante sea el propietario. Devuelve el userId o None.
    """
    meta = await _get_book_meta(book_id)
    if meta is None or meta["visibility"] != "private":
        return None
    user_id = await _user_from_header(authorization)
    if user_id is None:
        raise HTTPException(status_code=401,
                            detail="Este documento es privado. Inicia sesión.")
    if user_id != meta["owner_id"]:
        raise HTTPException(status_code=403,
                            detail="No tienes acceso a este documento.")
    return user_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Keep-alive para Cloud Scheduler (ping cada 5 min)."""
    return {"status": "ok", "message": "LibrisAudio Backend activo en Google Cloud Run"}


async def _appwrite_list_documents(collection: str, queries=None):
    """Lista documentos vía la API REST de Appwrite (JSON predecible,
    independiente de la versión del SDK de Python).
    `queries` es una lista de dicts en formato de query de Appwrite, p.ej.
    {"method": "limit", "values": [500]}."""
    url = f"{APPWRITE_ENDPOINT}/databases/{APPWRITE_DB_ID}/collections/{collection}/documents"
    params = []
    for q in (queries or []):
        params.append(("queries[]", json.dumps(q)))
    headers = {
        "X-Appwrite-Project": APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": APPWRITE_API_KEY or "",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json().get("documents", [])


def _appwrite_headers():
    return {
        "X-Appwrite-Project": APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": APPWRITE_API_KEY or "",
        "Content-Type": "application/json",
    }


async def _appwrite_create_document(collection: str, data: dict):
    url = f"{APPWRITE_ENDPOINT}/databases/{APPWRITE_DB_ID}/collections/{collection}/documents"
    payload = {"documentId": uuid.uuid4().hex, "data": data}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload, headers=_appwrite_headers())
        r.raise_for_status()
        return r.json()


async def _appwrite_update_document(collection: str, doc_id: str, data: dict):
    url = f"{APPWRITE_ENDPOINT}/databases/{APPWRITE_DB_ID}/collections/{collection}/documents/{doc_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(url, json={"data": data}, headers=_appwrite_headers())
        r.raise_for_status()
        return r.json()


@app.get("/api/books")
async def get_all_books(authorization: str = Header(default=None)):
    """
    Devuelve el catálogo público MÁS los documentos privados del usuario que
    llama. Sin sesión, solo catálogo. Los documentos de otros usuarios no se
    listan nunca.
    """
    requester = None
    try:
        requester = await _user_from_header(authorization)
    except HTTPException:
        requester = None   # sesión caducada: se sirve solo el catálogo

    books = []
    try:
        documents = await _appwrite_list_documents(
            "global_books",
            queries=[{"method": "limit", "values": [500]}]
        )
        for doc in documents:
            visibility = doc.get("visibility") or "catalog"
            if visibility == "private" and doc.get("added_by") != requester:
                continue
            books.append({
                "id":         doc.get("$id") or doc.get("book_id"),
                "book_id":    doc.get("book_id"),
                "title":      doc.get("title", "Sin título"),
                "author":     doc.get("author", "Autor Desconocido"),
                "parts_count":doc.get("parts_count", 1),
                "category":   doc.get("category", "General"),
                "cover_url":  doc.get("cover_url", ""),
                "added_by":   doc.get("added_by", ""),
            })
    except Exception as ex:
        print(f"[Books] Error listando desde Appwrite: {ex}")

    if not books:
        books = [
            {
                "id": "1", "book_id": "9780140449136",
                "title": "La Odisea", "author": "Homero",
                "parts_count": 5, "category": "Clásicos",
                "cover_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop",
                "added_by": "Libris"
            },
            {
                "id": "2", "book_id": "9788437604947",
                "title": "Don Quijote de la Mancha", "author": "Miguel de Cervantes",
                "parts_count": 8, "category": "Ficción",
                "cover_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300&h=400&fit=crop",
                "added_by": "Libris"
            }
        ]
    return books


@app.get("/api/tts-sample")
async def get_tts_sample(voice: str = "es-MX-JorgeNeural"):
    """Genera y cachea una muestra de voz corta."""
    safe_voice  = sanitize_filename(voice)
    sample_path = AUDIO_DIR / f"sample_{safe_voice}.mp3"
    if not sample_path.exists():
        try:
            await text_to_mp3("Hola, esta es una pequeña muestra de mi voz.", sample_path, voice=voice)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"No se pudo generar la muestra: {exc}")
    return FileResponse(sample_path, media_type="audio/mpeg")


@app.post("/api/upload-pdf")
async def upload_pdf(
    file:     UploadFile = File(...),
    title:    str        = Form(None),
    category: str        = Form("General"),
    added_by: str        = Form("upload"),   # ignorado: se toma del token
    authorization: str   = Header(default=None),
):
    print(f"[Upload] Recibiendo: {file.filename}")
    # El propietario SIEMPRE sale de la sesión verificada. El campo del
    # formulario era falsificable: cualquiera podía atribuirse un documento
    # ajeno o negar el propio.
    owner_id = await _user_from_header(authorization)
    if owner_id is None:
        raise HTTPException(status_code=401,
                            detail="Debes iniciar sesión para subir documentos.")
    try:
        if not R2_ENDPOINT_URL:
            raise HTTPException(status_code=500, detail="Cloudflare R2 no configurado")
        if not file.filename:
            raise HTTPException(status_code=400, detail="Falta el nombre del archivo.")

        pdf_bytes = await file.read()

        # META 1 — normalizador universal. Todo formato (y en META 2 también el
        # OCR) desemboca en la misma estructura Documento.
        try:
            documento = extraer_documento(pdf_bytes, file.filename, title)
        except DocumentoProtegido as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except FormatoNoSoportado as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=422,
                                detail=f"No se pudo leer el archivo: {exc}")

        if documento.necesita_ocr:
            # El OCR ya corrió y no sacó nada legible (o no está instalado).
            raise HTTPException(
                status_code=422,
                detail=documento.aviso or
                       "Este documento parece escaneado y no se pudo reconocer su texto. "
                       "Prueba con un escaneo más nítido.",
            )

        text  = documento.texto
        title = documento.titulo
        if not text.strip():
            raise HTTPException(status_code=422,
                                detail="No se pudo extraer texto del archivo.")

        chunks  = chunk_text(text, max_chars=3800)
        if not chunks:
            raise HTTPException(status_code=422, detail="No se pudo extraer texto suficiente.")

        book_id = uuid.uuid4().hex[:12]

        # Portada
        cover_url = None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype=documento.formato)
            if len(doc) > 0:
                pix       = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                cover_key = f"{book_id}/cover.png"
                await asyncio.to_thread(r2_upload, cover_key, pix.tobytes("png"), "image/png")
                cover_url = r2_public_url(cover_key)
                print(f"[Upload] Portada subida: {cover_key}")
            doc.close()
        except Exception as e:
            print(f"[Upload] Error extrayendo portada: {e}")

        # Partes de texto
        async def upload_chunk(i: int, chunk: str):
            key = f"{book_id}/text/part_{i}.txt"
            await asyncio.to_thread(r2_upload, key, chunk.encode("utf-8"), "text/plain; charset=utf-8")

        await asyncio.gather(*[upload_chunk(i, c) for i, c in enumerate(chunks)])
        print(f"[Upload] {len(chunks)} partes subidas a R2 para {book_id}")

        # Índice de capítulos (del TOC real del EPUB/MOBI/FB2, o heurístico en PDF)
        try:
            indice = {
                "formato":   documento.formato,
                "capitulos": documento.indice,
                "total_caracteres": len(text),
            }
            await asyncio.to_thread(
                r2_upload, f"{book_id}/index.json",
                json.dumps(indice, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            print(f"[Upload] Índice con {len(documento.capitulos)} capítulos")
        except Exception as e:
            print(f"[Upload] Warning índice: {e}")

        # Registrar en Appwrite
        try:
            appwrite_db.create_document(
                APPWRITE_DB_ID, "global_books",
                document_id=uuid.uuid4().hex,
                data={
                    "book_id":    book_id,
                    "title":      title,
                    "category":   category,
                    "added_by":   owner_id,
                    "visibility": "private",   # nunca al catálogo público
                    "cover_url":  cover_url or "",
                    "parts_count": len(chunks),
                }
            )
            print(f"[Upload] Libro registrado en Appwrite: {book_id}")
        except Exception as e:
            print(f"[Upload] Error registrando en Appwrite: {e}")

        return JSONResponse({
            "title":      title,
            "bookId":     book_id,
            "partsCount": len(chunks),
            "coverUrl":   cover_url,
            "format":     documento.formato,
            "chapters":   len(documento.capitulos),
            "notice":     documento.aviso,
        })

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        print(f"[Upload Error] {type(exc).__name__}: {exc}")
        return JSONResponse(status_code=500, content={"detail": f"Error interno: {str(exc)}"})


@app.get("/api/audio/{book_id}/{part_index}")
async def get_book_audio(book_id: str, part_index: int, voice: str = "es-MX-JorgeNeural",
                         authorization: str = Header(default=None)):
    """Motor JIT: genera y cachea MP3 en R2. Streamea directamente al cliente."""
    await _assert_can_read(book_id, authorization)
    if not R2_ENDPOINT_URL:
        raise HTTPException(status_code=500, detail="Cloudflare R2 no configurado")

    safe_voice = sanitize_filename(voice)
    mp3_key    = f"{book_id}/audio/part_{part_index}_{safe_voice}.mp3"

    mp3_exists = await asyncio.to_thread(r2_exists, mp3_key)
    if not mp3_exists:
        txt_key = f"{book_id}/text/part_{part_index}.txt"
        try:
            txt_bytes = await asyncio.to_thread(r2_download, txt_key)
            text      = txt_bytes.decode("utf-8")
        except Exception:
            raise HTTPException(status_code=404, detail="Parte de texto no encontrada en R2")

        print(f"[Audio] Generando MP3: {mp3_key}")
        local_mp3    = Path(f"/tmp/{book_id}_part_{part_index}_{safe_voice}.mp3")
        local_timing = Path(f"/tmp/{book_id}_part_{part_index}_{safe_voice}.json")
        timing_key   = f"{book_id}/timing/part_{part_index}_{safe_voice}_v3.json"
        try:
            await text_to_mp3(text, local_mp3, voice=voice, timing_path=local_timing)
        except Exception as exc:
            import traceback; traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error al generar audio: {exc}")

        try:
            with open(local_mp3, "rb") as f:
                await asyncio.to_thread(r2_upload, mp3_key, f.read(), "audio/mpeg")
            # Subir también los tiempos de palabra (karaoke)
            if local_timing.exists():
                with open(local_timing, "rb") as f:
                    await asyncio.to_thread(r2_upload, timing_key, f.read(), "application/json")
        except Exception as e:
            print(f"[Audio] Error subiendo a R2: {e}")
        finally:
            for p in (local_mp3, local_timing):
                try:
                    p.unlink()
                except Exception:
                    pass

    try:
        def stream_r2():
            obj = get_r2().get_object(Bucket=R2_BUCKET, Key=mp3_key)
            return obj["Body"], obj["ContentLength"]

        body_stream, content_length = await asyncio.to_thread(stream_r2)
        return StreamingResponse(
            body_stream,
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(content_length),
                "Accept-Ranges":  "bytes",
                "Cache-Control":  "public, max-age=31536000, immutable",
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al transmitir audio: {exc}")


# ---------------------------------------------------------------------------
# Tiempos de palabra (para resaltado sincronizado / karaoke en la app)
# ---------------------------------------------------------------------------

@app.get("/api/timing/{book_id}/{part_index}")
async def get_book_timing(book_id: str, part_index: int, voice: str = "es-MX-JorgeNeural",
                          authorization: str = Header(default=None)):
    await _assert_can_read(book_id, authorization)
    """Devuelve [{"w":palabra,"s":inicio_ms,"e":fin_ms}, ...] para resaltar
    cada palabra mientras suena el audio. Genera el JSON (y el MP3) si falta."""
    if not R2_ENDPOINT_URL:
        raise HTTPException(status_code=500, detail="Cloudflare R2 no configurado")

    safe_voice = sanitize_filename(voice)
    timing_key = f"{book_id}/timing/part_{part_index}_{safe_voice}_v3.json"

    exists = await asyncio.to_thread(r2_exists, timing_key)
    if not exists:
        txt_key = f"{book_id}/text/part_{part_index}.txt"
        try:
            txt_bytes = await asyncio.to_thread(r2_download, txt_key)
            text = txt_bytes.decode("utf-8")
        except Exception:
            raise HTTPException(status_code=404, detail="Parte de texto no encontrada en R2")

        local_mp3    = Path(f"/tmp/{book_id}_t{part_index}_{safe_voice}.mp3")
        local_timing = Path(f"/tmp/{book_id}_t{part_index}_{safe_voice}.json")
        try:
            await text_to_mp3(text, local_mp3, voice=voice, timing_path=local_timing)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error generando tiempos: {exc}")

        mp3_key = f"{book_id}/audio/part_{part_index}_{safe_voice}.mp3"
        try:
            if not await asyncio.to_thread(r2_exists, mp3_key):
                with open(local_mp3, "rb") as f:
                    await asyncio.to_thread(r2_upload, mp3_key, f.read(), "audio/mpeg")
            with open(local_timing, "rb") as f:
                await asyncio.to_thread(r2_upload, timing_key, f.read(), "application/json")
        except Exception as e:
            print(f"[Timing] Error subiendo a R2: {e}")
        finally:
            for p in (local_mp3, local_timing):
                try:
                    p.unlink()
                except Exception:
                    pass

    try:
        data = await asyncio.to_thread(r2_download, timing_key)
        return JSONResponse(content=json.loads(data.decode("utf-8")))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al leer los tiempos: {exc}")


# ---------------------------------------------------------------------------
# Texto de una parte (para VirtualBookFrame / modo lectura en la app Android)
# ---------------------------------------------------------------------------

@app.get("/api/text/{book_id}/{part_index}")
async def get_book_text(book_id: str, part_index: int,
                        authorization: str = Header(default=None)):
    """
    Devuelve el texto plano de una parte del libro desde Cloudflare R2.
    El catálogo público sigue abierto; los documentos privados exigen sesión
    y propiedad.
    """
    private = await _assert_can_read(book_id, authorization) is not None
    if not R2_ENDPOINT_URL:
        raise HTTPException(status_code=500, detail="Cloudflare R2 no configurado")

    txt_key = f"{book_id}/text/part_{part_index}.txt"
    try:
        txt_bytes = await asyncio.to_thread(r2_download, txt_key)
        text = txt_bytes.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Texto no encontrado para parte {part_index}")

    return PlainTextResponse(content=text, headers={
        "Cache-Control": "private, no-store" if private else "public, max-age=3600",
    })


# ---------------------------------------------------------------------------
# Book ownership — DELETE y PATCH (solo el uploader puede llamarlos)
# ---------------------------------------------------------------------------

@app.delete("/api/books/{book_id_hex}")
async def delete_book(book_id_hex: str, authorization: str = Header(default=None)):
    """
    Solo el propietario puede eliminar un libro.
    Auth: Authorization: Bearer <appwrite_session_id>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    session_id = authorization.split(" ", 1)[1]
    user_id    = await _verify_appwrite_session(session_id)

    # Verificar propiedad en Appwrite
    try:
        docs = await _appwrite_list_documents(
            "global_books",
            queries=[{"method": "equal", "attribute": "book_id", "values": [book_id_hex]}]
        )
        if not docs:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        book_doc = docs[0]
        if book_doc.get("added_by") != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este libro")
        doc_id = book_doc.get("$id")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando propiedad: {e}")

    # Eliminar archivos de R2
    try:
        all_keys = []
        for prefix in [f"{book_id_hex}/text/", f"{book_id_hex}/audio/", f"{book_id_hex}/"]:
            try:
                keys = await asyncio.to_thread(r2_list_prefix, prefix)
                all_keys.extend(keys)
            except Exception:
                pass
        if all_keys:
            await asyncio.to_thread(r2_delete, list(set(all_keys)))
        print(f"[Delete] {len(all_keys)} archivos eliminados de R2 para {book_id_hex}")
    except Exception as e:
        print(f"[Delete] Warning R2 cleanup: {e}")

    # Eliminar de Appwrite
    try:
        appwrite_db.delete_document(APPWRITE_DB_ID, "global_books", doc_id)
    except Exception as e:
        print(f"[Delete] Warning Appwrite delete: {e}")

    _invalidate_book_meta(book_id_hex)
    return {"status": "deleted", "book_id": book_id_hex}


@app.get("/api/export-mp3/{book_id}")
async def export_mp3(book_id: str, voice: str = "es-MX-JorgeNeural",
                     authorization: str = Header(default=None)):
    """
    META 3.6 — descarga el libro entero como un solo MP3.

    Une las partes YA generadas y cacheadas en R2. No genera nada nuevo a
    propósito: un libro largo tardaría más que el timeout de Cloud Run y
    dejaría al usuario esperando sin respuesta. Si faltan partes, se dice
    cuántas y el cliente las genera reproduciéndolas o descargándolas.
    """
    await _assert_can_read(book_id, authorization)

    safe_voice = sanitize_filename(voice)
    claves = await asyncio.to_thread(r2_list_prefix, f"{book_id}/audio/")
    partes = []
    for k in claves:
        m = re.search(rf"part_(\d+)_{re.escape(safe_voice)}\.mp3$", k)
        if m:
            partes.append((int(m.group(1)), k))
    partes.sort()

    if not partes:
        raise HTTPException(
            status_code=409,
            detail="Todavía no hay audio generado para este libro con esa voz. "
                   "Escúchalo o descárgalo primero y vuelve a intentarlo.",
        )

    destino = f"{book_id}/export/completo_{safe_voice}.mp3"
    if not await asyncio.to_thread(r2_exists, destino):
        import subprocess, tempfile, shutil
        tmp = Path(tempfile.mkdtemp(prefix="export_"))
        try:
            lista = tmp / "lista.txt"
            with open(lista, "w", encoding="utf-8") as f:
                for idx, clave in partes:
                    local = tmp / f"p{idx:05}.mp3"
                    local.write_bytes(await asyncio.to_thread(r2_download, clave))
                    f.write(f"file '{local.as_posix()}'\n")
            salida = tmp / "completo.mp3"
            # ffmpeg ya está en la imagen (lo instala el Dockerfile)
            proc = await asyncio.to_thread(
                subprocess.run,
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(lista), "-c", "copy", str(salida)],
                capture_output=True)
            if proc.returncode != 0 or not salida.exists():
                raise HTTPException(status_code=500,
                                    detail="No se pudo unir el audio.")
            await asyncio.to_thread(r2_upload, destino,
                                    salida.read_bytes(), "audio/mpeg")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    return {
        "url": r2_public_url(destino),
        "parts": len(partes),
        "voice": voice,
    }


@app.get("/api/formats")
def supported_formats():
    """Formatos que acepta la subida. La app lo usa para filtrar el selector."""
    return {"formats": FORMATOS_SOPORTADOS}


@app.get("/api/index/{book_id}")
async def get_book_index(book_id: str, authorization: str = Header(default=None)):
    """Índice de capítulos del documento. 404 si se subió antes de la META 1."""
    await _assert_can_read(book_id, authorization)
    try:
        raw = await asyncio.to_thread(r2_download, f"{book_id}/index.json")
        return JSONResponse(content=json.loads(raw.decode("utf-8")))
    except Exception:
        raise HTTPException(status_code=404, detail="Este documento no tiene índice.")


# ---------------------------------------------------------------------------
# Biblioteca del usuario — quitar del historial (NO borra el libro)
# ---------------------------------------------------------------------------

# Claves que la app guarda por libro en el estado del usuario.
_LIBRARY_KEY_PREFIXES = ("part_", "pct_", "pos_")


@app.delete("/api/library/{book_id_hex}")
async def remove_from_library(book_id_hex: str, authorization: str = Header(default=None)):
    """
    Quita un libro de la biblioteca/historial del usuario. El libro sigue
    existiendo: si vuelve a abrirlo, reaparece. Vale para CUALQUIER libro,
    también los del catálogo. No borra contenido.
    """
    user_id = await _user_from_header(authorization)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    try:
        docs = await _appwrite_list_documents(
            "user_state",
            queries=[{"method": "equal", "attribute": "user_id", "values": [user_id]}]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el estado: {e}")

    if not docs:
        return {"status": "ok", "book_id": book_id_hex, "removed": 0}

    doc   = docs[0]
    state = json.loads(doc.get("data") or "{}")

    removed = 0
    for key in [k for k in list(state.keys())
                if k in (p + book_id_hex for p in _LIBRARY_KEY_PREFIXES)]:
        state.pop(key, None)
        removed += 1

    started = state.get("started_books")
    if isinstance(started, list) and book_id_hex in started:
        state["started_books"] = [b for b in started if b != book_id_hex]
        removed += 1

    if state.get("last_book_id") == book_id_hex:
        state.pop("last_book_id", None)
        removed += 1

    try:
        await _appwrite_update_document("user_state", doc.get("$id"),
                                        {"data": json.dumps(state, ensure_ascii=False)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando el estado: {e}")

    return {"status": "ok", "book_id": book_id_hex, "removed": removed}


@app.patch("/api/books/{book_id_hex}")
async def patch_book(
    book_id_hex:   str  = ...,
    authorization: str  = Header(default=None),
    body:          dict = Body(default={}),
):
    """
    Solo el propietario puede editar título y/o categoría.
    Auth: Authorization: Bearer <appwrite_session_id>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    session_id = authorization.split(" ", 1)[1]
    user_id    = await _verify_appwrite_session(session_id)

    # Verificar propiedad en Appwrite
    try:
        docs = await _appwrite_list_documents(
            "global_books",
            queries=[{"method": "equal", "attribute": "book_id", "values": [book_id_hex]}]
        )
        if not docs:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        book_doc = docs[0]
        if book_doc.get("added_by") != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para editar este libro")
        doc_id = book_doc.get("$id")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando propiedad: {e}")

    # Aplicar cambios
    update_data = {}
    if "title" in body and str(body["title"]).strip():
        update_data["title"]    = str(body["title"]).strip()
    if "category" in body and str(body["category"]).strip():
        update_data["category"] = str(body["category"]).strip()

    if not update_data:
        return {"status": "no_changes"}

    try:
        appwrite_db.update_document(APPWRITE_DB_ID, "global_books", doc_id, data=update_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando libro: {e}")

    return {"status": "updated", "book_id": book_id_hex, "changes": update_data}


# ---------------------------------------------------------------------------
# Chat IA sobre el libro (OpenRouter cascada gratuita)
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role:    str
    content: str


class ChatBookRequest(BaseModel):
    book_id:            str
    part_index:         int
    user_message:       str
    history:            List[ChatMessage] = []
    user_openrouter_key: Optional[str]   = None
    enforce_free_only:  bool             = True


@app.post("/api/chat-book")
async def chat_with_book(req: ChatBookRequest):
    """Chat IA sobre el libro — OpenRouter cascada gratuita."""
    part_text = ""
    try:
        data      = r2_download(f"{req.book_id}/text/part_{req.part_index}.txt")
        part_text = data.decode("utf-8")
    except Exception as e:
        print(f"[Chat] No se pudo cargar el texto de la parte: {e}")

    system_prompt = (
        "Eres el asistente inteligente de Libris Audio (QuantumLabs / HarD P.). "
        "Ayuda al oyente a comprender el libro: explica conceptos, resume personajes, responde dudas. "
        "Responde de forma clara y amable en español.\n\n"
        f"--- TEXTO PARTE {req.part_index + 1} ---\n{part_text[:4000]}\n--- FIN ---"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in (req.history or []):
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.user_message})

    openrouter_key = (req.user_openrouter_key and req.user_openrouter_key.strip()) or \
                     os.environ.get("OPENROUTER_API_KEY", "")

    if not openrouter_key:
        return JSONResponse({"reply": "Configura OPENROUTER_API_KEY para activar el chat IA."})

    cascade = [
        "openrouter/free",
        "deepseek/deepseek-r1:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "google/gemma-2-9b-it:free",
    ]
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "HTTP-Referer":  "https://libris-audio.vercel.app",
        "X-Title":       "Libris Audio - QuantumLabs",
        "Content-Type":  "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in cascade:
            if req.enforce_free_only and not (model.endswith(":free") or model == "openrouter/free"):
                continue
            try:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": messages, "max_tokens": 500, "temperature": 0.7},
                )
                if res.status_code == 200:
                    reply = res.json()["choices"][0]["message"]["content"]
                    return JSONResponse({"reply": reply, "model_used": model})
            except Exception as ex:
                print(f"[Chat] Modelo {model} falló: {ex}")
                continue

    return JSONResponse({"reply": "La IA no está disponible en este momento. Inténtalo de nuevo."})


# ---------------------------------------------------------------------------
# Asistente de voz A2 — interpreta lenguaje natural → acción (OpenRouter)
# ---------------------------------------------------------------------------

class VoiceCommandRequest(BaseModel):
    transcript:          str
    current_part:        int = 0
    parts_count:         int = 1
    user_openrouter_key: Optional[str] = None
    enforce_free_only:   bool          = True


def _extract_json_action(text: str):
    """Extrae el primer objeto JSON {...} con 'action' del texto del LLM."""
    try:
        start = text.find("{")
        end   = text.rfind("}")
        if start >= 0 and end > start:
            obj = json.loads(text[start:end + 1])
            if isinstance(obj, dict) and "action" in obj:
                return obj
    except Exception:
        pass
    return None


@app.post("/api/voice-command")
async def voice_command(req: VoiceCommandRequest):
    """Convierte una frase de voz (ES/EN) en una acción de reproducción JSON."""
    system_prompt = (
        "Eres el intérprete de comandos de voz de una app de audiolibros. "
        f"El usuario escucha un libro (parte actual {req.current_part + 1} de {req.parts_count}). "
        "Convierte su frase (en español o inglés) en UNA sola acción. "
        "Responde SOLO con un objeto JSON válido, sin texto extra:\n"
        '{"action": "<play|pause|next|prev|rewind|forward|goto|speed_up|speed_down|speed_normal|bookmark|where|stop|unknown>", "seconds": <entero opcional>, "part": <entero 1-based opcional>}\n'
        "Usa 'goto' con 'part' para ir a un capítulo/parte concreto; 'rewind'/'forward' con 'seconds'; "
        "si la frase no corresponde a ninguna acción, usa \"unknown\"."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": req.transcript},
    ]

    openrouter_key = (req.user_openrouter_key and req.user_openrouter_key.strip()) or \
                     os.environ.get("OPENROUTER_API_KEY", "")
    if not openrouter_key:
        return JSONResponse({"action": "unknown"})

    cascade = [
        "openrouter/free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-2-9b-it:free",
        "qwen/qwen-2.5-coder-32b-instruct:free",
    ]
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "HTTP-Referer":  "https://libris-audio.vercel.app",
        "X-Title":       "Libris Audio - QuantumLabs",
        "Content-Type":  "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        for model in cascade:
            if req.enforce_free_only and not (model.endswith(":free") or model == "openrouter/free"):
                continue
            try:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": messages, "max_tokens": 80, "temperature": 0.0},
                )
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"]
                    action  = _extract_json_action(content)
                    if action:
                        return JSONResponse(action)
            except Exception as ex:
                print(f"[Voice] Modelo {model} falló: {ex}")
                continue

    return JSONResponse({"action": "unknown"})


# ---------------------------------------------------------------------------
# Estado del usuario en la nube (progreso + preferencias) — sincronización
# ---------------------------------------------------------------------------

@app.get("/api/user-state/{user_id}")
async def get_user_state(user_id: str):
    """Devuelve el estado del usuario (progreso, preferencias) como JSON."""
    try:
        docs = await _appwrite_list_documents(
            "user_state",
            queries=[{"method": "equal", "attribute": "user_id", "values": [user_id]}]
        )
        if docs:
            raw = docs[0].get("data") or "{}"
            return JSONResponse(content=json.loads(raw))
    except Exception as e:
        print(f"[UserState] get error: {e}", flush=True)
    return JSONResponse(content={})


@app.put("/api/user-state/{user_id}")
async def put_user_state(user_id: str, body: dict = Body(default={})):
    """Guarda (upsert) el estado del usuario."""
    data_str = json.dumps(body, ensure_ascii=False)
    try:
        docs = await _appwrite_list_documents(
            "user_state",
            queries=[{"method": "equal", "attribute": "user_id", "values": [user_id]}]
        )
        if docs:
            await _appwrite_update_document("user_state", docs[0].get("$id"), {"data": data_str})
        else:
            await _appwrite_create_document("user_state", {"user_id": user_id, "data": data_str})
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        print(f"[UserState] put error: {e}", flush=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
