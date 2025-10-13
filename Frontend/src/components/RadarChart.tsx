import { Card } from "@/components/ui/card";
import { Radar, RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

interface RadarChartProps {
  data: Array<{
    category: string;
    score: number;
    fullMark: number;
  }>;
}

export function RadarChart({ data }: RadarChartProps) {
  return (
    <Card className="p-6 bg-chart-bg border-border/50">
      <h3 className="font-semibold mb-6 text-lg">Score Breakdown</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsRadar data={data}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis 
            dataKey="category" 
            tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
          />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))' }} />
          <Radar 
            name="Score" 
            dataKey="score" 
            stroke="hsl(var(--primary))" 
            fill="hsl(var(--primary))" 
            fillOpacity={0.6}
          />
        </RechartsRadar>
      </ResponsiveContainer>
    </Card>
  );
}

