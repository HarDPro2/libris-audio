export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  progress: number; // 0-100
  duration: string;
  currentTime: number; // seconds
  totalTime: number; // seconds
  addedAt: Date;
  isProcessing?: boolean;
  audioUrl?: string; // URL of the generated MP3 from the backend
  bookId?: string;
  partsCount?: number;
  currentPartIndex?: number;
  voice?: string;
  category?: string;
}
