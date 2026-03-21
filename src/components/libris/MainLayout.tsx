import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { TopBar } from './TopBar';
import { AudioPlayer } from './AudioPlayer';
import { PlayerProvider, usePlayer } from '@/context/PlayerContext';
import { ReactNode } from 'react';

function LayoutInner({ children }: { children: ReactNode }) {
  const { currentBook } = usePlayer();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <main className="flex-1 flex flex-col">
          <TopBar />
          <div className={`flex-1 p-6 overflow-auto ${currentBook ? 'pb-28' : ''}`}>
            {children}
          </div>
        </main>
      </div>
      <AudioPlayer />
    </SidebarProvider>
  );
}

export function MainLayout({ children }: { children: ReactNode }) {
  return (
    <PlayerProvider>
      <LayoutInner>{children}</LayoutInner>
    </PlayerProvider>
  );
}
