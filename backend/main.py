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
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
                    
                    # Conservamos si el tamaño es igual o mayor al main size
                    # Permitimos hasta 0.6pt menos por variaciones de renderizado
                    if size >= main_font_size - 0.6:
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


async def text_to_mp3(text: str, output_path: Path, voice: str = "es-MX-JorgeNeural") -> None:
    """Convert text to speech and save as MP3 using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


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

    return JSONResponse({
        "title": title,
        "bookId": book_id,
        "partsCount": len(chunks),
        "coverUrl": cover_url
    })


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
