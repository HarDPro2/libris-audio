import { useMemo } from 'react';

interface WaveformProps {
  progress: number; // 0-1
  barCount?: number;
  onSeek?: (ratio: number) => void;
}

export function Waveform({ progress, barCount = 60, onSeek }: WaveformProps) {
  const bars = useMemo(() => {
    return Array.from({ length: barCount }, () => 0.15 + Math.random() * 0.85);
  }, [barCount]);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onSeek(ratio);
  };

  return (
    <div
      className="flex items-center gap-[2px] h-10 w-full cursor-pointer"
      onClick={handleClick}
    >
      {bars.map((height, i) => {
        const filled = i / barCount <= progress;
        return (
          <div
            key={i}
            className="flex-1 rounded-full transition-colors duration-150"
            style={{
              height: `${height * 100}%`,
              backgroundColor: filled
                ? 'hsl(var(--primary))'
                : 'hsl(var(--muted))',
              opacity: filled ? 1 : 0.4,
            }}
          />
        );
      })}
    </div>
  );
}
