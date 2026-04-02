import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { TopBar } from './TopBar';
import { AudioPlayer } from './AudioPlayer';
import { MobileBottomNav } from './MobileBottomNav';
import { PlayerProvider, usePlayer } from '@/context/PlayerContext';
import { ReactNode } from 'react';

function LayoutInner({ children }: { children: ReactNode }) {
  const { currentBook } = usePlayer();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <main className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <div className={`flex-1 p-4 md:p-6 overflow-auto ${currentBook ? 'pb-44 md:pb-28' : 'pb-24 md:pb-6'}`}>
            {children}
          </div>
        </main>
      </div>
      <MobileBottomNav />
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
