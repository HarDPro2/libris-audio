import { useState } from 'react';
import { BookCard } from '@/components/libris/BookCard';
import { UploadCard } from '@/components/libris/UploadCard';
import { usePlayer } from '@/context/PlayerContext';
import { BOOK_CATEGORIES } from '@/data/categories';
import { cn } from '@/lib/utils';

export default function LibraryPage() {
  const { books } = usePlayer();
  const [activeCategory, setActiveCategory] = useState("Todas");

  const filteredBooks = activeCategory === "Todas" 
    ? books 
    : books.filter(b => (b.category || "Sin Clasificar") === activeCategory);

  const usedCategories = new Set(books.map(b => b.category || "Sin Clasificar"));
  const availableCategories = ["Todas", ...BOOK_CATEGORIES.filter(c => c !== "Todas" && usedCategories.has(c))];

  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-foreground mb-4">Mi Biblioteca</h1>
      
      {/* Category Pills */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
        {availableCategories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
               "px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors",
               activeCategory === cat 
                 ? "bg-primary text-primary-foreground" 
                 : "bg-[hsl(var(--card))] text-muted-foreground hover:bg-muted"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {filteredBooks.map(book => (
          <BookCard key={book.id} book={book} variant="grid" />
        ))}
        {activeCategory === "Todas" && <UploadCard />}
      </div>
    </div>
  );
}
