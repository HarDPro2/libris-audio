import { NavLink } from 'react-router-dom';
import { Home, BookOpen, Upload, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';

const navItems = [
  { title: 'Inicio', url: '/', icon: Home, exact: true },
  { title: 'Bibiloteca', url: '/library', icon: BookOpen },
  { title: 'Subir', url: '/upload', icon: Upload },
  { title: 'Ajustes', url: '/settings', icon: Settings },
];

export function MobileBottomNav() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 h-[60px] bg-background/80 backdrop-blur-xl border-t border-border z-[100] flex items-center justify-around px-2 pb-safe shadow-t-lg">
      {navItems.map((item) => (
        <NavLink
          key={item.title}
          to={item.url}
          end={item.exact}
          className={({ isActive }) => cn(
            "flex flex-col items-center justify-center w-16 h-full gap-1 transition-colors duration-200",
            isActive ? "text-primary" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {({ isActive }) => (
            <>
              <item.icon className={cn("h-5 w-5", isActive && "stroke-[2.5px]")} />
              <span className={cn("text-[10px] font-medium leading-none", isActive && "font-bold")}>
                {item.title}
              </span>
            </>
          )}
        </NavLink>
      ))}
    </div>
  );
}
