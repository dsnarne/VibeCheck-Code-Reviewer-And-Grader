import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileCode } from "lucide-react";

interface FileItem {
  name: string;
  path: string;
  aiPercentage: number;
  quality: number;
  flags: string[];
}

interface FileListProps {
  files: FileItem[];
}

export function FileList({ files }: FileListProps) {
  const getAIColor = (percentage: number) => {
    if (percentage >= 80) return "text-destructive";
    if (percentage >= 50) return "text-warning";
    return "text-muted-foreground";
  };

  return (
    <Card className="p-6 border-border/50">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-lg">File Analysis</h3>
        <Badge variant="outline">{files.length} files</Badge>
      </div>
      <div className="space-y-4">
        {files.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-start gap-3 flex-1">
              <FileCode className="h-5 w-5 text-muted-foreground mt-1" />
              <div className="flex-1">
                <div className="font-medium mb-1">{file.name}</div>
                <div className="text-xs text-muted-foreground mb-2">{file.path}</div>
                <div className="flex gap-2 flex-wrap">
                  {file.flags.map((flag, flagIndex) => (
                    <Badge
                      key={flagIndex}
                      variant="outline"
                      className={
                        flag.includes("Security") || flag.includes("High AI%")
                          ? "border-destructive/50 text-destructive"
                          : flag.includes("Excellent") || flag.includes("Good")
                          ? "border-quality/50 text-quality"
                          : "border-warning/50 text-warning"
                      }
                    >
                      {flag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">AI%</div>
                <div className={`font-bold ${getAIColor(file.aiPercentage)}`}>
                  {file.aiPercentage}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">Quality</div>
                <div className="font-bold text-foreground">{file.quality}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
