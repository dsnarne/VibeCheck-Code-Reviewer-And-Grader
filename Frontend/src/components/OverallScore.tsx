import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown } from "lucide-react";

interface OverallScoreProps {
  score: number;
  aiPercentage: number;
  previousScore?: number;
  repoName: string;
}

export function OverallScore({ score, aiPercentage, previousScore, repoName }: OverallScoreProps) {
  const getScoreColor = (s: number) => {
    if (s >= 90) return "text-quality";
    if (s >= 75) return "text-primary";
    if (s >= 60) return "text-warning";
    return "text-destructive";
  };

  const getScoreGrade = (s: number) => {
    if (s >= 90) return "A";
    if (s >= 80) return "B";
    if (s >= 70) return "C";
    if (s >= 60) return "D";
    return "F";
  };

  const scoreDiff = previousScore ? score - previousScore : null;

  return (
    <Card className="p-8 bg-gradient-to-br from-card via-card to-card/80 border-border/50">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">{repoName}</h2>
          <Badge variant="outline" className="bg-ai-indicator/10 text-ai-indicator border-ai-indicator/30">
            {aiPercentage}% AI-Generated
          </Badge>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground mb-1">Overall Score</div>
          <div className={`text-6xl font-bold ${getScoreColor(score)}`}>
            {score}
            <span className="text-2xl ml-2 text-muted-foreground">{getScoreGrade(score)}</span>
          </div>
          {scoreDiff !== null && (
            <div className="flex items-center gap-1 mt-2 justify-end">
              {scoreDiff > 0 ? (
                <>
                  <TrendingUp className="h-4 w-4 text-quality" />
                  <span className="text-sm text-quality">+{scoreDiff} from last scan</span>
                </>
              ) : scoreDiff < 0 ? (
                <>
                  <TrendingDown className="h-4 w-4 text-destructive" />
                  <span className="text-sm text-destructive">{scoreDiff} from last scan</span>
                </>
              ) : (
                <span className="text-sm text-muted-foreground">No change</span>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
