import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="animate-fade-in max-w-lg">
      <h1 className="text-2xl font-bold text-foreground mb-6">Configuración</h1>
      <div className="space-y-4">
        {[
          { label: 'Velocidad predeterminada', value: '1x' },
          { label: 'Voz de narración', value: 'Natural (ES)' },
          { label: 'Calidad de audio', value: 'Alta (320kbps)' },
          { label: 'Modo oscuro', value: 'Activado' },
        ].map(item => (
          <div key={item.label} className="flex items-center justify-between p-4 rounded-xl bg-card border border-border">
            <span className="text-sm text-foreground">{item.label}</span>
            <span className="text-sm text-muted-foreground">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
