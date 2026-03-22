import { Play, MoreVertical, Trash2, FolderPlus } from 'lucide-react';
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

interface BookCardProps {
  book: Book;
  variant?: 'carousel' | 'grid';
}

export function BookCard({ book, variant = 'carousel' }: BookCardProps) {
  const { playBook, updateBookCategory, removeBook, restartBook } = usePlayer();

  if (variant === 'grid') {
    return (
      <div className="book-card group" onClick={() => playBook(book)}>
        <div className="aspect-[3/4] rounded-lg overflow-hidden mb-3 relative">
          <img src={book.coverUrl} alt={book.title} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center cursor-pointer hover:scale-105 transition-transform" onClick={() => playBook(book)}>
              <Play className="h-5 w-5 text-primary-foreground ml-0.5" />
            </div>
          </div>
          
          <div className="absolute top-2 left-2">
            <span className="px-2 py-1 text-[10px] font-medium bg-background/80 backdrop-blur-sm rounded-md text-foreground shadow-sm">
              {book.category || "Sin Clasificar"}
            </span>
          </div>

          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="secondary" size="icon" className="h-8 w-8 bg-background/80 hover:bg-background backdrop-blur-sm" onClick={(e) => e.stopPropagation()}>
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56" onClick={(e) => e.stopPropagation()}>
                <DropdownMenuLabel>Opciones</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <FolderPlus className="mr-2 h-4 w-4" />
                    <span>Mover a...</span>
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent className="max-h-[300px] overflow-y-auto">
                      {BOOK_CATEGORIES.filter(c => c !== "Todas").map(cat => (
                        <DropdownMenuItem 
                          key={cat} 
                          onClick={(e) => {
                            e.stopPropagation();
                            updateBookCategory(book.id, cat);
                          }}
                        >
                          {cat}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="cursor-pointer" onClick={(e) => { e.stopPropagation(); restartBook(book.id); playBook(book); }}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  <span>Empezar desde el principio</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive focus:bg-destructive/10 cursor-pointer" onClick={(e) => { e.stopPropagation(); removeBook(book.id); }}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  <span>Quitar de Mi Biblioteca</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <h3 className="text-sm font-semibold text-foreground truncate">{book.title}</h3>
        <p className="text-xs text-muted-foreground truncate">{book.author}</p>
        {book.progress > 0 && (
          <div className="mt-2">
            <Progress value={book.progress} className="h-1" />
            <p className="text-[10px] text-muted-foreground mt-1">{book.progress}%</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="book-card flex gap-4 min-w-[300px] max-w-[340px] shrink-0">
      <div className="w-20 h-28 rounded-lg overflow-hidden shrink-0">
        <img src={book.coverUrl} alt={book.title} className="w-full h-full object-cover" />
      </div>
      <div className="flex flex-col justify-between flex-1 min-w-0 py-1">
        <div>
          <h3 className="text-sm font-semibold text-foreground truncate">{book.title}</h3>
          <p className="text-xs text-muted-foreground truncate">{book.author}</p>
          <p className="text-[10px] text-muted-foreground mt-1">{book.duration}</p>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Progress value={book.progress} className="h-1.5 flex-1" />
            <span className="text-xs text-primary font-medium">{book.progress}%</span>
          </div>
          <Button
            size="sm"
            className="h-8 w-full text-xs font-semibold"
            onClick={() => playBook(book)}
          >
            <Play className="h-3.5 w-3.5 mr-1" />
            Reproducir
          </Button>
        </div>
      </div>
    </div>
  );
}
