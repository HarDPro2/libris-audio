import { Book } from '@/types/book';

export const sampleBooks: Book[] = [
  {
    id: '1',
    title: 'Dune',
    author: 'Frank Herbert',
    coverUrl: 'https://images.unsplash.com/photo-1547555999-14e818e09e33?w=300&h=400&fit=crop',
    progress: 65,
    duration: '21h 2min',
    currentTime: 49278,
    totalTime: 75720,
    addedAt: new Date('2024-12-01'),
  },
  {
    id: '2',
    title: 'Atomic Habits',
    author: 'James Clear',
    coverUrl: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop',
    progress: 32,
    duration: '5h 35min',
    currentTime: 6432,
    totalTime: 20100,
    addedAt: new Date('2025-01-15'),
  },
  {
    id: '3',
    title: 'Deep Work',
    author: 'Cal Newport',
    coverUrl: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300&h=400&fit=crop',
    progress: 88,
    duration: '7h 44min',
    currentTime: 24518,
    totalTime: 27840,
    addedAt: new Date('2025-02-10'),
  },
];
