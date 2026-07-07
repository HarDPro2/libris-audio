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
  books: Book[];
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

  // ── Cache Warmer Pattern Refs ──
  // The SINGLE audio element that actually plays (holds user gesture)
  const audioRef = useRef<HTMLAudioElement>(null);
  // The invisible audio element used ONLY to download the next track natively
  const prefetchRef = useRef<HTMLAudioElement>(null);

  const currentBookRef = useRef<Book | null>(null);
  const isPlayingRef = useRef<boolean>(state.isPlaying);
  const voiceRef = useRef<string>(state.voice);
  const isTransitioningRef = useRef<number>(0);

  // Sync refs that are used inside event listeners to avoid stale closures
  useEffect(() => {
    isPlayingRef.current = state.isPlaying;
  }, [state.isPlaying]);

  useEffect(() => {
    voiceRef.current = state.voice;
  }, [state.voice]);

  useEffect(() => {
    currentBookRef.current = state.currentBook;
  }, [state.currentBook]);

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

  // ── 1. Setup Audio Event Listeners ──
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    let lastSaveTime = 0;
    let lastDbSaveTime = 0;

    const onTimeUpdate = () => {
      const currentElapsed = audio.currentTime;
      setState(prev => ({ ...prev, elapsed: currentElapsed }));

      if ('mediaSession' in navigator && 'setPositionState' in navigator.mediaSession) {
        const dur = audio.duration;
        if (dur && isFinite(dur) && currentElapsed <= dur) {
          try {
            navigator.mediaSession.setPositionState({
              duration: dur,
              playbackRate: audio.playbackRate || 1,
              position: currentElapsed,
            });
          } catch { /* ignore invalid position states */ }
        }
      }

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

        setBooks(prev => prev.map(b => b.id === bk.id ? { ...b, currentTime: currentElapsed, progress: overallProgress } : b));

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
      if (bk.totalTime === dur) return;

      setBooks(bks => bks.map(b => b.id === bk.id ? { ...b, totalTime: dur } : b));
      setState(prev => prev.currentBook?.id === bk.id ? { ...prev, currentBook: { ...prev.currentBook!, totalTime: dur } } : prev);
      currentBookRef.current = { ...bk, totalTime: dur };

      updateBookProgressInDb(bk.id, { total_time: dur }).catch(console.error);
    };

    const onEnded = () => {
      const bk = currentBookRef.current;
      if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
        const nextIndex = (bk.currentPartIndex || 0) + 1;

        console.log(`[Cache Warmer] Part ${bk.currentPartIndex} ended. Pulling Part ${nextIndex} from network/cache.`);
        
        // ── 1. ASSIGN SRC TO SAME PLAYER AND PLAY IMMEDIATELY ──
        // Because prefetchRef already downloaded it, the browser should load it from disk cache instantly.
        // And because it's the SAME audio element that just finished playing, Autoplay is allowed.
        const expectedSrc = `${API_URL}/api/audio/${bk.bookId}/${nextIndex}?voice=${voiceRef.current}`;
        
        // Set and play instantly
        audio.src = expectedSrc;
        audio.load();
        audio.play().catch(err => {
           console.warn('[Cache Warmer] play() blocked despite using same element:', err);
           setState(prev => ({ ...prev, isPlaying: false }));
        });

        // ── 2. QUEUE NATIVE PREFETCH FOR THE NEXT-NEXT TRACK ──
        if (prefetchRef.current && nextIndex + 1 < bk.partsCount) {
           const nextNextSrc = `${API_URL}/api/audio/${bk.bookId}/${nextIndex + 1}?voice=${voiceRef.current}`;
           prefetchRef.current.src = nextNextSrc;
           prefetchRef.current.load(); // Native preload!
           console.log(`[Cache Warmer] Queued native prefetch for Part ${nextIndex + 1}`);
        }

        const updatedBook = { ...bk, currentPartIndex: nextIndex, currentTime: 0, totalTime: 0 };
        currentBookRef.current = updatedBook;
        
        isTransitioningRef.current = 2; // Prevent primary useEffect from interfering

        setBooks(bks => bks.map(b => b.id === updatedBook.id ? updatedBook : b));
        setState(prev => ({ ...prev, currentBook: updatedBook, elapsed: 0 }));

        updateBookProgressInDb(bk.id, {
          current_part_index: nextIndex,
          current_time: 0,
        }).catch(console.error);
      } else {
        setState(prev => ({ ...prev, isPlaying: false, elapsed: 0 }));
        updateBookProgressInDb(bk!.id, {
          current_part_index: 0,
          current_time: 0,
          progress: 100,
        }).catch(console.error);
      }
    };

    const onError = (e: Event) => {
      const err = (e.target as HTMLAudioElement).error;
      if (err && (err.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED || err.code === MediaError.MEDIA_ERR_NETWORK)) {
        console.warn('[Audio] Unrecoverable source error (book may have been deleted):', err.message);
        setState(prev => ({ ...prev, isPlaying: false }));
      }
    };

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('durationchange', onDurationChange);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('error', onError);
    
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('durationchange', onDurationChange);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('error', onError);
    };
  }, []);

  // ── 2. Primary Playback & Prefetch Initializer ──
  useEffect(() => {
    if (isTransitioningRef.current > 0) {
      isTransitioningRef.current -= 1;
      return;
    }

    const audio = audioRef.current;
    if (!audio) return;

    const bk = state.currentBook;
    if (!bk) {
      audio.src = '';
      if (prefetchRef.current) prefetchRef.current.src = '';
      return;
    }

    let expectedSrc = '';
    if (bk.bookId) {
      expectedSrc = `${API_URL}/api/audio/${bk.bookId}/${bk.currentPartIndex || 0}?voice=${state.voice}`;
    } else if (bk.audioUrl) {
      expectedSrc = bk.audioUrl;
    }

    let changedSrc = false;
    if (expectedSrc && (!audio.src || !audio.src.includes(expectedSrc))) {
      audio.src = expectedSrc;
      audio.load();
      changedSrc = true;
    } else if (!expectedSrc) {
      audio.src = '';
      if (prefetchRef.current) prefetchRef.current.src = '';
      return;
    }

    // Setup initial native prefetch for the next track
    if (prefetchRef.current && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) + 1 < bk.partsCount) {
      const nextSrc = `${API_URL}/api/audio/${bk.bookId}/${(bk.currentPartIndex || 0) + 1}?voice=${state.voice}`;
      if (!prefetchRef.current.src || !prefetchRef.current.src.includes(nextSrc)) {
        prefetchRef.current.src = nextSrc;
        prefetchRef.current.load();
        console.log(`[Cache Warmer] Queued native prefetch for Part ${(bk.currentPartIndex || 0) + 1}`);
      }
    }

    // Handle resume from progress
    if (changedSrc) {
      const handleCanPlay = () => {
        if (bk.currentTime && bk.currentTime > 1 && audio.currentTime < 1) {
          audio.currentTime = bk.currentTime;
        }
        if (isPlayingRef.current) {
          audio.play().catch(() => setState(prev => ({ ...prev, isPlaying: false })));
        }
        audio.removeEventListener('canplay', handleCanPlay);
      };
      audio.addEventListener('canplay', handleCanPlay);
    }
  }, [state.currentBook?.id, state.currentBook?.audioUrl, state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.voice]);

  // ── 3. Handle external isPlaying toggles ──
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
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

  useEffect(() => {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = state.isPlaying ? 'playing' : 'paused';
    }
  }, [state.isPlaying]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = state.speed;
  }, [state.speed]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = state.volume;
  }, [state.volume]);

  const playBook = useCallback(async (book: Book) => {
    const audio = audioRef.current;
    if (audio) {
      const url = book.bookId
        ? `${API_URL}/api/audio/${book.bookId}/${book.currentPartIndex || 0}?voice=${voiceRef.current}`
        : book.audioUrl || '';
      if (url && (!audio.src || !audio.src.includes(url))) {
        audio.src = url;
        audio.load();
      }
      audio.play().catch(e => console.warn('Autoplay blocked during user gesture:', e));
    }

    setBooks(prev => {
      const isPersonal = prev.some(b => b.id === book.id);
      if (!isPersonal) {
        addToPersonalLibrary(book.id).catch(console.error);
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
    const audio = audioRef.current;
    if (audio) {
      if (!currentlyPlaying) {
        audio.play().catch(console.warn);
      } else {
        audio.pause();
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

  const updateBookCategory = useCallback(async (id: string, category: string) => {
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

  useEffect(() => {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.setActionHandler('play', togglePlay);
      navigator.mediaSession.setActionHandler('pause', togglePlay);
      navigator.mediaSession.setActionHandler('seekforward', seekForward);
      navigator.mediaSession.setActionHandler('seekbackward', seekBackward);

      const goToPart = (delta: number) => {
        const bk = currentBookRef.current;
        if (!bk || !bk.partsCount) return;
        const target = (bk.currentPartIndex || 0) + delta;
        if (target < 0 || target >= bk.partsCount) return;
        seekToPart(target);
      };
      try {
        navigator.mediaSession.setActionHandler('nexttrack', () => goToPart(1));
        navigator.mediaSession.setActionHandler('previoustrack', () => goToPart(-1));
      } catch {
        /* Some browsers don't support these actions — safe to ignore */
      }
    }
  }, [togglePlay, seekForward, seekBackward, seekToPart]);

  const setVoice = useCallback((voice: string) => {
    setState(prev => ({ ...prev, voice }));
  }, []);

  const setSearchQuery = useCallback((searchQuery: string) => {
    setState(prev => ({ ...prev, searchQuery }));
  }, []);

  const deleteGlobalBook = useCallback(async (book: Book) => {
    if (!book.bookId) return;
    await deleteGlobalBookApi(book.bookId);
    setBooks(prev => prev.filter(b => b.id !== book.id));
    setState(prev =>
      prev.currentBook?.id === book.id
        ? { ...prev, currentBook: null, isPlaying: false, elapsed: 0 }
        : prev
    );
  }, []);

  const updateGlobalBookMeta = useCallback(async (
    book: Book,
    patch: { title?: string; category?: string }
  ) => {
    if (!book.bookId) return;
    await updateGlobalBookApi(book.bookId, patch);
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
      <audio ref={audioRef} preload="auto" crossOrigin="anonymous" />
      <audio ref={prefetchRef} preload="auto" style={{ display: 'none' }} crossOrigin="anonymous" />
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
