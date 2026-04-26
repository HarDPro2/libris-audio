import { Clock } from 'lucide-react';
import { usePlayer } from '@/context/PlayerContext';

export default function HistoryPage() {
  const { books, playBook } = usePlayer();
  const listened = books.filter(b => b.progress > 0).sort((a, b) => b.addedAt.getTime() - a.addedAt.getTime());

  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-foreground mb-6">Historial</h1>
      {listened.length === 0 ? (
        <div className="text-center mt-16 text-muted-foreground">
          <Clock className="h-12 w-12 mx-auto mb-4 opacity-40" />
          <p>Aún no has escuchado ningún libro.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {listened.map(book => (
            <div 
              key={book.id} 
              onClick={() => playBook(book)}
              className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border cursor-pointer hover:bg-card/80 transition-colors"
            >
              <div className="w-12 h-16 rounded-lg overflow-hidden shrink-0">
                <img src={book.coverUrl} alt={book.title} className="w-full h-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">{book.title}</p>
                <p className="text-xs text-muted-foreground">{book.author}</p>
              </div>
              <span className="text-sm text-primary font-medium">{book.progress}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
