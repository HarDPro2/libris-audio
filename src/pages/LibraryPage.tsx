import { useState, useEffect } from 'react';
import { BookCard } from '@/components/libris/BookCard';
import { UploadCard } from '@/components/libris/UploadCard';
import { usePlayer } from '@/context/PlayerContext';
import { fetchGlobalBooks } from '@/hooks/useBooks';
import { BOOK_CATEGORIES } from '@/data/categories';
import { cn } from '@/lib/utils';
import { Book } from '@/types/book';

export default function LibraryPage() {
  const { books: personalBooks } = usePlayer();
  const [globalBooks, setGlobalBooks] = useState<Book[]>([]);
  const [activeTab, setActiveTab] = useState<'explorar' | 'personal'>('personal');
  const [activeCategory, setActiveCategory] = useState("Todas");
  const [loadingGlobal, setLoadingGlobal] = useState(false);

  useEffect(() => {
    if (activeTab === 'explorar') {
      setLoadingGlobal(true);
      fetchGlobalBooks()
        .then(setGlobalBooks)
        .finally(() => setLoadingGlobal(false));
    }
  }, [activeTab]);

  const sourceBooks = activeTab === 'personal' ? personalBooks : globalBooks;

  const filteredBooks = activeCategory === "Todas" 
    ? sourceBooks 
    : sourceBooks.filter(b => (b.category || "Sin Clasificar") === activeCategory);

  const usedCategories = new Set(sourceBooks.map(b => b.category || "Sin Clasificar"));
  const availableCategories = ["Todas", ...BOOK_CATEGORIES.filter(c => c !== "Todas" && usedCategories.has(c))];

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <h1 className="text-2xl font-bold text-foreground">
          {activeTab === 'personal' ? 'Mi Biblioteca' : 'Explorar'}
        </h1>
        
        {/* Main Tabs */}
        <div className="flex bg-[hsl(var(--card))] rounded-lg p-1 border border-[hsl(var(--border))] self-start">
          <button
            onClick={() => { setActiveTab('explorar'); setActiveCategory('Todas'); }}
            className={cn(
              "px-4 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeTab === 'explorar' ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            Explorar
          </button>
          <button
            onClick={() => { setActiveTab('personal'); setActiveCategory('Todas'); }}
            className={cn(
              "px-4 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeTab === 'personal' ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            Mi Biblioteca
          </button>
        </div>
      </div>
      
      {/* Category Pills */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
        {availableCategories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
               "px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors border",
               activeCategory === cat 
                 ? "bg-primary text-primary-foreground border-primary" 
                 : "bg-transparent text-muted-foreground border-[hsl(var(--border))] hover:border-primary/50"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {loadingGlobal ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
        </div>
      ) : sourceBooks.length === 0 && activeTab === 'personal' ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="text-4xl mb-4">📚</div>
          <h2 className="text-lg font-semibold mb-2">Tu biblioteca está vacía</h2>
          <p className="text-muted-foreground text-sm max-w-sm mb-6">
            Ve a la pestaña Explorar para encontrar audiolibros o sube un PDF nuevo para empezar.
          </p>
          <button 
            onClick={() => setActiveTab('explorar')}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-full text-sm font-semibold hover:opacity-90 transition-opacity"
          >
            Explorar catálogo
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filteredBooks.map(book => (
            <BookCard key={book.id} book={book} variant="grid" />
          ))}
          {/* Al subir siempre va al global, y al usar la app, es util tener la opcion a mano */}
          {(activeCategory === "Todas" || activeCategory === "Nuevos") && <UploadCard />}
        </div>
      )}
    </div>
  );
}

