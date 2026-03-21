import asyncio
import os
import re
import uuid
import json
from pathlib import Path

import edge_tts
import fitz  # PyMuPDF
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

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
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files as static assets
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


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
async def upload_pdf(file: UploadFile = File(...), voice: str = Form("es-MX-JorgeNeural")):
    # ── Validate ──────────────────────────────────────────────────────────
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
    book_dir = BOOKS_DIR / book_id
    book_dir.mkdir()
    
    # ── Extract Cover ────────────────────────────────────────────────────────
    cover_url = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 0:
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            pix.save(book_dir / "cover.png")
            cover_url = f"http://localhost:8000/static/books/{book_id}/cover.png"
        doc.close()
    except Exception as e:
        print(f"[PDF] Error extracting cover: {e}")
    
    for i, chunk in enumerate(chunks):
        (book_dir / f"part_{i}.txt").write_text(chunk, encoding="utf-8")
        
    (book_dir / "metadata.json").write_text(json.dumps({
        "title": title,
        "voice": voice,
        "parts_count": len(chunks),
        "cover_url": cover_url
    }), encoding="utf-8")

    return JSONResponse({
        "title": title,
        "bookId": book_id,
        "partsCount": len(chunks),
        "voice": voice,
        "coverUrl": cover_url
    })


@app.get("/api/audio/{book_id}/{part_index}")
async def get_book_audio(book_id: str, part_index: int):
    """JIT Engine: Delivers audio for a specific part. Generates it if missing."""
    book_dir = BOOKS_DIR / book_id
    if not book_dir.exists():
        raise HTTPException(status_code=404, detail="Libro no encontrado")
        
    mp3_path = book_dir / f"part_{part_index}.mp3"
    txt_path = book_dir / f"part_{part_index}.txt"
    metadata_path = book_dir / "metadata.json"
    
    if not txt_path.exists():
        raise HTTPException(status_code=404, detail="Parte no encontrada")
        
    if not mp3_path.exists():
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        voice = meta.get("voice", "es-MX-JorgeNeural")
        text = txt_path.read_text(encoding="utf-8")
        try:
            await text_to_mp3(text, mp3_path, voice=voice)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error al generar audio: {exc}")
            
    return FileResponse(mp3_path, media_type="audio/mpeg")



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
