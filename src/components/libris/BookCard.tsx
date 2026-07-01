import { useState } from 'react';
import { Play, MoreVertical, Trash2, FolderPlus, Pencil, AlertTriangle, Loader2 } from 'lucide-react';
import { Book } from '@/types/book';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { usePlayer } from '@/context/PlayerContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
} from '@/components/ui/dropdown-menu';
import { BOOK_CATEGORIES } from '@/data/categories';
import { RotateCcw } from 'lucide-react';
import { EditBookModal } from './EditBookModal';

interface BookCardProps {
  book: Book;
  variant?: 'carousel' | 'grid';
  currentUserId?: string;
  onDeleted?: (bookId: string) => void; // called after successful global delete
}

// ── Inline delete-confirmation dialog ──────────────────────────────────────
function DeleteConfirmDialog({
  book,
  onConfirm,
  onCancel,
}: {
  book: Book;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setDeleting(true);
    setError('');
    try {
      await onConfirm();
    } catch (err: any) {
      setError(err.message || 'Error al eliminar el libro');
      setDeleting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}
    >
      <div className="w-full max-w-sm mx-4 rounded-2xl bg-card border border-border shadow-2xl p-6">
        <div className="flex items-start gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-destructive/15 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </div>
          <div>
            <h3 className="font-bold text-foreground">¿Eliminar del catálogo?</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Esto borrará <strong>"{book.title}"</strong> permanentemente para todos los usuarios. Esta acción no se puede deshacer.
            </p>
          </div>
        </div>

        {error && (
          <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg mb-4">{error}</p>
        )}

        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={onCancel} disabled={deleting}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            className="flex-1"
            onClick={handleConfirm}
            disabled={deleting}
          >
            {deleting ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Eliminando...</>
            ) : (
              <><Trash2 className="h-4 w-4 mr-2" />Eliminar</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Main BookCard component ─────────────────────────────────────────────────
export function BookCard({ book, variant = 'carousel', currentUserId, onDeleted }: BookCardProps) {
  const { playBook, updateBookCategory, removeBook, restartBook, deleteGlobalBook } = usePlayer();
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [localBook, setLocalBook] = useState(book);

  const isOwner = !!(currentUserId && localBook.uploadedBy === currentUserId);

  const handleDeleteGlobal = async () => {
    await deleteGlobalBook(localBook);
    setShowDeleteDialog(false);
    // Notify parent (e.g. LibraryPage) to remove this card from its local list immediately
    onDeleted?.(localBook.id);
  };

  if (variant === 'grid') {
    return (
      <>
        <div className="book-card group" onClick={() => playBook(localBook)}>
          <div className="aspect-[3/4] rounded-lg overflow-hidden mb-3 relative">
            <img src={localBook.coverUrl} alt={localBook.title} className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <div
                className="h-12 w-12 rounded-full bg-primary flex items-center justify-center cursor-pointer hover:scale-105 transition-transform"
                onClick={() => playBook(localBook)}
              >
                <Play className="h-5 w-5 text-primary-foreground ml-0.5" />
              </div>
            </div>

            <div className="absolute top-2 left-2">
              <span className="px-2 py-1 text-[10px] font-medium bg-background/80 backdrop-blur-sm rounded-md text-foreground shadow-sm">
                {localBook.category || 'Sin Clasificar'}
              </span>
            </div>

            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="secondary"
                    size="icon"
                    className="h-8 w-8 bg-background/80 hover:bg-background backdrop-blur-sm"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenuLabel>Opciones</DropdownMenuLabel>
                  <DropdownMenuSeparator />

                  {/* ── Owner-only actions ── */}
                  {isOwner && (
                    <>
                      <DropdownMenuItem
                        className="cursor-pointer"
                        onClick={(e) => { e.stopPropagation(); setShowEditModal(true); }}
                      >
                        <Pencil className="mr-2 h-4 w-4 text-primary" />
                        <span>Editar nombre / categoría</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                    </>
                  )}

                  {/* ── Category submenu ── */}
                  <DropdownMenuSub>
                    <DropdownMenuSubTrigger>
                      <FolderPlus className="mr-2 h-4 w-4" />
                      <span>Mover a...</span>
                    </DropdownMenuSubTrigger>
                    <DropdownMenuPortal>
                      <DropdownMenuSubContent className="max-h-[300px] overflow-y-auto">
                        {BOOK_CATEGORIES.filter(c => c !== 'Todas').map(cat => (
                          <DropdownMenuItem
                            key={cat}
                            onClick={(e) => { e.stopPropagation(); updateBookCategory(localBook.id, cat); }}
                          >
                            {cat}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuSubContent>
                    </DropdownMenuPortal>
                  </DropdownMenuSub>

                  <DropdownMenuSeparator />

                  <DropdownMenuItem
                    className="cursor-pointer"
                    onClick={(e) => { e.stopPropagation(); restartBook(localBook.id); playBook(localBook); }}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    <span>Empezar desde el principio</span>
                  </DropdownMenuItem>

                  <DropdownMenuSeparator />

                  <DropdownMenuItem
                    className="text-destructive/80 focus:bg-destructive/10 cursor-pointer"
                    onClick={(e) => { e.stopPropagation(); removeBook(localBook.id); }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    <span>Quitar de Mi Biblioteca</span>
                  </DropdownMenuItem>

                  {/* ── Owner-only: delete from global catalog ── */}
                  {isOwner && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive focus:bg-destructive/10 cursor-pointer font-medium"
                        onClick={(e) => { e.stopPropagation(); setShowDeleteDialog(true); }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        <span>Eliminar del catálogo global</span>
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
          <h3 className="text-sm font-semibold text-foreground truncate">{localBook.title}</h3>
          <p className="text-xs text-muted-foreground truncate">{localBook.author}</p>
          {localBook.progress > 0 && (
            <div className="mt-2">
              <Progress value={localBook.progress} className="h-1" />
              <p className="text-[10px] text-muted-foreground mt-1">{localBook.progress}%</p>
            </div>
          )}
        </div>

        {/* Modals rendered outside the card to avoid z-index issues */}
        {showEditModal && (
          <EditBookModal
            book={localBook}
            onClose={() => setShowEditModal(false)}
            onSaved={(updated) => { setLocalBook(updated); setShowEditModal(false); }}
          />
        )}
        {showDeleteDialog && (
          <DeleteConfirmDialog
            book={localBook}
            onConfirm={handleDeleteGlobal}
            onCancel={() => setShowDeleteDialog(false)}
          />
        )}
      </>
    );
  }

  // ── Carousel variant (unchanged) ──────────────────────────────────────────
  return (
    <div className="book-card flex gap-4 min-w-[300px] max-w-[340px] shrink-0">
      <div className="w-20 h-28 rounded-lg overflow-hidden shrink-0">
        <img src={localBook.coverUrl} alt={localBook.title} className="w-full h-full object-cover" />
      </div>
      <div className="flex flex-col justify-between flex-1 min-w-0 py-1">
        <div>
          <h3 className="text-sm font-semibold text-foreground truncate">{localBook.title}</h3>
          <p className="text-xs text-muted-foreground truncate">{localBook.author}</p>
          <p className="text-[10px] text-muted-foreground mt-1">{localBook.duration}</p>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Progress value={localBook.progress} className="h-1.5 flex-1" />
            <span className="text-xs text-primary font-medium">{localBook.progress}%</span>
          </div>
          <Button
            size="sm"
            className="h-8 w-full text-xs font-semibold"
            onClick={() => playBook(localBook)}
          >
            <Play className="h-3.5 w-3.5 mr-1" />
            Reproducir
          </Button>
        </div>
      </div>
    </div>
  );
}
