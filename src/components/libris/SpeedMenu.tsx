import { useState } from 'react';
import { usePlayer } from '@/context/PlayerContext';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';

const speeds = [0.75, 1, 1.25, 1.5, 2];

export function SpeedMenu() {
  const { speed, setSpeed } = usePlayer();
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-8 px-3 text-xs font-semibold border-primary/30 text-primary hover:bg-primary/10"
        >
          {speed}x
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-32 p-1 bg-card border-border" align="center" side="top">
        {speeds.map(s => (
          <button
            key={s}
            onClick={() => { setSpeed(s); setOpen(false); }}
            className={`w-full text-left px-3 py-1.5 text-sm rounded-md transition-colors ${
              s === speed ? 'bg-primary/15 text-primary font-medium' : 'text-foreground hover:bg-secondary'
            }`}
          >
            {s}x
          </button>
        ))}
      </PopoverContent>
    </Popover>
  );
}
