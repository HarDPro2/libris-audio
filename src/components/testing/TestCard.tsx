import { Clock, CheckCircle2, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { PsychTest } from '@/types/testing';
import { cn } from '@/lib/utils';

interface TestCardProps {
  test: PsychTest;
  isSelected?: boolean;
  onClick: () => void;
}

export function TestCard({ test, isSelected, onClick }: TestCardProps) {
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      cognitive: 'bg-blue-500/10 text-blue-600 border-blue-200',
      personality: 'bg-purple-500/10 text-purple-600 border-purple-200',
      mood: 'bg-amber-500/10 text-amber-600 border-amber-200',
      anxiety: 'bg-rose-500/10 text-rose-600 border-rose-200',
      trauma: 'bg-slate-500/10 text-slate-600 border-slate-200',
    };
    return colors[category] || 'bg-muted text-muted-foreground';
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      cognitive: 'Cognitivo',
      personality: 'Personalidad',
      mood: 'Estado de Ánimo',
      anxiety: 'Ansiedad',
      trauma: 'Trauma',
    };
    return labels[category] || category;
  };

  const getValidityStars = (validity: string) => {
    const count = validity === 'high' ? 3 : validity === 'moderate' ? 2 : 1;
    return Array.from({ length: 3 }, (_, i) => (
      <Star
        key={i}
        className={cn(
          'h-3.5 w-3.5',
          i < count ? 'fill-warning text-warning' : 'text-muted'
        )}
      />
    ));
  };

  return (
    <button
      onClick={onClick}
      className={cn('test-card text-left w-full', isSelected && 'active')}
    >
      <div className="flex items-start justify-between mb-3">
        <Badge 
          variant="outline" 
          className={cn('text-xs font-medium', getCategoryColor(test.category))}
        >
          {getCategoryLabel(test.category)}
        </Badge>
        <span className="text-2xl font-bold text-primary">{test.shortName}</span>
      </div>

      <h3 className="font-semibold text-foreground mb-2 line-clamp-2">
        {test.name}
      </h3>
      
      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {test.description}
      </p>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{test.estimatedTime} min</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>{test.questionCount} ítems</span>
          </div>
        </div>
        <div className="flex items-center gap-1" title={`Validez: ${test.validity}`}>
          {getValidityStars(test.validity)}
        </div>
      </div>
    </button>
  );
}
