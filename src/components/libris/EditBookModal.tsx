import { useState, useEffect } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { Book } from '@/types/book';
import { usePlayer } from '@/context/PlayerContext';
import { BOOK_CATEGORIES } from '@/data/categories';
import { Button } from '@/components/ui/button';

interface EditBookModalProps {
  book: Book;
  onClose: () => void;
  onSaved: (updatedBook: Book) => void;
}

export function EditBookModal({ book, onClose, onSaved }: EditBookModalProps) {
  const { updateGlobalBookMeta } = usePlayer();
  const [title, setTitle] = useState(book.title);
  const [category, setCategory] = useState(book.category || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleSave = async () => {
    if (!title.trim()) { setError('El título no puede estar vacío'); return; }
    setSaving(true);
    setError('');
    try {
      const patch: { title?: string; category?: string } = {};
      if (title.trim() !== book.title) patch.title = title.trim();
      if (category !== (book.category || '')) patch.category = category;

      if (Object.keys(patch).length > 0) {
        await updateGlobalBookMeta(book, patch);
      }
      onSaved({ ...book, ...patch });
    } catch (err: any) {
      setError(err.message || 'Error al guardar los cambios');
    } finally {
      setSaving(false);
    }
  };

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Modal panel */}
      <div className="relative w-full max-w-md mx-4 rounded-2xl bg-card border border-border shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">Editar libro</h2>
          <button
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Book preview */}
        <div className="flex items-center gap-4 px-6 py-4 border-b border-border bg-muted/30">
          {book.coverUrl && (
            <img
              src={book.coverUrl}
              alt={book.title}
              className="w-12 h-16 rounded-lg object-cover shrink-0 shadow-md"
            />
          )}
          <p className="text-xs text-muted-foreground leading-relaxed">
            Los cambios que hagas aquí se reflejarán en el <strong>catálogo global</strong> para todos los usuarios.
          </p>
        </div>

        {/* Form */}
        <div className="px-6 py-5 space-y-5">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5" htmlFor="edit-book-title">
              Título
            </label>
            <input
              id="edit-book-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
              placeholder="Título del libro"
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5" htmlFor="edit-book-category">
              Categoría
            </label>
            <select
              id="edit-book-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors appearance-none cursor-pointer"
            >
              <option value="">Sin Clasificar</option>
              {BOOK_CATEGORIES.filter(c => c !== 'Todas').map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 pb-5">
          <Button
            variant="outline"
            className="flex-1"
            onClick={onClose}
            disabled={saving}
          >
            Cancelar
          </Button>
          <Button
            className="flex-1"
            onClick={handleSave}
            disabled={saving || !title.trim()}
          >
            {saving ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Guardando...</>
            ) : (
              <><Save className="h-4 w-4 mr-2" />Guardar cambios</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
