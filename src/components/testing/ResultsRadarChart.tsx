import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { DomainScore } from '@/types/testing';

interface ResultsRadarChartProps {
  domainScores: DomainScore[];
  className?: string;
}

export function ResultsRadarChart({ domainScores, className }: ResultsRadarChartProps) {
  const data = domainScores.map((d) => ({
    domain: d.domain,
    value: d.percentile,
    fullMark: 100,
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid 
            stroke="hsl(var(--border))" 
            strokeDasharray="3 3"
          />
          <PolarAngleAxis 
            dataKey="domain" 
            tick={{ 
              fill: 'hsl(var(--muted-foreground))', 
              fontSize: 11,
              fontWeight: 500
            }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
            tickCount={5}
          />
          <Radar
            name="Percentil"
            dataKey="value"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.3}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            formatter={(value: number) => [`${value}%`, 'Percentil']}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
