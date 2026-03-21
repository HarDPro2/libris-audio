import { Plus, Loader2, AlertCircle, Volume2 } from 'lucide-react';
import { useRef, useState } from 'react';
import { usePlayer } from '@/context/PlayerContext';
import { checkDuplicateHash, addGlobalBook } from '@/hooks/useBooks';
import { useToast } from '@/components/ui/use-toast';
import { BOOK_CATEGORIES } from '@/data/categories';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { Button } from '@/components/ui/button';



export function UploadCard() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const { refreshBooks } = usePlayer();
  const { toast } = useToast();

  const selectableCategories = BOOK_CATEGORIES.filter(c => c !== "Todas" && c !== "Nuevos");

  const handleClick = () => {
    if (!selectedCategory) {
      setError('Debes elegir una categoría primero.');
      return;
    }
    if (!isProcessing) {
      setError(null);
      const confirmUpload = window.confirm(
        "¿Ya revisaste en la pestaña 'Explorar' que el libro no exista?\n\nPor favor, ayúdanos a evitar audiolibros duplicados en la plataforma."
      );
      if (confirmUpload) {
        fileRef.current?.click();
      }
    }
  };

  // Very basic SHA-256 calculator from file blob
  const calculateHash = async (file: File) => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setError('El archivo supera los 10 MB.');
      if (fileRef.current) fileRef.current.value = '';
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const hash = await calculateHash(file);
      const isDuplicate = await checkDuplicateHash(hash);
      
      if (isDuplicate) {
        toast({
          title: "Libro duplicado",
          description: "Este PDF ya se encuentra en la biblioteca global.",
          variant: "default",
        });
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail ?? `Error ${response.status}`);
      }

      const data: { title: string; bookId: string; partsCount: number; voice: string; coverUrl?: string } = await response.json();
      
      // Push to global library via Supabase
      await addGlobalBook({
        id: crypto.randomUUID(),
        title: data.title,
        author: 'Documento PDF',
        coverUrl: data.coverUrl || 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=300&h=400&fit=crop',
        progress: 0,
        duration: data.partsCount ? `~${data.partsCount * 4}min` : '~15min',
        currentTime: 0,
        totalTime: data.partsCount ? 0 : 900,
        addedAt: new Date(),
        bookId: data.bookId,
        partsCount: data.partsCount,
        currentPartIndex: 0,
        voice: data.voice || 'es-MX-JorgeNeural',
        fileHash: hash,
        category: selectedCategory
      });

      await refreshBooks();

      toast({
        title: "¡Libro procesado!",
        description: "El libro se ha añadido a la Biblioteca Principal.",
        style: { background: 'hsl(var(--primary))', color: 'hsl(var(--primary-foreground))', border: 'none' }
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido';
      setError(message);
    } finally {
      setIsProcessing(false);
      setSelectedCategory(''); // Reset
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={fileRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFile}
      />
      
      <div className="upload-card aspect-[3/4]" onClick={handleClick}>
        {isProcessing ? (
          <>
            <Loader2 className="h-10 w-10 text-primary animate-spin" />
            <span className="text-sm text-muted-foreground font-medium text-center px-2">
              Procesando PDF…<br />
              <span className="text-xs opacity-70">Generando audio con IA</span>
            </span>
          </>
        ) : error ? (
          <>
            <AlertCircle className="h-10 w-10 text-destructive" />
            <span className="text-xs text-destructive font-medium text-center px-3 leading-tight">
              {error}
            </span>
            <span className="text-xs text-muted-foreground mt-1">Toca para reintentar</span>
          </>
        ) : (
          <>
            <div className="h-14 w-14 rounded-full border-2 border-dashed border-muted-foreground/40 flex items-center justify-center">
              <Plus className="h-7 w-7 text-muted-foreground" />
            </div>
            <span className="text-sm text-muted-foreground font-medium">Subir Nuevo PDF</span>
            <span className="text-[10px] text-muted-foreground mt-1">Máximo 10 MB</span>
          </>
        )}
      </div>

      <div className="flex flex-col gap-2 w-full">
        <Select value={selectedCategory} onValueChange={(val) => { setSelectedCategory(val); setError(null); }} disabled={isProcessing}>
          <SelectTrigger className="w-full bg-[hsl(var(--card))] border-[hsl(var(--border))]">
            <SelectValue placeholder="Categoría obligatoria" />
          </SelectTrigger>
          <SelectContent>
            {selectableCategories.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}


