"""
migrate_to_r2.py - Ejecucion UNICA
Copia todos los archivos existentes de Supabase Storage -> Cloudflare R2.
- Migra: covers (PNG) y partes de texto (TXT)
- NO migra: MP3 de audio (se regeneran automaticamente JIT)
- Actualiza cover_url en global_books con las nuevas URLs de R2

Uso:
  1. Exporta las variables de entorno (ver abajo)
  2. pip install boto3 supabase httpx
  3. python migrate_to_r2.py
"""

import os
import asyncio
import httpx
import boto3
from botocore.config import Config
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
R2_ACCESS_KEY_ID     = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT_URL      = os.environ.get("R2_ENDPOINT_URL", "")
R2_BUCKET            = os.environ.get("R2_BUCKET_NAME", "libris-audio")
R2_PUBLIC_URL        = os.environ.get("R2_PUBLIC_URL", "").rstrip("/")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

r2 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)

def r2_upload(key, data, content_type):
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=content_type)

def r2_public_url(key):
    return f"{R2_PUBLIC_URL}/{key}"

async def download_url(url):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url)
        if r.status_code == 200:
            return r.content
        print(f"  WARN: No se pudo descargar ({r.status_code}): {url}")
        return None

async def migrate_book(book):
    book_id = book["book_id"]
    parts_count = book.get("parts_count", 0)
    old_cover_url = book.get("cover_url", "")
    result = {"book_id": book_id, "cover": False, "parts": 0, "errors": []}
    print(f"\n[>] Migrando: {book.get('title', book_id)} ({book_id})")

    # Cover
    if old_cover_url and "supabase" in old_cover_url:
        data = await download_url(old_cover_url)
        if data:
            key = f"{book_id}/cover.png"
            await asyncio.to_thread(r2_upload, key, data, "image/png")
            new_url = r2_public_url(key)
            supabase_client.table("global_books").update({"cover_url": new_url}).eq("book_id", book_id).execute()
            print(f"  [OK] Cover -> {new_url}")
            result["cover"] = True
        else:
            result["errors"].append("cover download failed")
    else:
        print(f"  [--] Cover: ya en R2 o sin cover")

    # Partes de texto
    migrated = 0
    for i in range(parts_count):
        txt_url = supabase_client.storage.from_("books").get_public_url(f"{book_id}/text/part_{i}.txt")
        data = await download_url(txt_url)
        if data:
            key = f"{book_id}/text/part_{i}.txt"
            await asyncio.to_thread(r2_upload, key, data, "text/plain; charset=utf-8")
            migrated += 1
        else:
            result["errors"].append(f"part_{i} failed")
    result["parts"] = migrated
    print(f"  [OK] Partes: {migrated}/{parts_count}")
    return result

async def main():
    print("=== Migracion Supabase Storage -> Cloudflare R2 ===")
    print(f"Bucket: {R2_BUCKET}  |  URL: {R2_PUBLIC_URL}\n")

    if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL, R2_PUBLIC_URL]):
        print("ERROR: Faltan variables de entorno R2.")
        return

    response = supabase_client.table("global_books").select("book_id,title,cover_url,parts_count").execute()
    books = response.data
    print(f"Total libros: {len(books)}")

    sem = asyncio.Semaphore(5)
    async def run(book):
        async with sem:
            return await migrate_book(book)

    results = await asyncio.gather(*[run(b) for b in books])

    covers = sum(1 for r in results if r["cover"])
    parts  = sum(r["parts"] for r in results)
    errors = sum(len(r["errors"]) for r in results)
    print(f"\n=== RESUMEN ===")
    print(f"Libros: {len(results)} | Covers: {covers} | Partes: {parts} | Errores: {errors}")
    if errors:
        for r in results:
            if r["errors"]:
                print(f"  {r['book_id']}: {r['errors']}")

if __name__ == "__main__":
    asyncio.run(main())
