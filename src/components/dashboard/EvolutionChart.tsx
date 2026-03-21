import { ClinicalEvolution } from '@/types/clinical';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface EvolutionChartProps {
  data: ClinicalEvolution[];
  patientName?: string;
}

export function EvolutionChart({ data, patientName }: EvolutionChartProps) {
  return (
    <div className="stat-card h-full">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-foreground">Evolución Clínica</h3>
        {patientName && (
          <p className="text-sm text-muted-foreground mt-1">{patientName}</p>
        )}
      </div>
      
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="evolutionGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="hsl(220, 13%, 91%)" 
              vertical={false}
            />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 9%, 46%)', fontSize: 12 }}
              dy={10}
            />
            <YAxis 
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 9%, 46%)', fontSize: 12 }}
              dx={-10}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(0, 0%, 100%)',
                border: '1px solid hsl(220, 13%, 91%)',
                borderRadius: '12px',
                boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.05)',
              }}
              labelStyle={{ color: 'hsl(220, 13%, 13%)', fontWeight: 600 }}
              formatter={(value: number) => [`${value}%`, 'Puntuación']}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="hsl(217, 91%, 60%)"
              strokeWidth={3}
              fill="url(#evolutionGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-primary" />
          <span className="text-muted-foreground">Índice de Recuperación</span>
        </div>
        <span className="font-semibold text-primary">+37% desde inicio</span>
      </div>
    </div>
  );
}
