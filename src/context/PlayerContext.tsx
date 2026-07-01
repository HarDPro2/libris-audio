import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { Book } from '@/types/book';
import { useAuth } from './AuthContext';
import { fetchUserBooks, updateBookProgressInDb, addToPersonalLibrary, removeFromPersonalLibrary, deleteGlobalBook as deleteGlobalBookApi, updateGlobalBook as updateGlobalBookApi } from '@/hooks/useBooks';

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
  deleteGlobalBook: (book: Book) => Promise<void>;
  updateGlobalBookMeta: (book: Book, patch: { title?: string; category?: string }) => Promise<void>;
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
  const prefetchRef = useRef<HTMLAudioElement>(null);
  const currentBookRef = useRef<Book | null>(null);
  const isPlayingRef = useRef<boolean>(state.isPlaying);
  const voiceRef = useRef<string>(state.voice);
  // Counter-based guard (not boolean) so it survives React 18's batched
  // double-renders: onEnded sets it to 2, each effect run decrements by 1
  // and skips if still > 0. This guarantees both re-render passes are blocked.
  const isTransitioningRef = useRef<number>(0);

  useEffect(() => {
    isPlayingRef.current = state.isPlaying;
  }, [state.isPlaying]);

  useEffect(() => {
    voiceRef.current = state.voice;
  }, [state.voice]);

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
  // IMPORTANT: This effect is GUARDED by isTransitioningRef.
  // When onEnded() handles an auto-advance between parts, it sets
  // isTransitioningRef.current = true before calling setState. This prevents
  // this effect from fighting with onEnded's direct audio manipulation,
  // which was the root cause of paragraph-skipping bugs.
  useEffect(() => {
    // If onEnded is already managing the transition, consume one guard token
    // and skip. Using a counter (not boolean) handles React 18 batched double-renders.
    if (isTransitioningRef.current > 0) {
      isTransitioningRef.current -= 1;
      return;
    }

    const audio = audioRef.current;
    if (!audio) return;
    const bk = state.currentBook;
    
    let expectedSrc = '';
    if (bk?.bookId) {
      expectedSrc = `${API_URL}/api/audio/${bk.bookId}/${bk.currentPartIndex || 0}?voice=${state.voice}`;
    } else if (bk?.audioUrl) {
      expectedSrc = bk.audioUrl;
    }

    if (expectedSrc && audio.src !== expectedSrc) {
      audio.src = expectedSrc;
      audio.load();
    } else if (!expectedSrc) {
      audio.src = '';
      return;
    }

    const handleCanPlay = () => {
      // Only seek to saved position for the INITIAL load of a book (currentTime > 1s)
      // Never seek during auto-advance transitions (handled by onEnded)
      if (bk?.currentTime && bk.currentTime > 1 && audio.currentTime < 1) {
        audio.currentTime = bk.currentTime;
      }
      if (isPlayingRef.current) {
        audio.play().catch(() => setState(prev => ({ ...prev, isPlaying: false })));
      }
    };

    audio.addEventListener('canplay', handleCanPlay);
    return () => audio.removeEventListener('canplay', handleCanPlay);
  }, [state.currentBook?.id, state.currentBook?.audioUrl, state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.voice]);

  // ── Prefetch next part ──────────────────────────────────────────────────
  useEffect(() => {
    const bk = state.currentBook;
    if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
      const nextIndex = (bk.currentPartIndex || 0) + 1;
      const nextUrl = `${API_URL}/api/audio/${bk.bookId}/${nextIndex}?voice=${state.voice}`;
      
      // Use standard fetch to reliably cache the next part in the browser
      fetch(nextUrl).catch(console.error);

      // And also preload it in a hidden audio element to give hints to mobile browsers
      if (prefetchRef.current && prefetchRef.current.src !== nextUrl) {
        prefetchRef.current.src = nextUrl;
        prefetchRef.current.load();
      }
    }
  }, [state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.voice]);

  // ── Play / pause ────────────────────────────────────────────────────────
  // GUARD: Never call play() here if onEnded is handling a part transition.
  // onEnded sets isTransitioningRef > 0, so we check it before acting.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    // Skip if a transition is in progress — onEnded manages play() directly
    if (isTransitioningRef.current > 0) return;
    if (state.isPlaying && (state.currentBook?.audioUrl || state.currentBook?.bookId)) {
      audio.play().catch((e) => {
        console.warn('Autoplay prevented or interrupted:', e);
        setState(prev => ({ ...prev, isPlaying: false }));
      });
    } else {
      audio.pause();
    }
  }, [state.isPlaying]);

  // ── Media Session API (Integración en OS y Pantalla de Bloqueo) ─────────
  useEffect(() => {
    if ('mediaSession' in navigator && state.currentBook) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: state.currentBook.title,
        artist: state.currentBook.author || 'Libris Audio',
        artwork: [
          { src: state.currentBook.coverUrl || '', sizes: '512x512', type: 'image/png' },
        ]
      });
    }
  }, [state.currentBook]);

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
    let lastDbSaveTime = 0;

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

        // 1. Update React state immediately every 3 seconds for UI responsiveness
        setBooks(prev => prev.map(b => b.id === bk.id ? { ...b, currentTime: currentElapsed, progress: overallProgress } : b));
        
        // 2. Persist to Supabase only every 15 seconds to avoid network starvation/lag on mobile
        if (now - lastDbSaveTime > 15000) {
          lastDbSaveTime = now;
          updateBookProgressInDb(bk.id, {
            current_time: currentElapsed,
            progress: overallProgress
          }).catch(console.error);
        }
      }
    };

    const onDurationChange = () => {
      if (!audio.duration || isNaN(audio.duration)) return;
      const bk = currentBookRef.current;
      if (!bk) return;

      const dur = Math.round(audio.duration);
      // Avoid duplicate DB writes: only persist if duration actually changed
      if (bk.totalTime === dur) return;

      setBooks(bks => bks.map(b => b.id === bk.id ? { ...b, totalTime: dur } : b));
      setState(prev => prev.currentBook?.id === bk.id ? { ...prev, currentBook: { ...prev.currentBook!, totalTime: dur } } : prev);
      // Update currentBookRef immediately so the guard above works on next fire
      currentBookRef.current = { ...bk, totalTime: dur };

      updateBookProgressInDb(bk.id, { total_time: dur }).catch(console.error);
    };

    const onEnded = () => {
      const bk = currentBookRef.current;
      if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
        const nextIndex = (bk.currentPartIndex || 0) + 1;
        const nextUrl = `${API_URL}/api/audio/${bk.bookId}/${nextIndex}?voice=${voiceRef.current}`;
        
        // Step 1: Directly control the audio element BEFORE React state update.
        // This is the correct sequence for mobile browsers (Brave, Safari, Opera):
        // the play() call must be as close as possible to the user's interaction (or the ended event).
        if (audio) {
          audio.src = nextUrl;
          audio.load();
          // Use canplaythrough for reliability before calling play()
          const playWhenReady = () => {
            audio.play().catch(e => {
              console.warn('[onEnded] play() blocked:', e);
              setState(prev => ({ ...prev, isPlaying: false }));
            });
            audio.removeEventListener('canplay', playWhenReady);
          };
          audio.addEventListener('canplay', playWhenReady);
          // Also attempt immediate play; some browsers can start instantly from cache
          audio.play().catch(() => {
            // If immediate play fails, the canplay listener above will retry
          });
        }

        const updatedBook = { ...bk, currentPartIndex: nextIndex, currentTime: 0, totalTime: 0 };
        currentBookRef.current = updatedBook;

        // Set guard to 2 tokens: enough to absorb React 18 batched double-renders
        // from the two setState calls below (setBooks + setState).
        isTransitioningRef.current = 2;

        // Step 3: Update React state so the UI reflects the new part.
        setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
        setState(prev => ({ ...prev, currentBook: updatedBook, elapsed: 0 }));
        
        // Step 4: Persist to DB
        updateBookProgressInDb(bk.id, {
          current_part_index: nextIndex,
          current_time: 0,
        }).catch(console.error);
      } else {
        // Book finished
        setState(prev => ({ ...prev, isPlaying: false, elapsed: 0 }));
        updateBookProgressInDb(bk!.id, {
          current_part_index: 0,
          current_time: 0,
          progress: 100,
        }).catch(console.error);
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
    // 🔥 MOBILE BROWSER FIX (Brave/Safari/Opera) 🔥
    // Set src and call play() SYNCHRONOUSLY inside the user gesture event handler.
    if (audioRef.current) {
      const url = book.bookId
        ? `${API_URL}/api/audio/${book.bookId}/${book.currentPartIndex || 0}?voice=${voiceRef.current}`
        : book.audioUrl || '';
      if (url && audioRef.current.src !== url) {
        audioRef.current.src = url;
        audioRef.current.load();
      }
      audioRef.current.play().catch(e => console.warn('Autoplay blocked during user gesture:', e));
    }

    // Determine the correct book object to use (with saved progress if in library)
    // IMPORTANT: We read from the books array via a ref-captured snapshot OUTSIDE
    // the setState setter to avoid the antipattern of mutating variables inside setters.
    setBooks(prev => {
      const isPersonal = prev.some(b => b.id === book.id);
      if (!isPersonal) {
        addToPersonalLibrary(book.id).catch(console.error);
        // Schedule state update with the new book after this setter returns
        setTimeout(() => {
          setState(prevState => ({
            ...prevState,
            currentBook: book,
            isPlaying: true,
            elapsed: book.currentTime || 0,
          }));
        }, 0);
        return [book, ...prev];
      }
      // Use the library version (has correct saved progress)
      const savedBook = prev.find(b => b.id === book.id) || book;
      setTimeout(() => {
        setState(prevState => ({
          ...prevState,
          currentBook: savedBook,
          isPlaying: true,
          elapsed: savedBook.currentTime || 0,
        }));
      }, 0);
      return prev;
    });
  }, []);

  const togglePlay = useCallback(() => {
    const currentlyPlaying = isPlayingRef.current;
    if (audioRef.current) {
      if (!currentlyPlaying) {
        audioRef.current.play().catch(console.warn);
      } else {
        audioRef.current.pause();
      }
    }
    setState(prev => ({ ...prev, isPlaying: !currentlyPlaying }));
  }, []);

  const setSpeed = useCallback((speed: number) => {
    setState(prev => ({ ...prev, speed }));
  }, []);

  const setVolume = useCallback((volume: number) => {
    setState(prev => ({ ...prev, volume }));
  }, []);

  const seekForward = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = Math.min(audio.currentTime + 15, audio.duration || 0);
      setState(prev => ({ ...prev, elapsed: audio.currentTime }));
    }
  }, []);

  const seekBackward = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = Math.max(audio.currentTime - 15, 0);
      setState(prev => ({ ...prev, elapsed: audio.currentTime }));
    }
  }, []);

  // Set Media Session Actions
  useEffect(() => {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.setActionHandler('play', togglePlay);
      navigator.mediaSession.setActionHandler('pause', togglePlay);
      navigator.mediaSession.setActionHandler('seekforward', seekForward);
      navigator.mediaSession.setActionHandler('seekbackward', seekBackward);
    }
  }, [togglePlay, seekForward, seekBackward]);

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

  // ── Owner-only: delete a book from the global catalog ────────────────────
  const deleteGlobalBook = useCallback(async (book: Book) => {
    if (!book.bookId) return;
    await deleteGlobalBookApi(book.bookId);
    // Remove from local state immediately for snappy UX
    setBooks(prev => prev.filter(b => b.id !== book.id));
    setState(prev =>
      prev.currentBook?.id === book.id
        ? { ...prev, currentBook: null, isPlaying: false, elapsed: 0 }
        : prev
    );
  }, []);

  // ── Owner-only: update title/category of a global book ───────────────────
  const updateGlobalBookMeta = useCallback(async (
    book: Book,
    patch: { title?: string; category?: string }
  ) => {
    if (!book.bookId) return;
    await updateGlobalBookApi(book.bookId, patch);
    // Optimistic local update
    setBooks(prev => prev.map(b =>
      b.id === book.id ? { ...b, ...patch } : b
    ));
    setState(prev =>
      prev.currentBook?.id === book.id
        ? { ...prev, currentBook: { ...prev.currentBook!, ...patch } }
        : prev
    );
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
      deleteGlobalBook,
      updateGlobalBookMeta,
    }}>
      <audio ref={audioRef} preload="metadata" />
      <audio ref={prefetchRef} preload="auto" style={{ display: 'none' }} />
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
