import { ScientificFeed } from '@/types/clinical';
import { ExternalLink, Clock, Tag } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScientificFeedItemProps {
  feed: ScientificFeed;
  onClick?: (feed: ScientificFeed) => void;
}

const categoryColors: Record<string, string> = {
  Research: 'bg-primary/10 text-primary',
  Guidelines: 'bg-success/10 text-success',
  Technology: 'bg-warning/10 text-warning',
  Review: 'bg-secondary text-secondary-foreground',
};

export function ScientificFeedItem({ feed, onClick }: ScientificFeedItemProps) {
  return (
    <button
      onClick={() => onClick?.(feed)}
      className="feed-item w-full text-left"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            {feed.isNew && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-primary text-primary-foreground">
                Nuevo
              </span>
            )}
            <span className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              categoryColors[feed.category] || categoryColors.Review
            )}>
              {feed.category}
            </span>
          </div>
          <h3 className="font-medium text-foreground line-clamp-2 leading-snug">
            {feed.title}
          </h3>
          <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
            {feed.summary}
          </p>
        </div>
        <ExternalLink className="h-4 w-4 text-muted-foreground shrink-0" />
      </div>
      
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <Tag className="h-3 w-3" />
          <span>{feed.source}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          <span>{feed.publishedAt}</span>
        </div>
      </div>
    </button>
  );
}
