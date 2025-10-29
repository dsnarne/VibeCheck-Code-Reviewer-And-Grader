import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileCode, Eye } from "lucide-react";
import { FileViewer } from "@/components/FileViewer";
import { useState } from "react";
import { apiService } from "@/lib/api";

interface FileItem {
  name: string;
  path: string;
  score?: number;
  issues?: string[];
  aiPercentage?: number;
  quality?: number;
  flags?: string[];
}

interface FileListProps {
  files: FileItem[];
  repoId?: string;
}

export function FileList({ files, repoId }: FileListProps) {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const getAIColor = (percentage: number) => {
    if (percentage >= 80) return "text-destructive";
    if (percentage >= 50) return "text-warning";
    return "text-muted-foreground";
  };

  const handleViewFile = async (file: FileItem) => {
    if (!repoId) {
      alert("Cannot view file: Repository ID not available");
      return;
    }

    setIsLoadingFile(true);
    try {
      console.log("Fetching file:", { repoId, filePath: file.path });
      console.log("File object:", file);
      
      // Try to find the correct path field
      const filePathToUse = file.path || file.relative_path || file.name;
      console.log("Using file path:", filePathToUse);
      
      // Get file content
      const fileData = await apiService.getFileContent(repoId, filePathToUse);
      console.log("File data received:", fileData);
      
      // Analyze the file for issues (on-demand analysis)
      try {
        console.log("Analyzing file for quality score and issues...");
        const analysisResult = await apiService.analyzeFile(repoId, filePathToUse);
        
        // Attach analysis results to file data
        fileData.quality_score = analysisResult.quality_score;
        fileData.issues_found = analysisResult.issues_found;
        
        // Convert issues to expected format
        fileData.issues = analysisResult.issues.map((iss: any) => ({
          line: iss.line,
          category: iss.category,
          severity: iss.severity || 'medium',
          issue: iss.issue,
          suggestion: iss.suggestion
        }));
        
        console.log(`✅ File analysis complete: quality=${analysisResult.quality_score}, issues=${analysisResult.issues_found}`);
      } catch (e) {
        console.warn('Could not analyze file:', e);
        fileData.issues = [];
        fileData.quality_score = 100;
      }
      
      setSelectedFile(fileData);
    } catch (error) {
      console.error("Failed to load file:", error);
      console.error("Error details:", {
        repoId,
        filePath: file.path,
        error: error instanceof Error ? error.message : String(error)
      });
      alert(`Failed to load file content: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoadingFile(false);
    }
  };

  return (
    <Card className="p-6 border-border/50">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-lg">File Analysis</h3>
        <Badge variant="outline">{files.length} files</Badge>
      </div>
      <div className="max-h-96 overflow-y-auto space-y-4 pr-2">
        {files.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-start gap-3 flex-1">
              <FileCode className="h-5 w-5 text-muted-foreground mt-1" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium">{file.name}</div>
                  {repoId && (
                    <button
                      onClick={() => handleViewFile(file)}
                      disabled={isLoadingFile}
                      className="px-3 py-1 text-xs bg-primary/10 hover:bg-primary/20 text-primary rounded-md transition-colors flex items-center gap-1"
                    >
                      <Eye className="h-3 w-3" />
                      {isLoadingFile ? 'Loading...' : 'View File'}
                    </button>
                  )}
                </div>
                <div className="text-xs text-muted-foreground mb-2">{file.path}</div>
                <div className="flex gap-2 flex-wrap">
                  {(file.flags || file.issues || []).slice(0, 3).map((flag, flagIndex) => (
                    <Badge
                      key={flagIndex}
                      variant="outline"
                      className={
                        flag.toLowerCase().includes("security")
                          ? "border-destructive/50 text-destructive"
                          : flag.toLowerCase().includes("excellent") || flag.toLowerCase().includes("good")
                          ? "border-quality/50 text-quality"
                          : "border-warning/50 text-warning"
                      }
                    >
                      {flag}
                    </Badge>
                  ))}
                  {((file.flags || file.issues || []).length > 3) && (
                    <Badge variant="outline" className="text-muted-foreground">+
                      { (file.flags || file.issues || []).length - 3 } more
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">AI%</div>
                <div className={`font-bold ${getAIColor(file.aiPercentage || 0)}`}>
                  {file.aiPercentage ?? 0}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">Quality</div>
                <div className="font-bold text-foreground">{file.quality ?? file.score ?? 0}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* File Viewer Modal */}
      {selectedFile && (
        <FileViewer
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}
    </Card>
  );
}

