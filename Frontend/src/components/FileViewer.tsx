import { Card } from "@/components/ui/card";
import { FileCode, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface FileIssue {
  line: number;
  category: string;
  severity: string;
  issue: string;
  suggestion?: string;
}

interface FileData {
  path: string;
  content: string;
  file_info: any;
  issues?: FileIssue[];
}

interface FileViewerProps {
  file: FileData | null;
  onClose: () => void;
}

export function FileViewer({ file, onClose }: FileViewerProps) {
  if (!file) return null;

  const lines = file.content.split('\n');
  const lineCount = lines.length;
  
  // Create a map of issues by line number
  const issuesByLine = new Map<number, FileIssue[]>();
  (file.issues || []).forEach(issue => {
    const lineIssues = issuesByLine.get(issue.line) || [];
    lineIssues.push(issue);
    issuesByLine.set(issue.line, lineIssues);
  });
  
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'error':
      case 'high':
        return 'bg-destructive/20 border-l-destructive';
      case 'warning':
      case 'medium':
        return 'bg-warning/20 border-l-warning';
      default:
        return 'bg-muted/20 border-l-muted';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <FileCode className="h-5 w-5" />
            <div>
              <h3 className="font-semibold">{file.path}</h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>{lineCount} lines</span>
                {(file.issues || []).length > 0 && (
                  <Badge variant="destructive" className="ml-2">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    {(file.issues || []).length} issues
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-md transition-colors text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>

        {/* Issues Summary */}
        {(file.issues || []).length > 0 && (
          <div className="p-4 border-b bg-muted/10 space-y-2 max-h-32 overflow-y-auto">
            <p className="text-xs font-semibold text-muted-foreground">Issues in this file:</p>
            {(file.issues || []).map((issue, idx) => (
              <div key={idx} className="text-xs flex items-start gap-2">
                <Badge variant={issue.severity === 'error' || issue.severity === 'high' ? 'destructive' : 'secondary'} className="text-xs">
                  {issue.category}
                </Badge>
                <span className="text-muted-foreground">Line {issue.line}: {issue.issue}</span>
              </div>
            ))}
          </div>
        )}

        {/* Code Display */}
        <div className="flex-1 overflow-auto bg-muted/10 p-4">
          <div className="space-y-0 font-mono text-sm">
            {lines.map((line, index) => {
              const lineNum = index + 1;
              const lineIssues = issuesByLine.get(lineNum) || [];
              const hasIssue = lineIssues.length > 0;

              return (
                <div
                  key={index}
                  className={`flex hover:bg-muted/30 transition-colors py-0.5 border-l-4 ${
                    hasIssue ? getSeverityColor(lineIssues[0].severity) : ''
                  }`}
                >
                  <span className="text-muted-foreground mr-4 w-12 text-right select-none text-xs">
                    {lineNum}
                  </span>
                  <span className="flex-1 break-all whitespace-pre-wrap">{line || ' '}</span>
                  {hasIssue && (
                    <div className="ml-4 flex gap-1">
                      {lineIssues.map((issue, idx) => (
                        <Badge
                          key={idx}
                          variant={issue.severity === 'error' || issue.severity === 'high' ? 'destructive' : 'secondary'}
                          className="text-xs"
                          title={issue.issue}
                        >
                          <AlertCircle className="h-3 w-3 mr-1" />
                          {issue.category}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </Card>
    </div>
  );
}