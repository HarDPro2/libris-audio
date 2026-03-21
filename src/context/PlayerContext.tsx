import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { Book } from '@/types/book';

interface PlayerState {
  currentBook: Book | null;
  isPlaying: boolean;
  speed: number;
  volume: number;
  elapsed: number;
}

interface PlayerContextValue extends PlayerState {
  books: Book[];
  audioRef: React.RefObject<HTMLAudioElement>;
  playBook: (book: Book) => void;
  togglePlay: () => void;
  setSpeed: (speed: number) => void;
  setVolume: (volume: number) => void;
  seekForward: () => void;
  seekBackward: () => void;
  addBook: (title: string, audioUrl?: string, bookId?: string, partsCount?: number, voice?: string, coverUrl?: string) => void;
  updateBookCategory: (bookId: string, category: string) => void;
  removeBook: (bookId: string) => void;
  restartBook: (bookId: string) => void;
  seekToPart: (partIndex: number) => void;
}

const PlayerContext = createContext<PlayerContextValue | null>(null);

export function PlayerProvider({ children }: { children: React.ReactNode }) {
  const [books, setBooks] = useState<Book[]>(() => {
    try {
      const saved = localStorage.getItem('libris_books');
      if (saved) {
        // Parse basic array, could revive dates here if needed
        const parsed = JSON.parse(saved);
        return parsed.map((p: any) => ({ ...p, addedAt: new Date(p.addedAt) }));
      }
    } catch (e) {
      console.error("Failed loading books from local storage", e);
    }
    return [];
  });
  const [state, setState] = useState<PlayerState>({
    currentBook: null,
    isPlaying: false,
    speed: 1,
    volume: 0.8,
    elapsed: 0,
  });

  // Single shared <audio> element for all playback
  const audioRef = useRef<HTMLAudioElement>(null);

  // ── Sync to LocalStorage ────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem('libris_books', JSON.stringify(books));
  }, [books]);

  // ── Sync src when currentBook changes ──────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const bk = state.currentBook;
    
    if (bk?.bookId) {
      audio.src = `http://localhost:8000/api/audio/${bk.bookId}/${bk.currentPartIndex || 0}`;
    } else if (bk?.audioUrl) {
      audio.src = bk.audioUrl;
    } else {
      audio.src = '';
    }
    
    audio.load();

    const handleCanPlay = () => {
      if (bk?.currentTime && audio.currentTime < 1) {
        audio.currentTime = bk.currentTime;
      }
      if (state.isPlaying) {
        audio.play().catch(() => setState(prev => ({ ...prev, isPlaying: false })));
      }
    };

    audio.addEventListener('canplay', handleCanPlay);
    return () => audio.removeEventListener('canplay', handleCanPlay);
  }, [state.currentBook?.id, state.currentBook?.audioUrl, state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.isPlaying]);

  // ── Prefetch next part ──────────────────────────────────────────────────
  useEffect(() => {
    const bk = state.currentBook;
    if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
      const nextIndex = (bk.currentPartIndex || 0) + 1;
      const nextUrl = `http://localhost:8000/api/audio/${bk.bookId}/${nextIndex}`;
      // Instantiate a background audio object to force browser to fetch/cache and backend to generate
      const prefetcher = new Audio();
      prefetcher.preload = 'auto';
      prefetcher.src = nextUrl;
    }
  }, [state.currentBook?.bookId, state.currentBook?.currentPartIndex]);

  // ── Play / pause ────────────────────────────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (state.isPlaying && (state.currentBook?.audioUrl || state.currentBook?.bookId)) {
      audio.play().catch(() => {
        // Browser blocked autoplay or src not ready yet — just pause state
        setState(prev => ({ ...prev, isPlaying: false }));
      });
    } else {
      audio.pause();
    }
  }, [state.isPlaying]);

  // ── Playback speed ──────────────────────────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) audio.playbackRate = state.speed;
  }, [state.speed]);

  // ── Volume ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) audio.volume = state.volume;
  }, [state.volume]);

  // ── Track elapsed time from real audio ─────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // Use a ref to throttle localStorage writes (every 3 seconds)
    let lastSaveTime = 0;

    const onTimeUpdate = () => {
      const currentElapsed = audio.currentTime;
      setState(prev => ({ ...prev, elapsed: currentElapsed }));

      // Throttle saving history to the books array (which triggers localStorage)
      const now = Date.now();
      if (now - lastSaveTime > 3000) {
        lastSaveTime = now;
        setBooks(prev => {
          const currentBookId = state.currentBook?.id;
          if (!currentBookId) return prev;
          
          return prev.map(bk => {
            if (bk.id === currentBookId) {
              // Calculate estimated total progress % based on parts
              let overallProgress = 0;
              if (bk.partsCount && bk.partsCount > 0) {
                 const partBaseProgress = ((bk.currentPartIndex || 0) / bk.partsCount) * 100;
                 // Assuming each part is ~4 mins for a very rough estimate to add small progression within the part
                 const withinPartProgress = Math.min((currentElapsed / 240) * (100 / bk.partsCount), 100 / bk.partsCount);
                 overallProgress = Math.round(partBaseProgress + withinPartProgress);
              }
              return { ...bk, currentTime: currentElapsed, progress: overallProgress || bk.progress };
            }
            return bk;
          });
        });
      }
    };

    const onDurationChange = () => {
      if (!audio.duration || isNaN(audio.duration)) return;
      setState(prev => {
        if (!prev.currentBook) return prev;
        const updatedBook = { ...prev.currentBook, totalTime: Math.round(audio.duration) };
        setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
        return { ...prev, currentBook: updatedBook };
      });
    };

    const onEnded = () => {
      setState(prev => {
        const bk = prev.currentBook;
        if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
          // Advance to next part!
          const nextIndex = (bk.currentPartIndex || 0) + 1;
          const updatedBook = { ...bk, currentPartIndex: nextIndex, currentTime: 0, totalTime: 0 };
          setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
          
          return { ...prev, currentBook: updatedBook, elapsed: 0 };
          // isPlaying stays true, the first useEffect will trigger the src change and auto-play
        }
        
        // Book fully finished (or no parts)
        return { ...prev, isPlaying: false, elapsed: 0 };
      });
    };

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('durationchange', onDurationChange);
    audio.addEventListener('ended', onEnded);
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('durationchange', onDurationChange);
      audio.removeEventListener('ended', onEnded);
    };
  }, []);

  // ── Actions ─────────────────────────────────────────────────────────────
  const playBook = useCallback((book: Book) => {
    setState(prev => ({
      ...prev,
      currentBook: book,
      isPlaying: true,
      elapsed: book.currentTime,
    }));
  }, []);

  const togglePlay = useCallback(() => {
    setState(prev => ({ ...prev, isPlaying: !prev.isPlaying }));
  }, []);

  const setSpeed = useCallback((speed: number) => {
    setState(prev => ({ ...prev, speed }));
  }, []);

  const setVolume = useCallback((volume: number) => {
    setState(prev => ({ ...prev, volume }));
  }, []);

  const seekForward = useCallback(() => {
    const audio = audioRef.current;
    if (audio && state.currentBook?.audioUrl) {
      audio.currentTime = Math.min(audio.currentTime + 15, audio.duration || 0);
    }
    setState(prev => ({
      ...prev,
      elapsed: Math.min(prev.elapsed + 15, prev.currentBook?.totalTime || 0),
    }));
  }, [state.currentBook?.audioUrl]);

  const seekBackward = useCallback(() => {
    const audio = audioRef.current;
    if (audio && state.currentBook?.audioUrl) {
      audio.currentTime = Math.max(audio.currentTime - 15, 0);
    }
    setState(prev => ({
      ...prev,
      elapsed: Math.max(prev.elapsed - 15, 0),
    }));
  }, [state.currentBook?.audioUrl]);

  const addBook = useCallback((title: string, audioUrl?: string, bookId?: string, partsCount?: number, voice?: string, coverUrl?: string) => {
    const newBook: Book = {
      id: Date.now().toString(),
      title,
      author: 'Documento PDF',
      coverUrl: coverUrl || 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=300&h=400&fit=crop',
      progress: 0,
      duration: partsCount ? `~${partsCount * 4}min` : '~15min',
      currentTime: 0,
      totalTime: partsCount ? 0 : 900,
      addedAt: new Date(),
      audioUrl,
      bookId,
      partsCount,
      currentPartIndex: 0,
      voice,
    };
    setBooks(prev => [newBook, ...prev]);
  }, []);

  const updateBookCategory = useCallback((id: string, category: string) => {
    setBooks(prev => prev.map(bk => bk.id === id ? { ...bk, category } : bk));
  }, []);
  
  const removeBook = useCallback((id: string) => {
    setBooks(prev => prev.filter(bk => bk.id !== id));
    setState(prev => prev.currentBook?.id === id ? { ...prev, currentBook: null, isPlaying: false, elapsed: 0 } : prev);
  }, []);

  const restartBook = useCallback((id: string) => {
    setBooks(prev => prev.map(bk => bk.id === id ? { ...bk, currentTime: 0, currentPartIndex: 0, progress: 0 } : bk));
    setState(prev => {
      if (prev.currentBook?.id === id) {
        const audio = audioRef.current;
        if (audio) audio.currentTime = 0;
        return { ...prev, currentBook: { ...prev.currentBook, currentTime: 0, currentPartIndex: 0 }, elapsed: 0, isPlaying: true };
      }
      return prev;
    });
  }, []);

  const seekToPart = useCallback((partIndex: number) => {
    setState(prev => {
      const bk = prev.currentBook;
      if (!bk || !bk.partsCount || partIndex < 0 || partIndex >= bk.partsCount) return prev;
      
      const updatedBook = { ...bk, currentPartIndex: partIndex, currentTime: 0 };
      setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
      return { ...prev, currentBook: updatedBook, elapsed: 0 };
    });
  }, []);

  return (
    <PlayerContext.Provider value={{
      ...state,
      books,
      audioRef,
      playBook,
      togglePlay,
      setSpeed,
      setVolume,
      seekForward,
      seekBackward,
      addBook,
      updateBookCategory,
      removeBook,
      restartBook,
      seekToPart,
    }}>
      {/* Hidden shared audio element — rendered once at context level */}
      <audio ref={audioRef} preload="metadata" />
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
