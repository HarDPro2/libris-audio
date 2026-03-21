import { CopilotMessage } from '@/types/testing';
import { SourceCard } from './SourceCard';
import { cn } from '@/lib/utils';
import { Brain, Beaker, User } from 'lucide-react';

interface ChatMessageProps {
  message: CopilotMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  const getMessageStyle = () => {
    if (isUser) return 'message-user';
    if (message.type === 'evidence') return 'message-evidence';
    return 'message-reasoning';
  };

  const getIcon = () => {
    if (isUser) return <User className="h-4 w-4" />;
    if (message.type === 'evidence') return <Beaker className="h-4 w-4" />;
    return <Brain className="h-4 w-4" />;
  };

  const getLabel = () => {
    if (isUser) return null;
    if (message.type === 'evidence') return 'Evidencia';
    return 'Razonamiento';
  };

  return (
    <div className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          message.type === 'evidence' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
        )}>
          {getIcon()}
        </div>
      )}
      
      <div className={cn('max-w-[85%] space-y-2', isUser && 'items-end')}>
        {getLabel() && (
          <span className={cn(
            'text-xs font-medium',
            message.type === 'evidence' ? 'text-primary' : 'text-muted-foreground'
          )}>
            {getLabel()}
          </span>
        )}
        
        <div className={getMessageStyle()}>
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="space-y-2 mt-3">
            <span className="text-xs font-medium text-muted-foreground">Fuentes citadas:</span>
            {message.sources.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        )}

        <span className="text-xs text-muted-foreground">
          {new Date(message.timestamp).toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </span>
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
          {getIcon()}
        </div>
      )}
    </div>
  );
}
