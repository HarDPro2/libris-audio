import { ExternalLink, BookOpen, FileText, ScrollText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { SourceReference } from '@/types/testing';
import { cn } from '@/lib/utils';

interface SourceCardProps {
  source: SourceReference;
  className?: string;
}

export function SourceCard({ source, className }: SourceCardProps) {
  const getIcon = () => {
    switch (source.type) {
      case 'journal':
        return <FileText className="h-4 w-4 text-primary" />;
      case 'textbook':
        return <BookOpen className="h-4 w-4 text-primary" />;
      case 'guideline':
        return <ScrollText className="h-4 w-4 text-primary" />;
    }
  };

  const getQuartileBadge = () => {
    if (!source.quartile) return null;
    
    const colors = {
      'Q1': 'bg-success/10 text-success border-success/20',
      'Q2': 'bg-primary/10 text-primary border-primary/20',
      'Q3': 'bg-warning/10 text-warning border-warning/20',
      'Q4': 'bg-muted text-muted-foreground border-border',
    };

    return (
      <Badge variant="outline" className={cn('text-xs font-medium', colors[source.quartile])}>
        {source.quartile} Journal
      </Badge>
    );
  };

  return (
    <div className={cn('source-card group', className)}>
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-foreground line-clamp-2 leading-snug">
            {source.title}
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            {source.authors.slice(0, 2).join(', ')}
            {source.authors.length > 2 && ' et al.'}
            {' · '}{source.year}
          </p>
          <div className="flex items-center gap-2 mt-2">
            {getQuartileBadge()}
            {source.journal && (
              <span className="text-xs text-muted-foreground truncate">
                {source.journal}
              </span>
            )}
            {source.impactFactor && (
              <span className="text-xs text-muted-foreground">
                IF: {source.impactFactor}
              </span>
            )}
          </div>
        </div>
        <button className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted rounded">
          <ExternalLink className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>
    </div>
  );
}
