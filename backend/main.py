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
try:
    import fitz  # PyMuPDF
except ImportError as ex:
    fitz = None
    print(f"Warning: PyMuPDF import note: {ex}")
import uvicorn
import httpx
from gtts import gTTS
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from appwrite.client import Client as AppwriteClient
from appwrite.services.databases import Databases as AppwriteDatabases

# ---------------------------------------------------------------------------
# Supabase — used ONLY for database (auth, global_books, user_books)
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Appwrite Database Integration (Continuous 24/7 non-pausing database)
# ---------------------------------------------------------------------------
APPWRITE_ENDPOINT   = os.environ.get("APPWRITE_ENDPOINT", "https://nyc.cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID", "6a72f5d6002eeff78bc2")
APPWRITE_API_KEY    = os.environ.get("APPWRITE_API_KEY", "standard_bb434ca194434c1144b8419ad413abd9473348e2e1eeca63e8edb257ada46c6d35166277da68a5427b6abbef0bbb632b28002dd401386de07c103efe8436a6f1a68b15f6bafe8bc07429fd366fcbdbecf616c7f7f51bab48fe2edacc1823c3f4ca500f397ca88a90b30639b12fea79369d13a018a97667f578497f594d441885")
APPWRITE_DB_ID      = os.environ.get("APPWRITE_DATABASE_ID", "libris_db")

appwrite_client = AppwriteClient()
appwrite_client.set_endpoint(APPWRITE_ENDPOINT)
appwrite_client.set_project(APPWRITE_PROJECT_ID)
appwrite_client.set_key(APPWRITE_API_KEY)

appwrite_db = AppwriteDatabases(appwrite_client)

# ---------------------------------------------------------------------------
# Cloudflare R2 — used for ALL file storage (covers, text parts, audio MP3s)
# R2 has zero egress cost vs Supabase Storage's 5 GB/month cap.
# ---------------------------------------------------------------------------
R2_ACCESS_KEY_ID     = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT_URL      = os.environ.get("R2_ENDPOINT_URL", "")
R2_BUCKET            = os.environ.get("R2_BUCKET_NAME", "libris-audio")
R2_PUBLIC_URL        = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")

_r2_client = None

def get_r2():
    """Lazy singleton for the boto3 S3 client pointing to R2."""
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
    """Upload bytes to R2."""
    get_r2().put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def r2_public_url(key: str) -> str:
    """Return the public CDN URL for a key (zero-egress cost via R2 dev URL)."""
    return f"{R2_PUBLIC_URL}/{key}"


def r2_exists(key: str) -> bool:
    """Check if a key exists — uses HeadObject (no egress cost)."""
    try:
        get_r2().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def r2_download(key: str) -> bytes:
    """Download and return raw bytes for a key."""
    obj = get_r2().get_object(Bucket=R2_BUCKET, Key=key)
    return obj["Body"].read()


def r2_delete(keys: list[str]) -> None:
    """Batch-delete a list of keys (max 1000 per call)."""
    if not keys:
        return
    get_r2().delete_objects(
        Bucket=R2_BUCKET,
        Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
    )


def r2_list_prefix(prefix: str) -> list[str]:
    """List all object keys under a given prefix."""
    paginator = get_r2().get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "static" / "audio"
BOOKS_DIR = BASE_DIR / "static" / "books"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
BOOKS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="LibrisAudio API")

# Allow the Vite dev server (port 8080) to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # More permissive for Vercel CORS
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clean_text_for_tts(raw: str) -> str:
    """
    Prepare raw PDF text for edge-tts:
    - Remove lines that are ONLY digits (page numbers)
    - Remove common PDF page-marker patterns ("Página N", "Page N", "- 2 -")
    - Collapse multiple blank lines / whitespace into a single space
    - Ensure the text ends with a period so the TTS doesn't cut off abruptly
    """
    lines = raw.splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        # Skip completely empty lines
        if not stripped:
            continue
        # Skip lines that are ONLY a number (bare page numbers: "1", "2", "42")
        if re.fullmatch(r'\d+', stripped):
            continue
        # Skip lines that end with page markers like: "Página 2", "Page 2", "www.lectulandia.com - Página 3"
        if re.search(r'(p[áa]gina|page|pág\.?)\s*\d+$', stripped, re.IGNORECASE):
            continue
        # Skip dash-wrapped page numbers: "- 2 -", "— 12 —"
        if re.fullmatch(r'[-–—\s]*\d+[-–—\s]*', stripped):
            continue
        cleaned.append(stripped)

    # Join with a single space — no blank-line pauses
    text = ' '.join(cleaned)

    # Collapse any remaining multiple spaces
    text = re.sub(r'  +', ' ', text)

    # Ensure it ends with a period
    if text and text[-1] not in '.!?':
        text += '.'

    return text.strip()

