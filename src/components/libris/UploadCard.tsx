import { Plus, Loader2, AlertCircle, Volume2 } from 'lucide-react';
import { useRef, useState } from 'react';
import { usePlayer } from '@/context/PlayerContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { Button } from '@/components/ui/button';

const VOICES = [
  // Norteamérica y España
  { id: 'es-MX-JorgeNeural', name: '🇲🇽 Jorge (México) - Hombre' },
  { id: 'es-MX-DaliaNeural', name: '🇲🇽 Dalia (México) - Mujer' },
  { id: 'es-ES-AlvaroNeural', name: '🇪🇸 Álvaro (España) - Hombre' },
  { id: 'es-ES-ElviraNeural', name: '🇪🇸 Elvira (España) - Mujer' },
  { id: 'es-US-AlonsoNeural', name: '🇺🇸 Alonso (EEUU/Neutral) - Hombre' },
  { id: 'es-US-PalomaNeural', name: '🇺🇸 Paloma (EEUU/Neutral) - Mujer' },
  
  // Sudamérica
  { id: 'es-AR-TomasNeural', name: '🇦🇷 Tomás (Argentina) - Hombre' },
  { id: 'es-AR-ElenaNeural', name: '🇦🇷 Elena (Argentina) - Mujer' },
  { id: 'es-BO-MarceloNeural', name: '🇧🇴 Marcelo (Bolivia) - Hombre' },
  { id: 'es-BO-SofiaNeural', name: '🇧🇴 Sofía (Bolivia) - Mujer' },
  { id: 'es-CL-LorenzoNeural', name: '🇨🇱 Lorenzo (Chile) - Hombre' },
  { id: 'es-CL-CatalinaNeural', name: '🇨🇱 Catalina (Chile) - Mujer' },
  { id: 'es-CO-GonzaloNeural', name: '🇨🇴 Gonzalo (Colombia) - Hombre' },
  { id: 'es-CO-SalomeNeural', name: '🇨🇴 Salomé (Colombia) - Mujer' },
  { id: 'es-EC-LuisNeural', name: '🇪🇨 Luis (Ecuador) - Hombre' },
  { id: 'es-EC-AndreaNeural', name: '🇪🇨 Andrea (Ecuador) - Mujer' },
  { id: 'es-PE-AlexNeural', name: '🇵🇪 Alex (Perú) - Hombre' },
  { id: 'es-PE-CamilaNeural', name: '🇵🇪 Camila (Perú) - Mujer' },
  { id: 'es-PY-MarioNeural', name: '🇵🇾 Mario (Paraguay) - Hombre' },
  { id: 'es-PY-TaniaNeural', name: '🇵🇾 Tania (Paraguay) - Mujer' },
  { id: 'es-UY-MateoNeural', name: '🇺🇾 Mateo (Uruguay) - Hombre' },
  { id: 'es-UY-ValentinaNeural', name: '🇺🇾 Valentina (Uruguay) - Mujer' },
  { id: 'es-VE-SebastianNeural', name: '🇻🇪 Sebastián (Venezuela) - Hombre' },
  { id: 'es-VE-PaolaNeural', name: '🇻🇪 Paola (Venezuela) - Mujer' },

  // Centroamérica y Caribe
  { id: 'es-CR-JuanNeural', name: '🇨🇷 Juan (Costa Rica) - Hombre' },
  { id: 'es-CR-MariaNeural', name: '🇨🇷 María (Costa Rica) - Mujer' },
  { id: 'es-CU-ManuelNeural', name: '🇨🇺 Manuel (Cuba) - Hombre' },
  { id: 'es-CU-BelkysNeural', name: '🇨🇺 Belkys (Cuba) - Mujer' },
  { id: 'es-DO-EmilioNeural', name: '🇩🇴 Emilio (R. Dominicana) - Hombre' },
  { id: 'es-DO-RamonaNeural', name: '🇩🇴 Ramona (R. Dominicana) - Mujer' },
  { id: 'es-GT-AndresNeural', name: '🇬🇹 Andrés (Guatemala) - Hombre' },
  { id: 'es-GT-MartaNeural', name: '🇬🇹 Marta (Guatemala) - Mujer' },
  { id: 'es-HN-CarlosNeural', name: '🇭🇳 Carlos (Honduras) - Hombre' },
  { id: 'es-HN-KarlaNeural', name: '🇭🇳 Karla (Honduras) - Mujer' },
  { id: 'es-NI-FedericoNeural', name: '🇳🇮 Federico (Nicaragua) - Hombre' },
  { id: 'es-NI-YolandaNeural', name: '🇳🇮 Yolanda (Nicaragua) - Mujer' },
  { id: 'es-PA-RobertoNeural', name: '🇵🇦 Roberto (Panamá) - Hombre' },
  { id: 'es-PA-MargaritaNeural', name: '🇵🇦 Margarita (Panamá) - Mujer' },
  { id: 'es-PR-VictorNeural', name: '🇵🇷 Víctor (Puerto Rico) - Hombre' },
  { id: 'es-PR-KarinaNeural', name: '🇵🇷 Karina (Puerto Rico) - Mujer' },
  { id: 'es-SV-RodrigoNeural', name: '🇸🇻 Rodrigo (El Salvador) - Hombre' },
  { id: 'es-SV-LorenaNeural', name: '🇸🇻 Lorena (El Salvador) - Mujer' },
];

