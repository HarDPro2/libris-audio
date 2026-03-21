import { useState } from 'react';
import { FlaskConical, Search, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TestCard } from '@/components/testing/TestCard';
import { TestExecution } from '@/components/testing/TestExecution';
import { TestResultsView } from '@/components/testing/TestResultsView';
import { PsychTest, TestResponse } from '@/types/testing';
import { mockPsychTests, mockBDIQuestions, mockTestResult } from '@/data/testingData';
import { cn } from '@/lib/utils';

type ViewState = 'selection' | 'execution' | 'results';

const categories = [
  { id: 'all', label: 'Todos' },
  { id: 'mood', label: 'Estado de Ánimo' },
  { id: 'anxiety', label: 'Ansiedad' },
  { id: 'cognitive', label: 'Cognitivo' },
  { id: 'personality', label: 'Personalidad' },
  { id: 'trauma', label: 'Trauma' },
];

export default function TestingLab() {
  const [view, setView] = useState<ViewState>('selection');
  const [selectedTest, setSelectedTest] = useState<PsychTest | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');

  const filteredTests = mockPsychTests.filter((test) => {
    const matchesSearch = test.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          test.shortName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === 'all' || test.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const handleSelectTest = (test: PsychTest) => {
    setSelectedTest(test);
  };

  const handleStartTest = () => {
    if (selectedTest) {
      setView('execution');
    }
  };

  const handleCompleteTest = (responses: TestResponse[]) => {
    console.log('Test completed with responses:', responses);
    // Ready for API connection - process responses
    setView('results');
  };

  const handleCancelTest = () => {
    setView('selection');
    setSelectedTest(null);
  };

  const handleRetakeTest = () => {
    setView('execution');
  };

  const handleBackToSelection = () => {
    setView('selection');
    setSelectedTest(null);
  };

  // Render execution mode
  if (view === 'execution' && selectedTest) {
    return (
      <TestExecution
        testName={selectedTest.name}
        questions={mockBDIQuestions} // Using BDI questions as demo
        onComplete={handleCompleteTest}
        onCancel={handleCancelTest}
      />
    );
  }

  // Render results view
  if (view === 'results' && selectedTest) {
    return (
      <TestResultsView
        result={mockTestResult}
        testName={selectedTest.name}
        onBack={handleBackToSelection}
        onRetake={handleRetakeTest}
      />
    );
  }

  // Render selection view
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <FlaskConical className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Laboratorio de Pruebas</h1>
            <p className="text-muted-foreground">Evaluaciones psicométricas estandarizadas</p>
          </div>
        </div>
        
        {selectedTest && (
          <Button onClick={handleStartTest} size="lg" className="gap-2">
            Iniciar {selectedTest.shortName}
          </Button>
        )}
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar pruebas..."
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 sm:pb-0">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-all',
                activeCategory === category.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              )}
            >
              {category.label}
            </button>
          ))}
        </div>
      </div>

      {/* Test Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredTests.map((test) => (
          <TestCard
            key={test.id}
            test={test}
            isSelected={selectedTest?.id === test.id}
            onClick={() => handleSelectTest(test)}
          />
        ))}
      </div>

      {filteredTests.length === 0 && (
        <div className="text-center py-12">
          <FlaskConical className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No se encontraron pruebas</h3>
          <p className="text-muted-foreground">Intenta ajustar los filtros de búsqueda</p>
        </div>
      )}
    </div>
  );
}
