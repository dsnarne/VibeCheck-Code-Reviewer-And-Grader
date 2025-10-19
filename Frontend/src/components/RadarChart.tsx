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
  // Default data if empty or invalid
  const defaultData = [
    { category: "Quality", score: 0, fullMark: 100 },
    { category: "Security", score: 0, fullMark: 100 },
    { category: "Git", score: 0, fullMark: 100 },
    { category: "Style", score: 0, fullMark: 100 },
    { category: "Originality", score: 0, fullMark: 100 },
    { category: "Team", score: 0, fullMark: 100 }
  ];

  const chartData = data && data.length > 0 ? data : defaultData;

  return (
    <Card className="p-6 bg-chart-bg border-border/50">
      <h3 className="font-semibold mb-6 text-lg">Score Breakdown</h3>
      <ResponsiveContainer width="100%" height={350}>
        <RechartsRadar data={chartData} margin={{ top: 40, right: 40, bottom: 40, left: 40 }}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis 
            dataKey="category" 
            tick={{ 
              fill: 'hsl(var(--foreground))', 
              fontSize: 14,
              dy: -15,
              dx: 0
            }}
            tickLine={false}
            axisLine={false}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]} 
            tick={{ 
              fill: 'hsl(var(--muted-foreground))',
              fontSize: 12,
              dy: 7
            }} 
            axisLine={false}
            tickLine={false}
          />
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