def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 1000) -> str:
    """Extrae texto limpio de los PDF usando análisis de diccionario y tamaño de fuente."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = min(len(doc), max_pages)
    
    # 1. Encontrar el tamaño de fuente dominante (main_font_size)
    font_counts = {}
    sample_pages = min(20, num_pages) # Analizamos las primeras 20 págs
    for i in range(sample_pages):
        page = doc[i]
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if b.get("type", 1) != 0: continue
            for line in b.get("lines", []):
                for s in line.get("spans", []):
                    size = round(s.get("size", 0), 1)
                    text = s.get("text", "").strip()
                    if len(text) > 2: # Solo contar palabras reales
                        font_counts[size] = font_counts.get(size, 0) + len(text)
                        
    if not font_counts:
        return ""
        
    main_font_size = max(font_counts, key=font_counts.get)
    print(f"[PDF] Font sizes detected: {font_counts}")
    print(f"[PDF] Main font size: {main_font_size}")
    
    # 2. Extraer texto filtrado
    extracted_lines = []
    
    for i in range(num_pages):
        page = doc[i]
        blocks = page.get_text("dict").get("blocks", [])
        page_height = page.rect.height
        
        # Ignorar 6% superior e inferior
        top_margin = page_height * 0.06
        bottom_margin = page_height * 0.94
        
        for b in blocks:
            if b.get("type", 1) != 0: continue # Solo texto
            
            # Ver coordenadas de bloque
            bbox = b.get("bbox")
            if bbox:
                # bbox es [x0, y0, x1, y1]
                y0, y1 = bbox[1], bbox[3]
                if y1 < top_margin or y0 > bottom_margin:
                    continue # Es un encabezado o pie de página
                    
            for line in b.get("lines", []):
                line_text = ""
                for s in line.get("spans", []):
                    size = round(s.get("size", 0), 1)
                    text = s.get("text", "")
                    
                    # Conservamos si el tamaño es razonable para ser texto del cuerpo/citas (al menos 70% del tamaño principal)
                    if size >= main_font_size * 0.7:
                        line_text += text
                
                line_text = line_text.strip()
                if line_text:
                    extracted_lines.append(line_text)

    doc.close()
    
    raw_text = "\n".join(extracted_lines)
    
    print(f"[PDF] Extracción heurística completada. {len(extracted_lines)} líneas útiles encontradas.")
    
    # 3. Lo pasamos por el limpiador básico para arreglar guiones y puntuaciones
    cleaned = clean_text_for_tts(raw_text)
    
    return cleaned

def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    """Splits text into chunks of roughly max_chars, preferably at sentence boundaries."""
    chunks = []
    while len(text) > max_chars:
        sub = text[:max_chars]
        
        # find last sentence boundary
        match = None
        for m in re.finditer(r'[.!?]\s+', sub):
            match = m
            
        if match:
            split_idx = match.end()
        else:
            # fallback to space
            split_idx = sub.rfind(' ')
            if split_idx == -1:
                split_idx = max_chars
                
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
        
    if text:
        chunks.append(text)
    return chunks

def sanitize_filename(name: str) -> str:
    """Turn any string into a safe filename slug."""
    slug = re.sub(r"[^\w\s-]", "", name).strip()
    slug = re.sub(r"[\s]+", "_", slug)
    return slug[:80] or "libro"


def _split_for_tts(text: str, max_chars: int = 1200) -> list[str]:
    """
    Split a part's text into small, sentence-based segments (<= max_chars).

    edge-tts occasionally returns INCOMPLETE audio for a single request — it
    silently drops a portion of the speech, which is exactly the "el audio se
    salta parte del texto" bug. The drop probability grows with request size,
    so we feed edge-tts small segments and stitch them back together. A drop in
    a tiny segment is both far less likely and far less damaging, and can be
    caught/retried individually.
    """
    text = (text or "").strip()
    if not text:
        return []

    # Split into sentences, keeping their terminal punctuation.
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
        # A single sentence longer than max_chars: hard-split at word boundaries.
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


async def _edge_tts_bytes(text: str, voice: str) -> bytes:
    """Stream a segment through edge-tts and return the raw MP3 bytes."""
    communicate = edge_tts.Communicate(text, voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            audio.extend(chunk["data"])
    return bytes(audio)


async def text_to_mp3(text: str, output_path: Path, voice: str = "es-MX-JorgeNeural"):
    """
    Generate a COMPLETE MP3 for a part, resilient to edge-tts silently dropping
    audio (the "skips part of the text" bug).

    Strategy:
      1. Split the part into small sentence-based segments.
      2. Generate each segment with edge-tts, retrying if the returned audio is
         empty or suspiciously short (a sign edge-tts dropped the segment).
      3. If edge-tts keeps failing for a segment, fall back to gTTS for that
         segment only — so one bad segment never loses the rest of the part.
      4. Concatenate every segment's MP3 bytes into the final file.
    """
    segments = _split_for_tts(text)
    if not segments:
        segments = [(text or ".").strip() or "."]

    out = bytearray()

    for seg in segments:
        # Conservative floor: any real speech segment produces far more than
        # this many bytes. It only trips on empty / near-empty (dropped) audio,
        # avoiding false retries on legitimately short output.
        min_expected = max(800, len(seg) * 8)
        seg_bytes = b""

        for attempt in range(3):
            try:
                seg_bytes = await _edge_tts_bytes(seg, voice)
            except Exception as e:
                print(f"[TTS] edge-tts error (attempt {attempt + 1}/3) on segment len={len(seg)}: {e}")
                seg_bytes = b""

            if len(seg_bytes) >= min_expected:
                break
            print(f"[TTS] Segment audio too short ({len(seg_bytes)}B < {min_expected}B); retry {attempt + 1}/3")
            await asyncio.sleep(0.4)

        # Per-segment fallback to gTTS if edge-tts kept returning incomplete audio.
        if len(seg_bytes) < min_expected:
            print(f"[TTS] Falling back to gTTS for one segment (len={len(seg)}).")
            def generate_gtts_bytes():
                import io
                buf = io.BytesIO()
                gTTS(text=seg, lang="es", tld="com.mx").write_to_fp(buf)
                return buf.getvalue()
            try:
                seg_bytes = await asyncio.to_thread(generate_gtts_bytes)
            except Exception as e:
                print(f"[TTS] gTTS fallback also failed for a segment: {e}")
                seg_bytes = b""

        out.extend(seg_bytes)

    if not out:
        raise RuntimeError("No se pudo generar audio para esta parte (TTS vacío).")

    with open(output_path, "wb") as f:
        f.write(out)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Endpoint ligero para el ping de Keep-Alive (UptimeRobot)."""
    return {"status": "ok", "message": "LibrisAudio Backend is awake!"}

