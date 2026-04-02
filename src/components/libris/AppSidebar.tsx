import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Home, BookOpen, Upload, Clock, Settings, AudioLines, Download, LogOut, User as UserIcon } from 'lucide-react';
import AuthorSignature from '@/components/common/Signature/AuthorSignature';
import { useAuth } from '@/context/AuthContext';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

const navItems = [
  { title: 'Home', url: '/', icon: Home },
  { title: 'Mi Biblioteca', url: '/library', icon: BookOpen },
  { title: 'Subir PDF', url: '/upload', icon: Upload },
  { title: 'Historial', url: '/history', icon: Clock },
  { title: 'Configuración', url: '/settings', icon: Settings },
];

export function AppSidebar() {
  const location = useLocation();
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const { user, signOut } = useAuth();

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
    }
  };

  return (
    <Sidebar className="hidden md:flex border-r border-sidebar-border bg-sidebar flex-col h-full">
      <SidebarHeader className="p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15">
            <AudioLines className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">LibrisAudio</h1>
            <p className="text-xs text-muted-foreground">PDF → Audiobook</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-3 flex-1">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        className={cn(
                          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                          isActive
                            ? 'bg-primary/10 text-primary'
                            : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                        )}
                      >
                        <item.icon className={cn('h-5 w-5', isActive && 'text-primary')} />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
              {deferredPrompt && (
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <button
                      onClick={handleInstallClick}
                      className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 text-primary hover:bg-primary/10 w-full text-left"
                    >
                      <Download className="h-5 w-5 text-primary" />
                      <span>Instalar App</span>
                    </button>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {user && (
        <SidebarFooter className="p-4 border-t border-sidebar-border mt-auto">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 px-2">
              <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                <UserIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-medium text-foreground truncate">
                  {user.user_metadata?.full_name || user.email?.split('@')[0]}
                </span>
                <span className="text-xs text-muted-foreground truncate">
                  {user.email}
                </span>
              </div>
            </div>
            
            <Button 
              variant="outline" 
              className="w-full justify-start text-muted-foreground hover:text-foreground bg-transparent border-sidebar-border"
              onClick={() => signOut()}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Cerrar Sesión
            </Button>

            <div className="mt-2 w-full flex justify-center">
              <AuthorSignature adaptive={true} />
            </div>
          </div>
        </SidebarFooter>
      )}
    </Sidebar>
  );
}
