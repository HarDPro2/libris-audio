import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage, AIInsight } from '@/types/clinical';
import { Send, BookOpen, Sparkles, AlertCircle, Lightbulb, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIInsightsPanelProps {
  isSearching?: boolean;
  onSendMessage?: (message: string) => void;
  onSearch?: (query: string) => void;
}

const mockInsights: AIInsight[] = [
  {
    id: '1',
    type: 'suggestion',
    content: 'Basado en los síntomas descritos, considere evaluar comorbilidad con trastorno de pánico.',
    confidence: 85,
    timestamp: '10:30',
  },
  {
    id: '2',
    type: 'reference',
    content: 'Ver: "CBT protocols for GAD" - Beck Institute Guidelines 2025',
    source: 'APA Clinical Guidelines',
    timestamp: '10:28',
  },
];

const mockMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: '¿Cuáles son los criterios DSM-5 para TAG?',
    timestamp: '10:25',
  },
  {
    id: '2',
    role: 'assistant',
    content: 'Los criterios DSM-5 para el Trastorno de Ansiedad Generalizada (F41.1) incluyen:\n\n1. Ansiedad y preocupación excesivas durante más de 6 meses\n2. Dificultad para controlar la preocupación\n3. Al menos 3 de 6 síntomas: inquietud, fatiga, dificultad de concentración, irritabilidad, tensión muscular, problemas de sueño\n4. Deterioro significativo en funcionamiento social/laboral',
    timestamp: '10:25',
    references: ['DSM-5 Section II', 'APA Guidelines 2024'],
  },
];

const insightIcons = {
  suggestion: Lightbulb,
  reference: BookOpen,
  alert: AlertCircle,
};

const insightColors = {
  suggestion: 'bg-primary/10 text-primary',
  reference: 'bg-success/10 text-success',
  alert: 'bg-warning/10 text-warning',
};

export function AIInsightsPanel({ isSearching, onSendMessage, onSearch }: AIInsightsPanelProps) {
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage?.(message);
      setMessage('');
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      onSearch?.(searchQuery);
    }
  };

  return (
    <div className="insight-panel h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">IA Insights</h3>
        </div>
        <p className="text-sm text-muted-foreground">Asistente clínico inteligente</p>
      </div>
      
      {/* Bibliography Search */}
      <div className="p-4 border-b border-border bg-secondary/30">
        <div className="flex items-center gap-2 mb-3">
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">Búsqueda en Bibliografía</span>
          {isSearching && (
            <div className="flex items-center gap-1.5 ml-auto">
              <Loader2 className="h-3 w-3 animate-spin text-primary" />
              <span className="text-xs text-primary">Buscando...</span>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar en literatura científica..."
            className="text-sm"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button size="sm" onClick={handleSearch} disabled={isSearching}>
            Buscar
          </Button>
        </div>
      </div>
      
      {/* Insights */}
      <div className="p-4 border-b border-border">
        <h4 className="text-sm font-medium text-foreground mb-3">Sugerencias Activas</h4>
        <div className="space-y-2">
          {mockInsights.map((insight) => {
            const Icon = insightIcons[insight.type];
            return (
              <div
                key={insight.id}
                className="p-3 rounded-lg bg-secondary/50 border border-border"
              >
                <div className="flex items-start gap-2">
                  <div className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full shrink-0',
                    insightColors[insight.type]
                  )}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground">{insight.content}</p>
                    {insight.source && (
                      <p className="text-xs text-muted-foreground mt-1">{insight.source}</p>
                    )}
                    {insight.confidence && (
                      <div className="flex items-center gap-2 mt-2">
                        <div className="h-1.5 flex-1 rounded-full bg-border">
                          <div 
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${insight.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">{insight.confidence}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Chat */}
      <div className="flex-1 flex flex-col min-h-0">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {mockMessages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-3',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground'
                )}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  {msg.references && msg.references.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/30">
                      <p className="text-xs opacity-70">Referencias: {msg.references.join(', ')}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        
        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Pregunte al asistente..."
              className="flex-1"
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <Button size="icon" onClick={handleSend}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