@app.get("/api/tts-sample")
async def get_tts_sample(voice: str = "es-MX-JorgeNeural"):
    """Generates (and caches) a short voice sample to preview."""
    safe_voice = sanitize_filename(voice)
    sample_path = AUDIO_DIR / f"sample_{safe_voice}.mp3"
    
    if not sample_path.exists():
        text = "Hola, esta es una pequeña muestra de mi voz."
        try:
            await text_to_mp3(text, sample_path, voice=voice)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"No se pudo generar la muestra: {exc}")
            
    return FileResponse(sample_path, media_type="audio/mpeg")


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    print(f"Recibiendo solicitud de subida: {file.filename}")
    try:
        # ── Validate ──────────────────────────────────────────────────────────
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase no configurado en el backend")

        if not R2_ENDPOINT_URL:
            raise HTTPException(status_code=500, detail="Cloudflare R2 no configurado en el backend")

        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="El archivo PDF está vacío.")

        # ── Extract text ───────────────────────────────────────────────────────
        try:
            text = extract_text_from_pdf(pdf_bytes, max_pages=1000)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"No se pudo leer el PDF: {exc}")

        if not text:
            raise HTTPException(
                status_code=422,
                detail="Las primeras páginas del PDF no contienen texto extraíble (puede ser un PDF escaneado).",
            )

        # ── Derive title ────────────────────────────────────────────────────────
        raw_title = file.filename.rsplit(".", 1)[0]
        title = raw_title.replace("_", " ").replace("-", " ").strip() or "Libro sin título"

        # ── Chunking & Metadata ──────────────────────────────────────────────────
        chunks = chunk_text(text, max_chars=3800)
        if not chunks:
            raise HTTPException(status_code=422, detail="No se pudo extraer texto suficiente.")

        book_id = uuid.uuid4().hex[:12]

        # ── Extract Cover → upload to R2 ─────────────────────────────────────
        cover_url = None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if len(doc) > 0:
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                cover_bytes = pix.tobytes("png")
                cover_key = f"{book_id}/cover.png"
                await asyncio.to_thread(r2_upload, cover_key, cover_bytes, "image/png")
                cover_url = r2_public_url(cover_key)
                print(f"[Upload] Cover subida a R2: {cover_key}")
            doc.close()
        except Exception as e:
            print(f"[PDF] Error extracting/uploading cover: {e}")

        # ── Upload text chunks to R2 ──────────────────────────────────────────
        async def upload_chunk(i: int, chunk: str):
            key = f"{book_id}/text/part_{i}.txt"
            await asyncio.to_thread(r2_upload, key, chunk.encode("utf-8"), "text/plain; charset=utf-8")

        await asyncio.gather(*[upload_chunk(i, c) for i, c in enumerate(chunks)])
        print(f"[Upload] {len(chunks)} partes de texto subidas a R2 para {book_id}")

        print(f"Subida completada con éxito: {book_id}")
        return JSONResponse({
            "title": title,
            "bookId": book_id,
            "partsCount": len(chunks),
            "coverUrl": cover_url
        })
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        print(f"[Upload Error] {type(exc).__name__}: {exc}")
        return JSONResponse(status_code=500, content={"detail": f"Error interno en el servidor: {str(exc)}"})


