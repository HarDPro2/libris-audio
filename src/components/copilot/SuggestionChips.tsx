import { Search, Brain, FileSearch, Lightbulb } from 'lucide-react';
import { QuickSuggestion } from '@/types/testing';
import { cn } from '@/lib/utils';

interface SuggestionChipsProps {
  suggestions: QuickSuggestion[];
  onSelect: (prompt: string) => void;
  className?: string;
}

export function SuggestionChips({ suggestions, onSelect, className }: SuggestionChipsProps) {
  const getIcon = (index: number) => {
    const icons = [Search, Brain, FileSearch, Lightbulb];
    const Icon = icons[index % icons.length];
    return <Icon className="h-3.5 w-3.5" />;
  };

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {suggestions.map((suggestion, index) => (
        <button
          key={suggestion.id}
          onClick={() => onSelect(suggestion.prompt)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted/50 hover:bg-muted hover:text-foreground rounded-full transition-all duration-200 border border-transparent hover:border-border"
        >
          {getIcon(index)}
          <span>{suggestion.label}</span>
        </button>
      ))}
    </div>
  );
}
