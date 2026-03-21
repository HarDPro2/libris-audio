import { Appointment } from '@/types/clinical';
import { Clock, User, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AppointmentCardProps {
  appointment: Appointment;
  onClick?: (appointment: Appointment) => void;
}

const typeLabels = {
  initial: 'Primera consulta',
  followup: 'Seguimiento',
  assessment: 'Evaluación',
};

const typeColors = {
  initial: 'bg-primary/10 text-primary',
  followup: 'bg-success/10 text-success',
  assessment: 'bg-warning/10 text-warning',
};

export function AppointmentCard({ appointment, onClick }: AppointmentCardProps) {
  return (
    <button
      onClick={() => onClick?.(appointment)}
      className="stat-card w-full text-left hover:border-primary/30 transition-all duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-lg font-semibold text-foreground">{appointment.time}</span>
        </div>
        <span className={cn(
          'px-2.5 py-1 rounded-full text-xs font-medium',
          typeColors[appointment.type]
        )}>
          {typeLabels[appointment.type]}
        </span>
      </div>
      
      <div className="flex items-center gap-2 mb-2">
        <User className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium text-foreground">{appointment.patientName}</span>
      </div>
      
      {appointment.notes && (
        <div className="flex items-start gap-2 mt-3 pt-3 border-t border-border">
          <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
          <p className="text-sm text-muted-foreground line-clamp-2">{appointment.notes}</p>
        </div>
      )}
    </button>
  );
}
