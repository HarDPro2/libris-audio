import { supabase } from '@/lib/supabase';
import { Book } from '@/types/book';

// Maps a joined user_books + global_books row to our local Book type
function rowToBook(row: any): Book {
  const gb = row.global_books;
  return {
    id: gb.id, // We use the global book ID as the main identifier
    title: gb.title,
    author: gb.author ?? '',
    coverUrl: gb.cover_url ?? '',
    progress: row.progress ?? 0,
    duration: '',
    currentTime: row.current_time ?? 0,
    totalTime: row.total_time ?? 0,
    addedAt: new Date(row.added_at),
    bookId: gb.book_id,
    partsCount: gb.parts_count ?? 1,
    currentPartIndex: row.current_part_index ?? 0,
    voice: gb.voice,
    category: gb.category,
    fileHash: gb.file_hash,
  };
}

// Maps a raw global_books row to a Book (with no personal progress)
function globalRowToBook(gb: any): Book {
  return {
    id: gb.id,
    title: gb.title,
    author: gb.author ?? '',
    coverUrl: gb.cover_url ?? '',
    progress: 0,
    duration: '',
    currentTime: 0,
    totalTime: 0,
    addedAt: new Date(gb.created_at),
    bookId: gb.book_id,
    partsCount: gb.parts_count ?? 1,
    currentPartIndex: 0,
    voice: gb.voice,
    category: gb.category,
    fileHash: gb.file_hash,
  };
}

// 1. Fetch the user's personal library (progress included)
export async function fetchUserBooks(): Promise<Book[]> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return [];

  const { data, error } = await supabase
    .from('user_books')
    .select('*, global_books(*)')
    .eq('user_id', user.id)
    .order('added_at', { ascending: false });

  if (error) { console.error('fetchUserBooks error:', error); return []; }
  return (data ?? []).map(rowToBook);
}

// 2. Fetch all available books in the global catalog
export async function fetchGlobalBooks(): Promise<Book[]> {
  const { data, error } = await supabase
    .from('global_books')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) { console.error('fetchGlobalBooks error:', error); return []; }
  return (data ?? []).map(globalRowToBook);
}

// 3. Add a newly uploaded book to the Global Library
export async function addGlobalBook(book: Book): Promise<string | null> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;

  const { data, error } = await supabase.from('global_books').insert({
    // We optionally let the DB generate the ID, or use ours
    id: book.id,
    title: book.title,
    author: book.author,
    cover_url: book.coverUrl,
    book_id: book.bookId,
    parts_count: book.partsCount ?? 1,
    voice: book.voice,
    category: book.category,
    file_hash: book.fileHash,
    added_by: user.id
  }).select('id').single();

  if (error) { console.error('addGlobalBook error:', error); return null; }
  return data.id;
}

// 4. Add a global book to the user's personal library
export async function addToPersonalLibrary(globalBookId: string): Promise<void> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;

  const { error } = await supabase.from('user_books').insert({
    user_id: user.id,
    global_book_id: globalBookId,
    current_part_index: 0,
    current_time: 0,
    total_time: 0,
    progress: 0
  });

  if (error && error.code !== '23505') { // Ignore unique violation (already added)
    console.error('addToPersonalLibrary error:', error);
  }
}

// 5. Remove a book from personal library
export async function removeFromPersonalLibrary(globalBookId: string): Promise<void> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;

  await supabase
    .from('user_books')
    .delete()
    .eq('user_id', user.id)
    .eq('global_book_id', globalBookId);
}

// 6. Update progress of a personal book
export async function updateBookProgressInDb(globalBookId: string, patch: Partial<{
  current_part_index: number;
  current_time: number;
  total_time: number;
  progress: number;
}>): Promise<void> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;

  await supabase
    .from('user_books')
    .update(patch)
    .eq('user_id', user.id)
    .eq('global_book_id', globalBookId);
}

// 7. Check if a duplicate PDF hash exists in the global library
export async function checkDuplicateHash(hash: string): Promise<boolean> {
  const { data } = await supabase
    .from('global_books')
    .select('id')
    .eq('file_hash', hash)
    .limit(1);
  return (data?.length ?? 0) > 0;
}
