import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface CodeIssue {
  file: string;
  line: number;
  category: string;
  severity: string;
  type: string;
  description: string;
  snippet: string;
}

interface ScoreCardProps {
  title: string;
  score: number;
  color: string;
  icon?: React.ReactNode;
  description?: string;
  issues?: CodeIssue[];
}

export function ScoreCard({ title, score, color, icon, description, issues = [] }: ScoreCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Debug log to see what issues we have
  console.log(`ScoreCard ${title} has ${issues.length} issues:`, issues);
  
  // Temporary: Add sample issues for testing when no data available and score > 0
  const displayIssues = issues.length > 0 ? issues : (score > 0 ? [{
    file: "example.py",
    line: 42,
    category: title.toLowerCase(),
    severity: "medium",
    type: "test",
    description: `Sample issue for ${title}`,
    snippet: `def sample_function():  # This is a test issue`
  }] : []);

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow border-border/50">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {icon && <div className="text-muted-foreground">{icon}</div>}
          <div>
            <h3 className="font-semibold text-sm text-muted-foreground">{title}</h3>
            {description && <p className="text-xs text-muted-foreground/70 mt-1">{description}</p>}
          </div>
        </div>
        <div className="text-3xl font-bold" style={{ color }}>
          {score}
        </div>
      </div>
      <Progress value={score} className="h-2 mb-4" style={{ 
        '--progress-background': color 
      } as React.CSSProperties} />
      
      {displayIssues.length > 0 && (
        <button 
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsExpanded(!isExpanded);
            console.log('Button clicked, isExpanded:', !isExpanded);
          }}
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2 w-full mb-2"
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {isExpanded ? 'Hide' : 'Show'} Issues ({displayIssues.length})
        </button>
      )}
      
      {isExpanded && displayIssues.length > 0 && (
        <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
          {displayIssues.map((issue, idx) => (
            <div key={idx} className="p-3 rounded-lg border bg-muted/30 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium">{issue.file}</span>
                <span className="text-xs text-muted-foreground">line {issue.line}</span>
                <span className="px-2 py-0.5 rounded text-xs bg-destructive/10 text-destructive border border-destructive/20">
                  {issue.severity}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mb-2">{issue.description}</p>
              <code className="text-xs bg-muted px-2 py-1 rounded block font-mono">{issue.snippet}</code>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
