import { CheckCircle2, XCircle, ChevronDown } from 'lucide-react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { DSMCriteria } from '@/types/testing';
import { cn } from '@/lib/utils';

interface EvidencePanelProps {
  dsmCriteria: DSMCriteria[];
  clinicalNotes: string[];
  className?: string;
}

export function EvidencePanel({ dsmCriteria, clinicalNotes, className }: EvidencePanelProps) {
  return (
    <div className={cn('space-y-4', className)}>
      <Accordion type="multiple" defaultValue={['dsm-criteria', 'clinical-notes']} className="space-y-3">
        {/* DSM-5 Criteria */}
        {dsmCriteria.map((criteria) => (
          <AccordionItem 
            key={criteria.code} 
            value={`dsm-${criteria.code}`}
            className="border border-border rounded-xl overflow-hidden bg-card"
          >
            <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50 [&[data-state=open]>svg]:rotate-180">
              <div className="flex items-center gap-3 text-left">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <span className="text-xs font-bold text-primary">{criteria.criteriaMetCount}/{criteria.totalCriteria}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-foreground">{criteria.name}</span>
                  <p className="text-xs text-muted-foreground">{criteria.code}</p>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-2 pt-2">
                {criteria.criteriaDetails.map((detail, index) => (
                  <div 
                    key={index}
                    className={cn(
                      'flex items-start gap-3 p-3 rounded-lg',
                      detail.met ? 'bg-success/5' : 'bg-muted/50'
                    )}
                  >
                    {detail.met ? (
                      <CheckCircle2 className="h-4 w-4 text-success shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={cn(
                        'text-sm',
                        detail.met ? 'text-foreground' : 'text-muted-foreground'
                      )}>
                        {detail.criterion}
                      </p>
                      {detail.evidence && (
                        <p className="text-xs text-primary mt-1">
                          Evidencia: {detail.evidence}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}

        {/* Clinical Notes */}
        <AccordionItem 
          value="clinical-notes"
          className="border border-border rounded-xl overflow-hidden bg-card"
        >
          <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50">
            <div className="flex items-center gap-3 text-left">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <span className="text-xs font-bold text-primary">{clinicalNotes.length}</span>
              </div>
              <span className="text-sm font-medium text-foreground">Notas Clínicas Sugeridas</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <ul className="space-y-2 pt-2">
              {clinicalNotes.map((note, index) => (
                <li 
                  key={index}
                  className="flex items-start gap-2 text-sm text-foreground p-3 bg-muted/50 rounded-lg"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                    {index + 1}
                  </span>
                  {note}
                </li>
              ))}
            </ul>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