@app.get("/api/clean-audio")
async def clean_audio(token: str = None):
    """
    Cleans up all generated MP3 audio files from R2 storage.
    Keeps text parts and covers — only removes cached audio to free space.
    """
    expected_token = os.environ.get("CLEANUP_TOKEN") or "libris_cleanup_default_secret_2026"
    if token != expected_token:
        raise HTTPException(status_code=403, detail="No autorizado")

    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    try:
        # 1. Obtener todos los book_ids de la base de datos
        def get_books():
            return supabase.table("global_books").select("book_id").execute()

        response = await asyncio.to_thread(get_books)
        book_ids = [row["book_id"] for row in response.data]

        all_mp3_keys = []

        # 2. Listar archivos .mp3 de cada libro en R2 (concurrente)
        async def list_audio_keys(book_id: str) -> list[str]:
            try:
                prefix = f"{book_id}/audio/"
                keys = await asyncio.to_thread(r2_list_prefix, prefix)
                return [k for k in keys if k.endswith(".mp3")]
            except Exception as e:
                print(f"[Cleanup] Error listando audios de {book_id}: {e}")
                return []

        results = await asyncio.gather(*[list_audio_keys(bid) for bid in book_ids])
        for res in results:
            all_mp3_keys.extend(res)

        # 3. Borrar en lotes de 1000 (límite de R2/S3)
        deleted_count = 0
        if all_mp3_keys:
            for i in range(0, len(all_mp3_keys), 1000):
                batch = all_mp3_keys[i:i + 1000]
                await asyncio.to_thread(r2_delete, batch)
                deleted_count += len(batch)

        return JSONResponse({
            "status": "success",
            "message": f"Se eliminaron {deleted_count} archivos de audio (.mp3) de R2",
            "files_deleted": all_mp3_keys
        })

    except Exception as e:
        print(f"[Cleanup Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error al limpiar audios: {str(e)}")


