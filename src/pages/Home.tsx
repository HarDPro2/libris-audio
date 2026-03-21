import { BookCard } from '@/components/libris/BookCard';
import { UploadCard } from '@/components/libris/UploadCard';
import { usePlayer } from '@/context/PlayerContext';

export default function Home() {
  const { books } = usePlayer();
  const inProgress = books.filter(b => b.progress > 0 && b.progress < 100);

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Continuar escuchando */}
      {inProgress.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-foreground mb-4">Continuar Escuchando</h2>
          <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
            {inProgress.map(book => (
              <BookCard key={book.id} book={book} variant="carousel" />
            ))}
          </div>
        </section>
      )}

      {/* Mi Biblioteca */}
      <section>
        <h2 className="text-lg font-semibold text-foreground mb-4">Mi Biblioteca</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {books.map(book => (
            <BookCard key={book.id} book={book} variant="grid" />
          ))}
          <UploadCard />
        </div>
      </section>
    </div>
  );
}
