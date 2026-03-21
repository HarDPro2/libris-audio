import { Patient } from '@/types/clinical';
import { User, Calendar, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface PatientCardProps {
  patient: Patient;
  onSelect?: (patient: Patient) => void;
}

const statusLabels = {
  active: 'Activo',
  inactive: 'Inactivo',
  completed: 'Completado',
};

const statusColors = {
  active: 'bg-success/10 text-success',
  inactive: 'bg-muted text-muted-foreground',
  completed: 'bg-primary/10 text-primary',
};

export function PatientCard({ patient, onSelect }: PatientCardProps) {
  return (
    <div className="stat-card">
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <User className="h-6 w-6 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-foreground truncate">{patient.name}</h3>
            <span className={cn(
              'px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap',
              statusColors[patient.status]
            )}>
              {statusLabels[patient.status]}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{patient.age} años</p>
          {patient.diagnosis && (
            <p className="text-sm text-muted-foreground mt-2 line-clamp-1">{patient.diagnosis}</p>
          )}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {patient.nextAppointment && (
            <div className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4" />
              <span>{patient.nextAppointment}</span>
            </div>
          )}
          {patient.evolutionScore && (
            <div className="flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4" />
              <span>{patient.evolutionScore}%</span>
            </div>
          )}
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={() => onSelect?.(patient)}
          className="text-primary hover:text-primary hover:bg-primary/10"
        >
          Ver perfil
        </Button>
      </div>
    </div>
  );
}
