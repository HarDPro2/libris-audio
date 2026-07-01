import asyncio
import os
import re
import uuid
import json
from pathlib import Path

import edge_tts
import fitz  # PyMuPDF
import uvicorn
import httpx
from gtts import gTTS
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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


async def text_to_mp3(text: str, output_path: Path, voice: str = "es-MX-JorgeNeural"):
    """Uses edge-tts to generate an MP3 file with a fallback to Google TTS."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
    except Exception as e:
        print(f"[TTS] Microsoft Edge-TTS connection failed: {e}. Falling back to gTTS...")
        def generate_gtts():
            tts = gTTS(text=text, lang="es", tld="com.mx")
            tts.save(str(output_path))
        await asyncio.to_thread(generate_gtts)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
            
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="El archivo PDF está vacío.")

        # ── Extract text ───────────────────────────────────────────────────────
        try:
            # Extraemos todo el texto posible (límite subido a 1000 páginas)
            text = extract_text_from_pdf(pdf_bytes, max_pages=1000)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"No se pudo leer el PDF: {exc}")

        if not text:
            raise HTTPException(
                status_code=422,
                detail="Las primeras páginas del PDF no contienen texto extraíble (puede ser un PDF escaneado).",
            )

        # ── Derive title ────────────────────────────────────────────────────────
        raw_title = file.filename.rsplit(".", 1)[0]  # strip ".pdf"
        title = raw_title.replace("_", " ").replace("-", " ").strip() or "Libro sin título"

        # ── Chunking & Metadata ──────────────────────────────────────────────────
        chunks = chunk_text(text, max_chars=3800)
        if not chunks:
             raise HTTPException(status_code=422, detail="No se pudo extraer texto suficiente.")

        book_id = uuid.uuid4().hex[:12]

        # ── Extract Cover ────────────────────────────────────────────────────────
        cover_url = None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if len(doc) > 0:
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                cover_bytes = pix.tobytes("png")
                
                cover_path = f"{book_id}/cover.png"
                supabase.storage.from_("books").upload(
                    cover_path,
                    cover_bytes,
                    {"content-type": "image/png"}
                )
                cover_url = supabase.storage.from_("books").get_public_url(cover_path)
                
            doc.close()
        except Exception as e:
            print(f"[PDF] Error extracting cover: {e}")

        # ── Upload Chunks ────────────────────────────────────────────────────────
        for i, chunk in enumerate(chunks):
            txt_path = f"{book_id}/text/part_{i}.txt"
            supabase.storage.from_("books").upload(
                txt_path,
                chunk.encode("utf-8"),
                {"content-type": "text/plain"}
            )

        print(f"Subida completada con éxito: {book_id}")
        return JSONResponse({
            "title": title,
            "bookId": book_id,
            "partsCount": len(chunks),
            "coverUrl": cover_url
        })
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly so FastAPI handles them
        raise http_exc
    except Exception as exc:
        print(f"[Upload Error] {type(exc).__name__}: {exc}")
        # Explicit JSON Response to preserve CORS headers on 500
        return JSONResponse(status_code=500, content={"detail": f"Error interno en el servidor: {str(exc)}"})


@app.get("/api/clean-audio")
async def clean_audio(token: str = None):
    """
    Cleans up all generated MP3 audio files in the 'books' storage bucket.
    This frees up space while maintaining book texts and user progress.
    """
    expected_token = os.environ.get("CLEANUP_TOKEN") or "libris_cleanup_default_secret_2026"
    if token != expected_token:
        raise HTTPException(status_code=403, detail="No autorizado")

    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    try:
        # 1. Obtener la lista de todos los libros para saber sus IDs
        def get_books():
            return supabase.table("global_books").select("book_id").execute()
        
        response = await asyncio.to_thread(get_books)
        book_ids = [row["book_id"] for row in response.data]
        
        cleaned_count = 0
        all_paths_to_delete = []

        # 2. Listar los archivos en su carpeta de audio de forma concurrente
        async def process_book(book_id):
            def list_audio_files(bid):
                return supabase.storage.from_("books").list(f"{bid}/audio", {"limit": 1000})
            try:
                files = await asyncio.to_thread(list_audio_files, book_id)
                paths = []
                for f in files:
                    if f.get("name") and f["name"].endswith(".mp3"):
                        paths.append(f"{book_id}/audio/{f['name']}")
                return paths
            except Exception as e:
                print(f"[Cleanup] Error al listar audios para libro {book_id}: {e}")
                return []

        tasks = [process_book(bid) for bid in book_ids]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            all_paths_to_delete.extend(res)

        # 3. Eliminar los archivos en lotes de 100 de forma concurrente
        if all_paths_to_delete:
            def delete_batch(batch):
                return supabase.storage.from_("books").remove(batch)
                
            delete_tasks = []
            for i in range(0, len(all_paths_to_delete), 100):
                chunk = all_paths_to_delete[i:i+100]
                delete_tasks.append(asyncio.to_thread(delete_batch, chunk))
                cleaned_count += len(chunk)
                
            await asyncio.gather(*delete_tasks)

        return JSONResponse({
            "status": "success",
            "message": f"Se eliminaron {cleaned_count} archivos de audio (.mp3)",
            "files_deleted": all_paths_to_delete
        })

    except Exception as e:
        print(f"[Cleanup Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error al limpiar audios: {str(e)}")


@app.get("/api/audio/{book_id}/{part_index}")
async def get_book_audio(book_id: str, part_index: int, voice: str = "es-MX-JorgeNeural"):
    """JIT Engine: Delivers audio for a specific part. Generates it if missing."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    safe_voice = sanitize_filename(voice)
    mp3_path = f"{book_id}/audio/part_{part_index}_{safe_voice}.mp3"
    public_mp3_url = supabase.storage.from_("books").get_public_url(mp3_path)
    
    # 1. Check if it already exists in Cloud Storage by pinging its public URL
    async with httpx.AsyncClient() as client:
        try:
            r = await client.head(public_mp3_url)
            if r.status_code == 200:
                print(f"[Audio] Caching Hit for {mp3_path}")
                return RedirectResponse(public_mp3_url)
        except Exception:
            pass

    # 2. Doesn't exist. We must generate it. Download text first.
    txt_path = f"{book_id}/text/part_{part_index}.txt"
    public_txt_url = supabase.storage.from_("books").get_public_url(txt_path)
    
    async with httpx.AsyncClient() as client:
        r = await client.get(public_txt_url)
        if r.status_code != 200:
            raise HTTPException(status_code=404, detail="Parte de texto no encontrada en la nube")
        text = r.text
        
    print(f"[Audio] Generando MP3 localmente para {mp3_path}...")
    local_mp3 = Path(f"/tmp/{book_id}_part_{part_index}_{safe_voice}.mp3")
    local_mp3.parent.mkdir(parents=True, exist_ok=True)
    try:
        await text_to_mp3(text, local_mp3, voice=voice)
    except Exception as exc:
        import traceback
        print(f"!!! CRASH IN EDGE-TTS !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar audio: {exc}")
        
    # 3. Upload the generated MP3 to Cloud Storage
    print(f"[Audio] Subiendo generacion a Supabase Storage: {mp3_path}")
    with open(local_mp3, "rb") as f:
        try:
            supabase.storage.from_("books").upload(
                mp3_path,
                f.read(),
                {"content-type": "audio/mpeg"}
            )
        except Exception as e:
            print(f"[Audio] Error subiendo MP3 a Supabase: {e}")
            
    # Clean up local temp file
    try:
        local_mp3.unlink()
    except:
        pass
        
    # 4. Redirect seamlessly to the newly generated public MP3 file!
    return RedirectResponse(public_mp3_url)


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

    # ── Delete all Storage files concurrently ─────────────────────────────
    async def delete_folder(folder: str):
        """List and remove all files under a storage folder path."""
        try:
            files = await asyncio.to_thread(
                lambda: supabase.storage.from_("books").list(folder, {"limit": 1000})
            )
            paths = [f"{folder}/{f['name']}" for f in files if f.get("name")]
            if paths:
                await asyncio.to_thread(lambda: supabase.storage.from_("books").remove(paths))
                print(f"[Delete] Removed {len(paths)} files from {folder}/")
        except Exception as e:
            print(f"[Delete] Warning: could not clean folder {folder}: {e}")

    await asyncio.gather(
        delete_folder(f"{book_id_hex}/audio"),
        delete_folder(f"{book_id_hex}/text"),
    )
    # Cover is a single file, remove directly
    try:
        await asyncio.to_thread(
            lambda: supabase.storage.from_("books").remove([f"{book_id_hex}/cover.png"])
        )
    except Exception:
        pass

    # ── Delete global_books record (CASCADE removes user_books) ──────────
    # IMPORTANT: Must use user's JWT directly (not the anon-key supabase client)
    # so that auth.uid() is set and the RLS DELETE policy is satisfied.
    await _supabase_delete_as_user("global_books", "id", str(global_book_db_id), token)

    print(f"[Delete] Book {book_id_hex} (db id: {global_book_db_id}) permanently deleted by user {user_id}")
    return JSONResponse({"status": "success", "message": "Libro eliminado del catálogo permanentemente"})


