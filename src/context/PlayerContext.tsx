import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { Book } from '@/types/book';
import { useAuth } from './AuthContext';
import { fetchUserBooks, updateBookProgressInDb, addToPersonalLibrary, removeFromPersonalLibrary } from '@/hooks/useBooks';

interface PlayerState {
  currentBook: Book | null;
  isPlaying: boolean;
  speed: number;
  volume: number;
  elapsed: number;
  voice: string;
  searchQuery: string;
}

interface PlayerContextValue extends PlayerState {
  books: Book[]; // The user's personal library
  audioRef: React.RefObject<HTMLAudioElement>;
  playBook: (book: Book) => void;
  togglePlay: () => void;
  setSpeed: (speed: number) => void;
  setVolume: (volume: number) => void;
  seekForward: () => void;
  seekBackward: () => void;
  refreshBooks: () => Promise<void>;
  updateBookCategory: (bookId: string, category: string) => void;
  removeBook: (bookId: string) => void;
  restartBook: (bookId: string) => void;
  seekToPart: (partIndex: number) => void;
  setVoice: (voice: string) => void;
  setSearchQuery: (query: string) => void;
}

const PlayerContext = createContext<PlayerContextValue | null>(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function PlayerProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [state, setState] = useState<PlayerState>({
    currentBook: null,
    isPlaying: false,
    speed: 1,
    volume: 0.8,
    elapsed: 0,
    voice: 'es-MX-JorgeNeural',
    searchQuery: '',
  });

  const audioRef = useRef<HTMLAudioElement>(null);
  const currentBookRef = useRef<Book | null>(null);

  // Keep a ref to the current book so the audio event listeners don't use stale closures
  useEffect(() => {
    currentBookRef.current = state.currentBook;
  }, [state.currentBook]);

  // ── Load Personal Library ───────────────────────────────────────────────
  const refreshBooks = useCallback(async () => {
    if (user) {
      const dbBooks = await fetchUserBooks();
      setBooks(dbBooks);
    } else {
      setBooks([]);
    }
  }, [user]);

  useEffect(() => {
    refreshBooks();
  }, [refreshBooks]);

  // ── Sync src when currentBook changes ──────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const bk = state.currentBook;
    
    if (bk?.bookId) {
      audio.src = `${API_URL}/api/audio/${bk.bookId}/${bk.currentPartIndex || 0}?voice=${state.voice}`;
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
      const nextUrl = `${API_URL}/api/audio/${bk.bookId}/${nextIndex}?voice=${state.voice}`;
      const prefetcher = new Audio();
      prefetcher.preload = 'auto';
      prefetcher.src = nextUrl;
    }
  }, [state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.voice]);

  // ── Play / pause ────────────────────────────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (state.isPlaying && (state.currentBook?.audioUrl || state.currentBook?.bookId)) {
      audio.play().catch(() => {
        setState(prev => ({ ...prev, isPlaying: false }));
      });
    } else {
      audio.pause();
    }
  }, [state.isPlaying]);

  // ── Playback speed & Volume ──────────────────────────────────────────────
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = state.speed;
  }, [state.speed]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = state.volume;
  }, [state.volume]);

  // ── Track elapsed time & Sync Progress to Supabase ──────────────────────
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    let lastSaveTime = 0;

    const onTimeUpdate = () => {
      const currentElapsed = audio.currentTime;
      setState(prev => ({ ...prev, elapsed: currentElapsed }));

      const now = Date.now();
      if (now - lastSaveTime > 3000) {
        lastSaveTime = now;
        const bk = currentBookRef.current;
        if (!bk) return;

        let overallProgress = bk.progress;
        if (bk.partsCount && bk.partsCount > 0) {
           const partBaseProgress = ((bk.currentPartIndex || 0) / bk.partsCount) * 100;
           const withinPartProgress = Math.min((currentElapsed / 240) * (100 / bk.partsCount), 100 / bk.partsCount);
           overallProgress = Math.round(partBaseProgress + withinPartProgress);
        }

        // 1. Update React state immediately
        setBooks(prev => prev.map(b => b.id === bk.id ? { ...b, currentTime: currentElapsed, progress: overallProgress } : b));
        
        // 2. Persist to Supabase silently in background
        updateBookProgressInDb(bk.id, {
          current_time: currentElapsed,
          progress: overallProgress
        }).catch(console.error);
      }
    };

    const onDurationChange = () => {
      if (!audio.duration || isNaN(audio.duration)) return;
      const bk = currentBookRef.current;
      if (!bk) return;

      const dur = Math.round(audio.duration);
      setBooks(bks => bks.map(b => b.id === bk.id ? { ...b, totalTime: dur } : b));
      setState(prev => prev.currentBook?.id === bk.id ? { ...prev, currentBook: { ...prev.currentBook!, totalTime: dur } } : prev);
      
      updateBookProgressInDb(bk.id, { total_time: dur }).catch(console.error);
    };

    const onEnded = () => {
      const bk = currentBookRef.current;
      if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
        const nextIndex = (bk.currentPartIndex || 0) + 1;
        const updatedBook = { ...bk, currentPartIndex: nextIndex, currentTime: 0, totalTime: 0 };
        
        setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
        setState(prev => ({ ...prev, currentBook: updatedBook, elapsed: 0 }));
        
        updateBookProgressInDb(bk.id, {
          current_part_index: nextIndex,
          current_time: 0,
        }).catch(console.error);
      } else {
        setState(prev => ({ ...prev, isPlaying: false, elapsed: 0 }));
      }
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
  const playBook = useCallback(async (book: Book) => {
    // If we're playing a book that isn't in our personal library, add it
    let finalBook = book;
    setBooks(prev => {
      const isPersonal = prev.some(b => b.id === book.id);
      if (!isPersonal) {
        // Optimistic UI insert
        addToPersonalLibrary(book.id).catch(console.error);
        return [book, ...prev];
      }
      // If it exists in personal library, use the version with the correct saved progress
      finalBook = prev.find(b => b.id === book.id) || book;
      return prev;
    });

    // Short timeout to let state settle
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        currentBook: finalBook,
        isPlaying: true,
        elapsed: finalBook.currentTime,
      }));
    }, 0);
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

  const updateBookCategory = useCallback(async (id: string, category: string) => {
    // Note: Since category is now a global property in the new schema, this would theoretically update global_books.
    // For safety, we only update state locally unless we add a specific global update method if the user is admin.
    setBooks(prev => prev.map(bk => bk.id === id ? { ...bk, category } : bk));
  }, []);
  
  const removeBook = useCallback(async (id: string) => {
    setBooks(prev => prev.filter(bk => bk.id !== id));
    setState(prev => prev.currentBook?.id === id ? { ...prev, currentBook: null, isPlaying: false, elapsed: 0 } : prev);
    await removeFromPersonalLibrary(id);
  }, []);

  const restartBook = useCallback(async (id: string) => {
    setBooks(prev => prev.map(bk => bk.id === id ? { ...bk, currentTime: 0, currentPartIndex: 0, progress: 0 } : bk));
    setState(prev => {
      if (prev.currentBook?.id === id) {
        const audio = audioRef.current;
        if (audio) audio.currentTime = 0;
        return { ...prev, currentBook: { ...prev.currentBook, currentTime: 0, currentPartIndex: 0 }, elapsed: 0, isPlaying: true };
      }
      return prev;
    });
    await updateBookProgressInDb(id, { current_time: 0, current_part_index: 0, progress: 0 });
  }, []);

  const seekToPart = useCallback(async (partIndex: number) => {
    setState(prev => {
      const bk = prev.currentBook;
      if (!bk || !bk.partsCount || partIndex < 0 || partIndex >= bk.partsCount) return prev;
      
      const updatedBook = { ...bk, currentPartIndex: partIndex, currentTime: 0 };
      setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
      updateBookProgressInDb(bk.id, { current_part_index: partIndex, current_time: 0 }).catch(console.error);
      
      return { ...prev, currentBook: updatedBook, elapsed: 0 };
    });
  }, []);

  const setVoice = useCallback((voice: string) => {
    setState(prev => ({ ...prev, voice }));
  }, []);

  const setSearchQuery = useCallback((searchQuery: string) => {
    setState(prev => ({ ...prev, searchQuery }));
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
      refreshBooks,
      updateBookCategory,
      removeBook,
      restartBook,
      seekToPart,
      setVoice,
      setSearchQuery,
    }}>
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
