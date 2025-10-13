import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ScoreCardProps {
  title: string;
  score: number;
  color: string;
  icon?: React.ReactNode;
  description?: string;
}

export function ScoreCard({ title, score, color, icon, description }: ScoreCardProps) {
  return (
    <Card className="p-6 hover:shadow-lg transition-shadow border-border/50">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {icon && <div className="text-2xl">{icon}</div>}
          <div>
            <h3 className="font-semibold text-sm text-muted-foreground">{title}</h3>
            {description && <p className="text-xs text-muted-foreground/70 mt-1">{description}</p>}
          </div>
        </div>
        <div className="text-3xl font-bold" style={{ color }}>
          {score}
        </div>
      </div>
      <Progress value={score} className="h-2" style={{ 
        '--progress-background': color 
      } as React.CSSProperties} />
    </Card>
  );
}
