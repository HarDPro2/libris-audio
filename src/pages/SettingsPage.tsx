import { useState, useEffect } from 'react';
import { User, Save } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function SettingsPage() {
  const { user, updateProfile } = useAuth();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  useEffect(() => {
    if (user?.user_metadata?.full_name) {
      setName(user.user_metadata.full_name);
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    setLoading(true);
    setStatus(null);
    const { error } = await updateProfile(name);
    
    if (error) {
      setStatus({ type: 'error', msg: error });
    } else {
      setStatus({ type: 'success', msg: 'Perfil actualizado con éxito.' });
    }
    setLoading(false);
  };

  return (
    <div className="animate-fade-in max-w-lg">
      <h1 className="text-2xl font-bold text-foreground mb-6">Configuración</h1>
      
      <div className="p-6 rounded-2xl bg-card border border-border shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Perfil de Usuario</h2>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground mb-1 block">Nombre de Usuario</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tu nombre visible"
              className="w-full bg-background border border-border rounded-lg px-4 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground mt-1">Este nombre aparecerá en tu perfil y al lado de los libros que subas.</p>
          </div>

          {status && (
            <div className={`p-3 rounded-lg text-sm ${status.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
              {status.msg}
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {loading ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>
        </form>
      </div>

    </div>
  );
}
