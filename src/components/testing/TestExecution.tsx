import { useState } from 'react';
import { ArrowLeft, ArrowRight, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { TestQuestion, TestResponse } from '@/types/testing';
import { cn } from '@/lib/utils';

interface TestExecutionProps {
  testName: string;
  questions: TestQuestion[];
  onComplete: (responses: TestResponse[]) => void;
  onCancel: () => void;
}

export function TestExecution({ testName, questions, onComplete, onCancel }: TestExecutionProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<TestResponse[]>([]);
  const [selectedValue, setSelectedValue] = useState<number | null>(null);

  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentIndex === questions.length - 1;

  const handleSelectOption = (value: number) => {
    setSelectedValue(value);
  };

  const handleNext = () => {
    if (selectedValue === null) return;

    const newResponse: TestResponse = {
      questionId: currentQuestion.id,
      value: selectedValue,
      timestamp: new Date().toISOString(),
    };

    const updatedResponses = [...responses.filter(r => r.questionId !== currentQuestion.id), newResponse];
    setResponses(updatedResponses);

    if (isLastQuestion) {
      onComplete(updatedResponses);
    } else {
      setCurrentIndex((prev) => prev + 1);
      // Check if next question already has a response
      const nextResponse = responses.find(r => r.questionId === questions[currentIndex + 1].id);
      setSelectedValue(nextResponse?.value ?? null);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
      const prevResponse = responses.find(r => r.questionId === questions[currentIndex - 1].id);
      setSelectedValue(prevResponse?.value ?? null);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onCancel}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Salir del test
            </button>
            <span className="text-sm font-medium text-foreground">{testName}</span>
            <span className="text-sm text-muted-foreground">
              {currentIndex + 1} / {questions.length}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </header>

      {/* Question */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-2xl animate-fade-in">
          {currentQuestion.domain && (
            <span className="inline-block px-3 py-1 mb-4 text-xs font-medium text-primary bg-primary/10 rounded-full">
              {currentQuestion.domain}
            </span>
          )}
          
          <h2 className="text-2xl font-semibold text-foreground mb-8">
            {currentQuestion.text}
          </h2>

          <div className="space-y-3">
            {currentQuestion.options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelectOption(option.value)}
                className={cn(
                  'w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left transition-all duration-200',
                  selectedValue === option.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/40 hover:bg-muted/50'
                )}
              >
                <div className={cn(
                  'flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-semibold transition-colors',
                  selectedValue === option.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                )}>
                  {option.label}
                </div>
                <span className={cn(
                  'text-sm transition-colors',
                  selectedValue === option.value ? 'text-foreground' : 'text-muted-foreground'
                )}>
                  {option.description}
                </span>
                {selectedValue === option.value && (
                  <Check className="h-5 w-5 text-primary ml-auto" />
                )}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-border">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Anterior
          </Button>

          {selectedValue === null && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              Selecciona una opción
            </div>
          )}

          <Button
            onClick={handleNext}
            disabled={selectedValue === null}
            className="gap-2"
          >
            {isLastQuestion ? 'Finalizar' : 'Siguiente'}
            {!isLastQuestion && <ArrowRight className="h-4 w-4" />}
          </Button>
        </div>
      </footer>
    </div>
  );
}
