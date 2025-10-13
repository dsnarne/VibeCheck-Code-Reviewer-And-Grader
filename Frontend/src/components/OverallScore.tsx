import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Star, Zap } from "lucide-react";

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

  const getScoreBackground = (s: number) => {
    if (s >= 90) return "bg-gradient-to-br from-quality/20 to-quality/5";
    if (s >= 75) return "bg-gradient-to-br from-primary/20 to-primary/5";
    if (s >= 60) return "bg-gradient-to-br from-warning/20 to-warning/5";
    return "bg-gradient-to-br from-destructive/20 to-destructive/5";
  };

  const scoreDiff = previousScore ? score - previousScore : null;

  return (
    <Card className="overflow-hidden bg-gradient-to-br from-card via-card to-card/80 border-border/50 shadow-lg">
      {/* Header Section */}
      <div className="px-8 pt-8 pb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                VibeCheck
              </h1>
              <p className="text-muted-foreground text-sm">Repository Analysis</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-ai-indicator/10 text-ai-indicator border-ai-indicator/30 px-3 py-1">
            <Star className="h-3 w-3 mr-1" />
            {aiPercentage}% AI-Generated
          </Badge>
        </div>

        {/* Repository Name and Score Combined */}
        <div className="px-8 pb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-foreground">{repoName}</h2>
              <p className="text-muted-foreground text-sm">Overall Vibe Score</p>
            </div>
            
            <div className="flex items-center gap-4 mr-80">
              <div className="flex items-baseline gap-2">
                <div className={`text-6xl font-bold ${getScoreColor(score)} leading-none`}>
                  {score}
                </div>
                <div className="text-2xl font-bold text-muted-foreground">/100</div>
                <div className={`text-xl font-bold ${getScoreColor(score)} ml-2`}>
                  Grade {getScoreGrade(score)}
                </div>
              </div>
              
              {scoreDiff !== null && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background/50 backdrop-blur-sm">
                  {scoreDiff > 0 ? (
                    <>
                      <TrendingUp className="h-4 w-4 text-quality" />
                      <span className="text-sm font-medium text-quality">+{scoreDiff}</span>
                    </>
                  ) : scoreDiff < 0 ? (
                    <>
                      <TrendingDown className="h-4 w-4 text-destructive" />
                      <span className="text-sm font-medium text-destructive">{scoreDiff}</span>
                    </>
                  ) : (
                    <span className="text-sm font-medium text-muted-foreground">No change</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
