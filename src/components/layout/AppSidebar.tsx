import { NavLink, useLocation } from 'react-router-dom';
import { 
  Home, 
  Users, 
  BookOpen, 
  Settings, 
  Stethoscope,
  Activity,
  FlaskConical
} from 'lucide-react';
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

const navigationItems = [
  { title: 'Inicio', url: '/', icon: Home },
  { title: 'Pacientes', url: '/patients', icon: Users },
  { title: 'Diagnóstico', url: '/diagnosis', icon: Stethoscope },
  { title: 'Laboratorio', url: '/testing-lab', icon: FlaskConical },
  { title: 'Biblioteca', url: '/library', icon: BookOpen },
  { title: 'Configuración', url: '/settings', icon: Settings },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar className="border-r border-border bg-sidebar">
      <SidebarHeader className="p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
            <Activity className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">ClínicAI</h1>
            <p className="text-xs text-muted-foreground">Ingeniería Diagnóstica</p>
          </div>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="px-3">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        className={cn(
                          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                          isActive
                            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                            : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
                        )}
                      >
                        <item.icon className={cn(
                          'h-5 w-5',
                          isActive ? 'text-primary' : ''
                        )} />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
            <span className="text-sm font-medium text-primary">DR</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">Dr. Ramírez</p>
            <p className="text-xs text-muted-foreground truncate">Psicología Clínica</p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