@app.patch("/api/books/{book_id_hex}")
async def update_book_meta(book_id_hex: str, body: dict, authorization: str = Header(default=None)):
    """
    Owner-only: Update a book's title and/or category in global_books.
    Body: { "title": "...", "category": "..." }  (both optional)
    Requires: Authorization: Bearer <supabase_jwt>
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    # ── Auth ──────────────────────────────────────────────────────────────
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

    # ── Build patch (only allow title and category) ───────────────────────
    patch: dict = {}
    if "title" in body and isinstance(body["title"], str) and body["title"].strip():
        patch["title"] = body["title"].strip()
    if "category" in body and isinstance(body["category"], str):
        patch["category"] = body["category"].strip() or None

    if not patch:
        raise HTTPException(status_code=400, detail="Nada que actualizar. Envía 'title' y/o 'category'.")

    # IMPORTANT: Must use user's JWT directly (not the anon-key supabase client)
    # so that auth.uid() is set and the RLS UPDATE policy is satisfied.
    await _supabase_patch_as_user("global_books", "id", str(global_book_db_id), patch, token)

    print(f"[Update] Book {book_id_hex} updated by user {user_id}: {patch}")
    return JSONResponse({"status": "success", "updated": patch})


# ---------------------------------------------------------------------------
# Debug endpoint — inspect extracted text without generating audio
# ---------------------------------------------------------------------------
@app.post("/api/preview-pdf")
async def preview_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    pages_info = []
    for i in range(min(5, total_pages)):  # check up to 5 pages
        raw = doc[i].get_text()
        pages_info.append({"page": i + 1, "chars_raw": len(raw), "preview": raw[:300]})
    doc.close()

    raw_all = "\n".join(p["preview"] for p in pages_info)
    full_raw = "\n".join(
        fitz.open(stream=pdf_bytes, filetype="pdf")[i].get_text()
        for i in range(min(2, total_pages))
    )
    cleaned = clean_text_for_tts(full_raw)

    return JSONResponse({
        "total_pages_in_pdf": total_pages,
        "pages": pages_info,
        "cleaned_text_length": len(cleaned),
        "cleaned_text_preview": cleaned[:500],
        "cleaned_text_end": cleaned[-500:],
    })


# ---------------------------------------------------------------------------
# Dev entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
