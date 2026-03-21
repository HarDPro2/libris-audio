import { useState } from 'react';
import { AppointmentCard } from '@/components/dashboard/AppointmentCard';
import { EvolutionChart } from '@/components/dashboard/EvolutionChart';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { mockAppointments, mockEvolutionData, mockPatients } from '@/data/mockData';
import { Users, Calendar, TrendingUp, Clock } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function Dashboard() {
  const [selectedPatientId, setSelectedPatientId] = useState(mockPatients[0].id);
  const selectedPatient = mockPatients.find(p => p.id === selectedPatientId);
  
  const todayAppointments = mockAppointments.filter(a => a.status === 'scheduled');

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Buenos días, Dr. Ramírez</h1>
        <p className="text-muted-foreground mt-1">Resumen de su actividad clínica</p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Citas Hoy"
          value={todayAppointments.length}
          icon={Calendar}
          variant="primary"
          description="4 programadas"
        />
        <StatsCard
          title="Pacientes Activos"
          value={mockPatients.filter(p => p.status === 'active').length}
          icon={Users}
          variant="success"
          trend={{ value: 12, isPositive: true }}
        />
        <StatsCard
          title="Próxima Cita"
          value="09:00"
          icon={Clock}
          description="María García López"
        />
        <StatsCard
          title="Promedio Evolución"
          value="68%"
          icon={TrendingUp}
          variant="primary"
          trend={{ value: 8, isPositive: true }}
        />
      </div>
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointments */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Citas del Día</h2>
            <span className="text-sm text-muted-foreground">
              {todayAppointments.length} citas
            </span>
          </div>
          <div className="space-y-3">
            {todayAppointments.map((appointment) => (
              <AppointmentCard 
                key={appointment.id} 
                appointment={appointment}
                onClick={(apt) => console.log('Selected appointment:', apt)}
              />
            ))}
          </div>
        </div>
        
        {/* Evolution Chart */}
        <div className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Evolución Clínica</h2>
            <Select value={selectedPatientId} onValueChange={setSelectedPatientId}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Seleccionar paciente" />
              </SelectTrigger>
              <SelectContent>
                {mockPatients.filter(p => p.status === 'active').map((patient) => (
                  <SelectItem key={patient.id} value={patient.id}>
                    {patient.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <EvolutionChart 
            data={mockEvolutionData} 
            patientName={selectedPatient?.name}
          />
        </div>
      </div>
    </div>
  );
}
