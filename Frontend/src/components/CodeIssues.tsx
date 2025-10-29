import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, Code2, FileText } from "lucide-react";
import { useState } from "react";

interface Issue {
  file: string;
  path: string;
  line: number;
  issue: string;
  severity: 'error' | 'warning' | 'info';
  codeSnippet: string;
  suggestion?: string;
}

interface CodeIssuesProps {
  issues: Issue[];
  category: string;
}

export function CodeIssues({ issues, category }: CodeIssuesProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!issues || issues.length === 0) {
    return null;
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'text-destructive border-destructive/50 bg-destructive/10';
      case 'warning':
        return 'text-warning border-warning/50 bg-warning/10';
      default:
        return 'text-muted-foreground border-muted-foreground/50 bg-muted/10';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'Error';
      case 'warning':
        return 'Warning';
      default:
        return 'Info';
    }
  };

  return (
    <Card className="p-4 border-border/50 mt-4">
      <div 
        className="flex items-center justify-between cursor-pointer hover:bg-muted/30 p-2 rounded"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          <span className="font-semibold">{category} Issues ({issues.length})</span>
        </div>
        <Badge variant="outline">{issues.length} issues found</Badge>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {issues.map((issue, index) => (
            <div key={index} className="border-l-4 border-muted/50 pl-4 py-2 hover:bg-muted/30 rounded-r">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono text-sm text-muted-foreground">
                    {issue.file}
                  </span>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-muted-foreground">Line {issue.line}</span>
                </div>
                <Badge className={getSeverityColor(issue.severity)} variant="outline">
                  {getSeverityLabel(issue.severity)}
                </Badge>
              </div>
              
              <p className="text-sm text-foreground mb-2">{issue.issue}</p>
              
              {issue.codeSnippet && (
                <div className="bg-muted/50 rounded-md p-3 font-mono text-xs overflow-x-auto">
                  <pre className="whitespace-pre-wrap break-words">
                    {issue.codeSnippet}
                  </pre>
                </div>
              )}
              
              {issue.suggestion && (
                <div className="mt-2 text-xs text-muted-foreground italic">
                  💡 Suggestion: {issue.suggestion}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
