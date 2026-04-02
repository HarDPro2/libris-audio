import { Play, Pause, SkipBack, SkipForward, Volume2 } from 'lucide-react';
import { usePlayer } from '@/context/PlayerContext';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Waveform } from './Waveform';
import { SpeedMenu } from './SpeedMenu';

function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

const VOICES = [
  { id: 'es-MX-JorgeNeural', name: '🇲🇽 Jorge (México) - Hombre' },
  { id: 'es-MX-DaliaNeural', name: '🇲🇽 Dalia (México) - Mujer' },
  { id: 'es-ES-AlvaroNeural', name: '🇪🇸 Álvaro (España) - Hombre' },
  { id: 'es-ES-ElviraNeural', name: '🇪🇸 Elvira (España) - Mujer' },
  { id: 'es-US-AlonsoNeural', name: '🇺🇸 Alonso (EEUU) - Hombre' },
  { id: 'es-US-PalomaNeural', name: '🇺🇸 Paloma (EEUU) - Mujer' },
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

export function AudioPlayer() {
  const {
    currentBook,
    isPlaying,
    togglePlay,
    seekForward,
    seekBackward,
    volume,
    setVolume,
    elapsed,
    audioRef,
    seekToPart,
    voice,
    setVoice,
  } = usePlayer();

  if (!currentBook) return null;

  const progress = currentBook.totalTime > 0 ? elapsed / currentBook.totalTime : 0;

  // Allow scrubbing via the waveform progress bar (click on Waveform = seek)
  const handleSeek = (ratio: number) => {
    const audio = audioRef.current;
    if (audio && audio.duration && !isNaN(audio.duration)) {
      audio.currentTime = ratio * audio.duration;
    }
  };

  return (
    <div className="fixed bottom-[60px] md:bottom-0 left-0 right-0 z-50 border-t border-border bg-[hsl(var(--player-background))]/95 backdrop-blur-xl shadow-[0_-4px_10px_rgba(0,0,0,0.1)]">
      <div className="flex flex-col md:flex-row items-center gap-2 md:gap-4 px-3 md:px-6 py-2 md:py-0 md:h-20">
        
        {/* Book info & Mobile Menus */}
        <div className="flex items-center justify-between w-full md:w-48 md:shrink-0 gap-2">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-[6px] md:rounded-lg overflow-hidden shrink-0">
              <img src={currentBook.coverUrl} alt={currentBook.title} className="w-full h-full object-cover" />
            </div>
            <div className="min-w-0 flex flex-col justify-center">
              <p className="text-sm font-medium text-foreground truncate">{currentBook.title}</p>
              <p className="text-xs text-muted-foreground truncate leading-tight">{currentBook.author}</p>
              {currentBook.partsCount && currentBook.partsCount > 1 && (
                <div className="mt-0.5">
                  <Select
                    value={currentBook.currentPartIndex?.toString() || "0"}
                    onValueChange={(val) => seekToPart(parseInt(val, 10))}
                  >
                    <SelectTrigger className="h-4 md:h-5 w-fit border-none shadow-none text-[10px] text-muted-foreground font-medium p-0 pr-1 hover:text-foreground transition-colors focus:ring-0 focus:ring-offset-0 bg-transparent gap-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {Array.from({ length: currentBook.partsCount }).map((_, i) => (
                        <SelectItem key={i} value={i.toString()} className="text-xs">
                          Parte {i + 1} de {currentBook.partsCount}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </div>
          
          {/* Mobile Right Edge: Play controls or menus */}
          <div className="flex md:hidden items-center gap-1 shrink-0">
            <Select value={voice} onValueChange={setVoice}>
              <SelectTrigger className="h-8 focus:ring-0 shadow-none text-[10px] bg-transparent border-muted-foreground/30 px-2 w-20 truncate">
                <SelectValue placeholder="Voz" />
              </SelectTrigger>
              <SelectContent align="end" className="max-h-[250px] w-56">
                {VOICES.map(v => (
                  <SelectItem key={v.id} value={v.id} className="text-xs">{v.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <SpeedMenu />
          </div>
        </div>

        {/* Center controls + waveform */}
        <div className="flex-1 flex flex-col items-center gap-1 w-full max-w-2xl mx-auto">
          {/* Main Play Controls */}
          <div className="flex items-center gap-3 md:mt-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={seekBackward}
            >
              <SkipBack className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              className="h-9 w-9 md:h-10 md:w-10 rounded-full"
              onClick={togglePlay}
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={seekForward}
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Waveform Row */}
          <div className="w-full flex items-center justify-between gap-2 px-1">
            <span className="text-[10px] text-muted-foreground w-8 md:w-12 text-right shrink-0">
              {formatTime(elapsed)}
            </span>
            <div className="flex-1 min-w-0">
               <Waveform progress={progress} onSeek={handleSeek} />
            </div>
            <span className="text-[10px] text-muted-foreground w-8 md:w-12 shrink-0">
              {formatTime(currentBook.totalTime)}
            </span>
          </div>
        </div>

        {/* Desktop Right controls */}
        <div className="hidden md:flex items-center gap-3 w-56 xl:w-80 justify-end shrink-0">
          <Select value={voice} onValueChange={setVoice}>
            <SelectTrigger className="h-8 text-xs bg-transparent border-muted-foreground/30 hover:bg-muted w-36 overflow-hidden focus:ring-0">
              <SelectValue placeholder="Voz" />
            </SelectTrigger>
            <SelectContent align="end" className="max-h-[300px]">
              {VOICES.map(v => (
                <SelectItem key={v.id} value={v.id} className="text-xs">{v.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <SpeedMenu />
          <Volume2 className="hidden lg:block h-4 w-4 text-muted-foreground shrink-0" />
          <Slider
            value={[volume * 100]}
            onValueChange={([v]) => setVolume(v / 100)}
            max={100}
            step={1}
            className="hidden lg:flex w-20"
          />
        </div>
      </div>
    </div>
  );
}