@app.get("/api/audio/{book_id}/{part_index}")
async def get_book_audio(book_id: str, part_index: int, voice: str = "es-MX-JorgeNeural"):
    """JIT Engine: Delivers audio for a specific part. Generates it if missing.

    Files are stored in Cloudflare R2 (zero egress cost).
    Streams directly through backend to ensure CORS & Range request compliance for mobile/PWA.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    safe_voice = sanitize_filename(voice)
    mp3_key = f"{book_id}/audio/part_{part_index}_{safe_voice}.mp3"

    # 1. Check if MP3 already exists in R2
    mp3_exists = await asyncio.to_thread(r2_exists, mp3_key)
    if not mp3_exists:
        # 2. Not cached — download text part from R2 to generate audio
        txt_key = f"{book_id}/text/part_{part_index}.txt"
        try:
            txt_bytes = await asyncio.to_thread(r2_download, txt_key)
            text = txt_bytes.decode("utf-8")
        except Exception:
            raise HTTPException(status_code=404, detail="Parte de texto no encontrada en R2")

        # 3. Generate MP3 locally with edge-tts
        print(f"[Audio] Generando MP3 para {mp3_key}...")
        local_mp3 = Path(f"/tmp/{book_id}_part_{part_index}_{safe_voice}.mp3")
        try:
            await text_to_mp3(text, local_mp3, voice=voice)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error al generar audio: {exc}")

        # 4. Upload generated MP3 to R2
        print(f"[Audio] Subiendo MP3 a R2: {mp3_key}")
        try:
            with open(local_mp3, "rb") as f:
                await asyncio.to_thread(r2_upload, mp3_key, f.read(), "audio/mpeg")
        except Exception as e:
            print(f"[Audio] Error subiendo MP3 a R2: {e}")
        finally:
            try:
                local_mp3.unlink()
            except Exception:
                pass

    # 5. Stream audio from R2 via StreamingResponse (preserves CORS & Range headers for mobile)
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
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=31536000, immutable",
            }
        )
    except Exception as exc:
        print(f"[Audio Error] Error streaming audio from R2: {exc}")
        raise HTTPException(status_code=500, detail=f"Error al transmitir audio: {exc}")


# ---------------------------------------------------------------------------
# Book ownership endpoints — DELETE and PATCH (only the uploader can call)
# ---------------------------------------------------------------------------

def _verify_book_owner(book_id_hex: str, user_id: str) -> dict:
    """
    Fetches the global_books record and raises 403 if the caller is not the uploader.
    Returns the full book row on success.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")
    response = supabase.table("global_books").select("*").eq("book_id", book_id_hex).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    book_row = response.data
    if book_row.get("added_by") != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este libro")
    return book_row


async def _supabase_delete_as_user(table: str, eq_field: str, eq_value: str, token: str):
    """
    Calls Supabase REST API DELETE with the user's JWT so that auth.uid() is set
    and RLS policies like 'auth.uid() = added_by' are satisfied.
    The supabase-py client uses the ANON key which leaves auth.uid() NULL.
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_KEY,
        "Prefer": "return=minimal",
    }
    async with httpx.AsyncClient() as client:
        r = await client.delete(url, params={eq_field: f"eq.{eq_value}"}, headers=headers)
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail=f"Error al eliminar de la base de datos: {r.text}")


async def _supabase_patch_as_user(table: str, eq_field: str, eq_value: str, data: dict, token: str):
    """
    Calls Supabase REST API PATCH with the user's JWT so that RLS policies are satisfied.
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    async with httpx.AsyncClient() as client:
        r = await client.patch(url, params={eq_field: f"eq.{eq_value}"}, json=data, headers=headers)
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail=f"Error al actualizar la base de datos: {r.text}")