export function UploadCard() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState(VOICES[0].id);
  const [isPlayingSample, setIsPlayingSample] = useState(false);
  const { addBook } = usePlayer();

  const playSample = () => {
    if (isPlayingSample) return;
    setIsPlayingSample(true);
    const audio = new Audio(`http://localhost:8000/api/tts-sample?voice=${selectedVoice}`);
    audio.onended = () => setIsPlayingSample(false);
    audio.onerror = () => setIsPlayingSample(false);
    audio.play().catch(() => setIsPlayingSample(false));
  };

  const handleClick = () => {
    if (!isProcessing) {
      setError(null);
      fileRef.current?.click();
    }
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('voice', selectedVoice);

      const response = await fetch('http://localhost:8000/api/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail ?? `Error ${response.status}`);
      }

      const data: { title: string; bookId: string; partsCount: number; voice: string; coverUrl?: string } = await response.json();
      addBook(data.title, undefined, data.bookId, data.partsCount, data.voice, data.coverUrl);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido';
      setError(message);
    } finally {
      setIsProcessing(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={fileRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFile}
      />
      
      <div className="upload-card aspect-[3/4]" onClick={handleClick}>
        {isProcessing ? (
          <>
            <Loader2 className="h-10 w-10 text-primary animate-spin" />
            <span className="text-sm text-muted-foreground font-medium text-center px-2">
              Procesando PDF…<br />
              <span className="text-xs opacity-70">Generando audio con IA</span>
            </span>
          </>
        ) : error ? (
          <>
            <AlertCircle className="h-10 w-10 text-destructive" />
            <span className="text-xs text-destructive font-medium text-center px-3 leading-tight">
              {error}
            </span>
            <span className="text-xs text-muted-foreground mt-1">Toca para reintentar</span>
          </>
        ) : (
          <>
            <div className="h-14 w-14 rounded-full border-2 border-dashed border-muted-foreground/40 flex items-center justify-center">
              <Plus className="h-7 w-7 text-muted-foreground" />
            </div>
            <span className="text-sm text-muted-foreground font-medium">Subir Nuevo PDF</span>
          </>
        )}
      </div>

      <div className="flex gap-2 w-full">
        <Select value={selectedVoice} onValueChange={setSelectedVoice} disabled={isProcessing || isPlayingSample}>
          <SelectTrigger className="flex-1 bg-[hsl(var(--card))] border-[hsl(var(--border))]">
            <SelectValue placeholder="Voz" />
          </SelectTrigger>
          <SelectContent>
            {VOICES.map((v) => (
              <SelectItem key={v.id} value={v.id}>
                {v.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button 
          variant="outline" 
          size="icon" 
          onClick={playSample} 
          disabled={isPlayingSample || isProcessing}
          className="shrink-0 bg-[hsl(var(--card))] border-[hsl(var(--border))]"
          title="Escuchar muestra de voz"
        >
          {isPlayingSample ? <Loader2 className="h-4 w-4 animate-spin text-primary" /> : <Volume2 className="h-4 w-4 text-primary" />}
        </Button>
      </div>
    </div>
  );
}
