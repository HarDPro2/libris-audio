import { useState, useEffect } from 'react';
import { Search, User } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Menu } from 'lucide-react';

export function TopBar() {
  const [userName, setUserName] = useState("Usuario");

  useEffect(() => {
    const saved = localStorage.getItem('libris_username');
    if (saved) setUserName(saved);
  }, []);

  const handleChangeName = () => {
    const newName = prompt("¿Cómo te llamas?", userName);
    if (newName && newName.trim() !== "") {
      const finalName = newName.trim();
      setUserName(finalName);
      localStorage.setItem('libris_username', finalName);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 backdrop-blur-md px-6">
      <SidebarTrigger className="-ml-2">
        <Menu className="h-5 w-5" />
      </SidebarTrigger>

      <div className="flex-1">
        <h2 className="text-sm text-muted-foreground">
          Bienvenido de nuevo,{' '}
          <span 
            className="text-foreground font-medium cursor-pointer hover:underline decoration-primary underline-offset-4"
            title="Haz clic para cambiar tu nombre"
            onClick={handleChangeName}
          >
            {userName}
          </span>
        </h2>
      </div>

      <div className="relative w-64">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar libros..."
          className="pl-9 bg-secondary border-border text-sm h-9"
        />
      </div>

      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/15">
        <User className="h-4 w-4 text-primary" />
      </div>
    </header>
  );
}
