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

  // ── Ping-Pong Double Buffering Audio Refs ──
  const audioRef0 = useRef<HTMLAudioElement>(null);
  const audioRef1 = useRef<HTMLAudioElement>(null);
  const activeAudioIndex = useRef<0 | 1>(0);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  // We expose activeAudioRef as the traditional `audioRef` so UI components (like progress bar) stay compatible.
  const exportedAudioRef = useRef<HTMLAudioElement>(null);

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

  // Keep exportedAudioRef pointing to the true active DOM element
  useEffect(() => {
    const leader = activeAudioIndex.current === 0 ? audioRef0.current : audioRef1.current;
    if (leader) {
      activeAudioRef.current = leader;
      (exportedAudioRef as any).current = leader;
    }
  });

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
    const audio0 = audioRef0.current;
    const audio1 = audioRef1.current;
    if (!audio0 || !audio1) return;

    // Set initial active audio
    if (!activeAudioRef.current) {
       activeAudioRef.current = audio0;
       (exportedAudioRef as any).current = audio0;
    }

    let lastSaveTime = 0;
    let lastDbSaveTime = 0;

    const onTimeUpdate = (e: Event) => {
      const target = e.target as HTMLAudioElement;
      // ONLY process time updates from the LEADER audio. Ignore prefetcher events.
      if (target !== activeAudioRef.current) return;

      const currentElapsed = target.currentTime;
      setState(prev => ({ ...prev, elapsed: currentElapsed }));

      if ('mediaSession' in navigator && 'setPositionState' in navigator.mediaSession) {
        const dur = target.duration;
        if (dur && isFinite(dur) && currentElapsed <= dur) {
          try {
            navigator.mediaSession.setPositionState({
              duration: dur,
              playbackRate: target.playbackRate || 1,
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

    const onDurationChange = (e: Event) => {
      const target = e.target as HTMLAudioElement;
      if (target !== activeAudioRef.current) return;
      if (!target.duration || isNaN(target.duration)) return;
      
      const bk = currentBookRef.current;
      if (!bk) return;

      const dur = Math.round(target.duration);
      if (bk.totalTime === dur) return;

      setBooks(bks => bks.map(b => b.id === bk.id ? { ...b, totalTime: dur } : b));
      setState(prev => prev.currentBook?.id === bk.id ? { ...prev, currentBook: { ...prev.currentBook!, totalTime: dur } } : prev);
      currentBookRef.current = { ...bk, totalTime: dur };

      updateBookProgressInDb(bk.id, { total_time: dur }).catch(console.error);
    };

    const onEnded = (e: Event) => {
      const target = e.target as HTMLAudioElement;
      if (target !== activeAudioRef.current) return;

      const bk = currentBookRef.current;
      if (bk && bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) < bk.partsCount - 1) {
        const nextIndex = (bk.currentPartIndex || 0) + 1;

        console.log(`[Ping-Pong] Part ${bk.currentPartIndex} ended. Swapping to native buffer for Part ${nextIndex}.`);
        
        // ── SWAP LEADER AND PREFETCHER ──
        activeAudioIndex.current = activeAudioIndex.current === 0 ? 1 : 0;
        activeAudioRef.current = activeAudioIndex.current === 0 ? audioRef0.current : audioRef1.current;
        (exportedAudioRef as any).current = activeAudioRef.current;
        
        const newLeader = activeAudioRef.current;
        const newPrefetch = activeAudioIndex.current === 0 ? audioRef1.current : audioRef0.current;

        if (newLeader) {
           const expectedSrc = `${API_URL}/api/audio/${bk.bookId}/${nextIndex}?voice=${voiceRef.current}`;
           // Ensure it has the right src (in case prefetch failed or didn't run)
           if (!newLeader.src || !newLeader.src.includes(expectedSrc)) {
              newLeader.src = expectedSrc;
              newLeader.load();
           }
           newLeader.play().catch(err => {
              console.warn('[Ping-Pong] play() blocked:', err);
              setState(prev => ({ ...prev, isPlaying: false }));
           });
        }

        // ── QUEUE NATIVE PREFETCH FOR THE NEXT-NEXT TRACK ──
        if (newPrefetch && nextIndex + 1 < bk.partsCount) {
           const nextNextSrc = `${API_URL}/api/audio/${bk.bookId}/${nextIndex + 1}?voice=${voiceRef.current}`;
           newPrefetch.src = nextNextSrc;
           newPrefetch.load(); // Native preload!
           console.log(`[Ping-Pong] Queued native prefetch for Part ${nextIndex + 1}`);
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
      const target = e.target as HTMLAudioElement;
      if (target !== activeAudioRef.current) return;
      const err = target.error;
      if (err && (err.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED || err.code === MediaError.MEDIA_ERR_NETWORK)) {
        console.warn('[Audio] Unrecoverable source error (book may have been deleted):', err.message);
        setState(prev => ({ ...prev, isPlaying: false }));
      }
    };

    const attach = (a: HTMLAudioElement) => {
      a.addEventListener('timeupdate', onTimeUpdate);
      a.addEventListener('durationchange', onDurationChange);
      a.addEventListener('ended', onEnded);
      a.addEventListener('error', onError);
    };
    const detach = (a: HTMLAudioElement) => {
      a.removeEventListener('timeupdate', onTimeUpdate);
      a.removeEventListener('durationchange', onDurationChange);
      a.removeEventListener('ended', onEnded);
      a.removeEventListener('error', onError);
    };

    attach(audio0); attach(audio1);
    return () => { detach(audio0); detach(audio1); };
  }, []);

  // ── 2. Primary Playback & Prefetch Initializer ──
  useEffect(() => {
    if (isTransitioningRef.current > 0) {
      isTransitioningRef.current -= 1;
      return;
    }

    const leader = activeAudioRef.current;
    const prefetch = activeAudioIndex.current === 0 ? audioRef1.current : audioRef0.current;
    if (!leader || !prefetch) return;

    const bk = state.currentBook;
    if (!bk) {
      leader.src = '';
      prefetch.src = '';
      return;
    }

    let expectedSrc = '';
    if (bk.bookId) {
      expectedSrc = `${API_URL}/api/audio/${bk.bookId}/${bk.currentPartIndex || 0}?voice=${state.voice}`;
    } else if (bk.audioUrl) {
      expectedSrc = bk.audioUrl;
    }

    let changedLeader = false;
    if (expectedSrc && (!leader.src || !leader.src.includes(expectedSrc))) {
      leader.src = expectedSrc;
      leader.load();
      changedLeader = true;
    } else if (!expectedSrc) {
      leader.src = '';
      prefetch.src = '';
      return;
    }

    // Setup initial native prefetch for the next track
    if (bk.bookId && bk.partsCount && (bk.currentPartIndex || 0) + 1 < bk.partsCount) {
      const nextSrc = `${API_URL}/api/audio/${bk.bookId}/${(bk.currentPartIndex || 0) + 1}?voice=${state.voice}`;
      if (!prefetch.src || !prefetch.src.includes(nextSrc)) {
        prefetch.src = nextSrc;
        prefetch.load();
        console.log(`[Ping-Pong] Queued native prefetch for Part ${(bk.currentPartIndex || 0) + 1}`);
      }
    }

    // Handle resume from progress
    if (changedLeader) {
      const handleCanPlay = () => {
        if (bk.currentTime && bk.currentTime > 1 && leader.currentTime < 1) {
          leader.currentTime = bk.currentTime;
        }
        if (isPlayingRef.current) {
          leader.play().catch(() => setState(prev => ({ ...prev, isPlaying: false })));
        }
        leader.removeEventListener('canplay', handleCanPlay);
      };
      leader.addEventListener('canplay', handleCanPlay);
    }
  }, [state.currentBook?.id, state.currentBook?.audioUrl, state.currentBook?.bookId, state.currentBook?.currentPartIndex, state.voice]);

  // ── 3. Handle external isPlaying toggles ──
  useEffect(() => {
    const leader = activeAudioRef.current;
    if (!leader) return;
    if (isTransitioningRef.current > 0) return;
    if (state.isPlaying && (state.currentBook?.audioUrl || state.currentBook?.bookId)) {
      leader.play().catch((e) => {
        console.warn('Autoplay prevented or interrupted:', e);
        setState(prev => ({ ...prev, isPlaying: false }));
      });
    } else {
      leader.pause();
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
    if (audioRef0.current) audioRef0.current.playbackRate = state.speed;
    if (audioRef1.current) audioRef1.current.playbackRate = state.speed;
  }, [state.speed]);

  useEffect(() => {
    if (audioRef0.current) audioRef0.current.volume = state.volume;
    if (audioRef1.current) audioRef1.current.volume = state.volume;
  }, [state.volume]);

  const playBook = useCallback(async (book: Book) => {
    const leader = activeAudioRef.current;
    if (leader) {
      const url = book.bookId
        ? `${API_URL}/api/audio/${book.bookId}/${book.currentPartIndex || 0}?voice=${voiceRef.current}`
        : book.audioUrl || '';
      if (url && (!leader.src || !leader.src.includes(url))) {
        leader.src = url;
        leader.load();
      }
      leader.play().catch(e => console.warn('Autoplay blocked during user gesture:', e));
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
    const leader = activeAudioRef.current;
    if (leader) {
      if (!currentlyPlaying) {
        leader.play().catch(console.warn);
      } else {
        leader.pause();
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
    const leader = activeAudioRef.current;
    if (leader) {
      leader.currentTime = Math.min(leader.currentTime + 15, leader.duration || 0);
      setState(prev => ({ ...prev, elapsed: leader.currentTime }));
    }
  }, []);

  const seekBackward = useCallback(() => {
    const leader = activeAudioRef.current;
    if (leader) {
      leader.currentTime = Math.max(leader.currentTime - 15, 0);
      setState(prev => ({ ...prev, elapsed: leader.currentTime }));
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
        const leader = activeAudioRef.current;
        if (leader) leader.currentTime = 0;
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
      audioRef: exportedAudioRef,
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
      <audio ref={audioRef0} preload="auto" style={{ display: 'none' }} crossOrigin="anonymous" />
      <audio ref={audioRef1} preload="auto" style={{ display: 'none' }} crossOrigin="anonymous" />
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
