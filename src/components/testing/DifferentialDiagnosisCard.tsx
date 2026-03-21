import { AlertTriangle, ArrowRight, HelpCircle } from 'lucide-react';
import { DifferentialDiagnosis } from '@/types/testing';
import { cn } from '@/lib/utils';

interface DifferentialDiagnosisCardProps {
  differential: DifferentialDiagnosis;
  className?: string;
}

export function DifferentialDiagnosisCard({ differential, className }: DifferentialDiagnosisCardProps) {
  const getOverlapColor = (percentage: number) => {
    if (percentage >= 70) return 'text-destructive bg-destructive/10 border-destructive/20';
    if (percentage >= 50) return 'text-warning bg-warning/10 border-warning/20';
    return 'text-muted-foreground bg-muted border-border';
  };

  return (
    <div className={cn('differential-alert', className)}>
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-warning/20">
          <AlertTriangle className="h-5 w-5 text-warning" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-foreground mb-1">
            Posible Diagnóstico Diferencial
          </h4>
          <p className="text-sm text-muted-foreground mb-4">
            Los resultados sugieren solapamiento entre diagnósticos que requiere evaluación adicional.
          </p>

          {/* Diagnosis comparison */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 p-3 bg-background rounded-lg border border-border">
              <span className="text-xs text-muted-foreground">Primario</span>
              <p className="text-sm font-medium text-foreground mt-0.5">
                {differential.primaryDiagnosis}
              </p>
            </div>
            
            <div className={cn(
              'px-3 py-1.5 rounded-full text-xs font-bold border',
              getOverlapColor(differential.overlapPercentage)
            )}>
              {differential.overlapPercentage}%
            </div>
            
            <div className="flex-1 p-3 bg-background rounded-lg border border-border">
              <span className="text-xs text-muted-foreground">Alternativo</span>
              <p className="text-sm font-medium text-foreground mt-0.5">
                {differential.alternativeDiagnosis}
              </p>
            </div>
          </div>

          {/* Distinguishing factors */}
          <div className="mb-4">
            <h5 className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
              <HelpCircle className="h-3.5 w-3.5" />
              Factores Distintivos
            </h5>
            <ul className="space-y-1.5">
              {differential.distinguishingFactors.map((factor, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                  <ArrowRight className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  {factor}
                </li>
              ))}
            </ul>
          </div>

          {/* Recommendation */}
          <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
            <span className="text-xs font-medium text-primary">Recomendación</span>
            <p className="text-sm text-foreground mt-1">
              {differential.recommendation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