@app.delete("/api/books/{book_id_hex}")
async def delete_book(book_id_hex: str, authorization: str = Header(default=None)):
    """
    Owner-only: Permanently deletes a book and ALL its associated files from
    Supabase Storage (texts, audios, cover). The CASCADE FK on user_books
    ensures all personal library entries are removed automatically.
    Requires: Authorization: Bearer <supabase_jwt>
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    # ── Auth: extract user from JWT ───────────────────────────────────────
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    token = authorization.split(" ", 1)[1]
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # ── Verify ownership ──────────────────────────────────────────────────
    book_row = await asyncio.to_thread(_verify_book_owner, book_id_hex, user_id)
    global_book_db_id = book_row["id"]

    # ── Delete all R2 files concurrently ─────────────────────────────────
    async def delete_r2_prefix(prefix: str):
        """List and delete all R2 objects under a prefix."""
        try:
            keys = await asyncio.to_thread(r2_list_prefix, prefix)
            if keys:
                await asyncio.to_thread(r2_delete, keys)
                print(f"[Delete] Eliminados {len(keys)} archivos de R2 bajo {prefix}")
        except Exception as e:
            print(f"[Delete] Warning: no se pudo limpiar {prefix} en R2: {e}")

    await asyncio.gather(
        delete_r2_prefix(f"{book_id_hex}/audio/"),
        delete_r2_prefix(f"{book_id_hex}/text/"),
    )
    # Cover
    try:
        await asyncio.to_thread(r2_delete, [f"{book_id_hex}/cover.png"])
    except Exception:
        pass

    # ── Delete global_books record (CASCADE removes user_books) ──────────
    # IMPORTANT: Must use user's JWT directly (not the anon-key supabase client)
    # so that RLS policies (auth.uid() = added_by) are respected.
    await _supabase_delete_as_user("global_books", "id", global_book_db_id, token)

    return {"status": "success", "message": "Libro eliminado permanentemente"}


@app.patch("/api/books/{book_id_hex}")
async def update_book(book_id_hex: str, payload: dict, authorization: str = Header(default=None)):
    """
    Owner-only: Updates a book's title and/or category.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    # ── Auth: extract user from JWT ──
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    token = authorization.split(" ", 1)[1]
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # ── Verify ownership ──
    book_row = await asyncio.to_thread(_verify_book_owner, book_id_hex, user_id)
    global_book_db_id = book_row["id"]

    # ── Update global_books record ──
    patch_data = {}
    if "title" in payload:
        patch_data["title"] = payload["title"]
    if "category" in payload:
        patch_data["category"] = payload["category"]

    if not patch_data:
        return {"status": "success", "message": "Nada que actualizar"}

    await _supabase_patch_as_user("global_books", "id", global_book_db_id, patch_data, token)

    return {"status": "success", "message": "Libro actualizado"}


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatBookRequest(BaseModel):
    book_id: str
    part_index: int
    user_message: str
    history: list[ChatMessage] = []
    user_openrouter_key: str | None = None
    enforce_free_only: bool = True

@app.post("/api/chat-book")
async def chat_with_book(req: ChatBookRequest):
    """
    OpenRouter Cascade LLM Assistant for asking questions about the book.
    Firmado por: HarD P. / QuantumLabs-by-HarDP
    """
    part_key = f"parts/{req.book_id}/part_{req.part_index}.json"
    part_text = ""
    try:
        data = r2_download(part_key)
        if data:
            part_json = json.loads(data.decode("utf-8"))
            part_text = part_json.get("text", "")
    except Exception as e:
        print(f"Could not load part text for chat: {e}")

    system_prompt = (
        "Eres el asistente inteligente de lectura e IA conversacional de Libris Audio (desarrollado por QuantumLabs / HarD P.). "
        "Tu objetivo es ayudar al oyente a comprender mejor el libro, explicar conceptos complejos, resumir personajes o responder sus dudas. "
        "Responde de forma clara, directa y amable en espa�ol.\n\n"
        f"--- TEXTO DEL CAP�TULO / PARTE ACTUAL (Parte {req.part_index + 1}) ---\n"
        f"{part_text[:4000]}\n"
        "--- FIN DEL TEXTO ---"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in (req.history or []):
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.user_message})

    openrouter_api_key = (req.user_openrouter_key and req.user_openrouter_key.strip()) or os.environ.get("OPENROUTER_API_KEY", "")
    models_cascade = [
        "openrouter/free",
        "deepseek/deepseek-r1:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

    if not openrouter_api_key:
        return JSONResponse({"reply": f"Respuesta inteligente a '{req.user_message}': El personaje y cap�tulo actual analizado por IA. (Nota: Para conectar en vivo con modelos avanzados OpenRouter, asigna OPENROUTER_API_KEY en Render)."})

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "HTTP-Referer": "https://libris-audio.vercel.app",
        "X-Title": "Libris Audio - QuantumLabs",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in models_cascade:
            if req.enforce_free_only and not (model.endswith(":free") or model == "openrouter/free"):
                continue
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    resp_data = res.json()
                    reply = resp_data["choices"][0]["message"]["content"]
                    return JSONResponse({"reply": reply, "model_used": model})
            except Exception as ex:
                print(f"Cascade model {model} failed: {ex}")
                continue

    return JSONResponse({"reply": "Lo siento, la IA no est� disponible en este momento. Int�ntalo de nuevo en unos instantes."})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)







