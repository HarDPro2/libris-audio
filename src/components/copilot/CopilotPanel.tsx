import { useState } from 'react';
import { X, Send, Wifi, Database, Loader2 } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage } from './ChatMessage';
import { SuggestionChips } from './SuggestionChips';
import { CopilotMessage, QuickSuggestion } from '@/types/testing';
import { mockCopilotMessages, quickSuggestions } from '@/data/testingData';
import { cn } from '@/lib/utils';

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  patientName?: string;
  className?: string;
}

export function CopilotPanel({ isOpen, onClose, patientName = 'María García López' }: CopilotPanelProps) {
  const [messages, setMessages] = useState<CopilotMessage[]>(mockCopilotMessages);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = (content: string) => {
    if (!content.trim()) return;

    const newMessage: CopilotMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      type: 'question',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response - ready for API connection
    setTimeout(() => {
      const aiResponse: CopilotMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        type: 'reasoning',
        content: 'Procesando tu consulta y analizando la base de conocimiento científico...',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const handleSuggestionSelect = (prompt: string) => {
    handleSendMessage(prompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-lg p-0 glass-panel border-l border-border/50"
      >
        {/* Header */}
        <SheetHeader className="p-4 border-b border-border/50 bg-background/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <Database className="h-5 w-5 text-primary" />
              </div>
              <div>
                <SheetTitle className="text-base font-semibold text-foreground">
                  Co-Piloto Clínico
                </SheetTitle>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Wifi className="h-3 w-3 text-success" />
                  <span className="text-xs text-muted-foreground">
                    Conectado a: <span className="text-foreground font-medium">{patientName}</span>
                  </span>
                </div>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-2 mt-3 px-1">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-success/10 text-success text-xs font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
              Biblioteca Científica Global
            </div>
          </div>
        </SheetHeader>

        {/* Messages */}
        <ScrollArea className="flex-1 h-[calc(100vh-280px)]">
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Analizando...</span>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border/50 bg-background/95 backdrop-blur-sm">
          <SuggestionChips 
            suggestions={quickSuggestions} 
            onSelect={handleSuggestionSelect}
            className="mb-3"
          />
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pregunta al asistente clínico..."
              className="flex-1 bg-muted/50 border-border/50 focus:border-primary/50"
              disabled={isLoading}
            />
            <Button 
              onClick={() => handleSendMessage(inputValue)}
              disabled={!inputValue.trim() || isLoading}
              size="icon"
              className="shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
