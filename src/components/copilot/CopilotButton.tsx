import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CopilotButtonProps {
  onClick: () => void;
  isOpen: boolean;
}

export function CopilotButton({ onClick, isOpen }: CopilotButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'copilot-fab',
        isOpen && 'scale-0 opacity-0 pointer-events-none'
      )}
      aria-label="Abrir Co-Piloto Clínico"
    >
      <Sparkles className="h-6 w-6" />
    </button>
  );
}
