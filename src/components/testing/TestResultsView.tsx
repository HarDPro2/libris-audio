import { ArrowLeft, Download, Share2, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TestResult } from '@/types/testing';
import { ResultsRadarChart } from './ResultsRadarChart';
import { DifferentialDiagnosisCard } from './DifferentialDiagnosisCard';
import { EvidencePanel } from './EvidencePanel';
import { cn } from '@/lib/utils';

interface TestResultsViewProps {
  result: TestResult;
  testName: string;
  onBack: () => void;
  onRetake: () => void;
}

export function TestResultsView({ result, testName, onBack, onRetake }: TestResultsViewProps) {
  const getSeverityBadge = (severity?: string) => {
    const styles: Record<string, string> = {
      minimal: 'bg-success/10 text-success border-success/20',
      mild: 'bg-blue-500/10 text-blue-600 border-blue-200',
      moderate: 'bg-warning/10 text-warning border-warning/20',
      severe: 'bg-destructive/10 text-destructive border-destructive/20',
    };
    const labels: Record<string, string> = {
      minimal: 'Mínimo',
      mild: 'Leve',
      moderate: 'Moderado',
      severe: 'Grave',
    };
    
    if (!severity) return null;
    
    return (
      <Badge variant="outline" className={cn('text-sm font-semibold px-3 py-1', styles[severity])}>
        {labels[severity]}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-background animate-fade-in">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver al laboratorio
            </button>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <Download className="h-4 w-4" />
                Exportar
              </Button>
              <Button variant="outline" size="sm" className="gap-2">
                <Share2 className="h-4 w-4" />
                Compartir
              </Button>
              <Button variant="ghost" size="sm" onClick={onRetake} className="gap-2">
                <RotateCcw className="h-4 w-4" />
                Repetir test
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Title & Score */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Análisis Diferencial: {testName}
          </h1>
          <p className="text-muted-foreground mb-4">
            Completado el {new Date(result.completedAt).toLocaleDateString('es-ES', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
          <div className="flex items-center justify-center gap-4">
            <div className="text-center">
              <span className="text-4xl font-bold text-primary">{result.totalScore}</span>
              <span className="text-lg text-muted-foreground">/{result.maxScore}</span>
            </div>
            {getSeverityBadge(result.severity)}
            {result.percentile && (
              <span className="text-sm text-muted-foreground">
                Percentil {result.percentile}
              </span>
            )}
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Radar Chart + Differential */}
          <div className="lg:col-span-3 space-y-6">
            {/* Radar Chart */}
            <div className="results-card p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Perfil por Dominios
              </h2>
              <ResultsRadarChart domainScores={result.domainScores} />
              
              {/* Domain Legend */}
              <div className="grid grid-cols-2 gap-3 mt-4">
                {result.domainScores.map((domain) => (
                  <div key={domain.domain} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium text-foreground">{domain.domain}</span>
                    <div className="text-right">
                      <span className="text-sm font-bold text-primary">{domain.percentile}%</span>
                      <p className="text-xs text-muted-foreground">Percentil</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Differential Diagnosis */}
            {result.differentialDiagnosis && result.differentialDiagnosis.length > 0 && (
              <div className="space-y-4">
                {result.differentialDiagnosis.map((diff, index) => (
                  <DifferentialDiagnosisCard key={index} differential={diff} />
                ))}
              </div>
            )}
          </div>

          {/* Right: Evidence Panel */}
          <div className="lg:col-span-2">
            <div className="sticky top-24">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Panel de Evidencia
              </h2>
              <EvidencePanel 
                dsmCriteria={result.dsmCriteria} 
                clinicalNotes={result.clinicalNotes}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
