import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  AlertCircle, 
  Calendar, 
  FileText, 
  RefreshCw, 
  Eye,
  Star
} from "lucide-react";

interface ExistingAnalysis {
  exists: boolean;
  repo_id?: string;
  full_name?: string;
  analysis_date?: string;
  overall_score?: number;
  file_count?: number;
  has_file_analysis?: boolean;
  message?: string;
}

interface RepoAnalysisDialogProps {
  existingAnalysis: ExistingAnalysis | null;
  isOpen: boolean;
  onClose: () => void;
  onViewExisting: () => void;
  onReanalyze: () => void;
  isLoading?: boolean;
}

export function RepoAnalysisDialog({ 
  existingAnalysis, 
  isOpen, 
  onClose, 
  onViewExisting, 
  onReanalyze,
  isLoading = false 
}: RepoAnalysisDialogProps) {
  if (!isOpen || !existingAnalysis?.exists) return null;

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-quality";
    if (score >= 75) return "text-primary";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  const getScoreGrade = (score: number) => {
    if (score >= 90) return "A";
    if (score >= 80) return "B";
    if (score >= 70) return "C";
    if (score >= 60) return "D";
    return "F";
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-2 rounded-lg bg-primary/10">
            <AlertCircle className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold mb-1">Repository Already Analyzed</h2>
            <p className="text-sm text-muted-foreground">
              This repository has been analyzed before. Choose an option below.
            </p>
          </div>
        </div>

        {/* Repository Info */}
        <div className="mb-6 p-4 rounded-lg bg-muted/30">
          <h3 className="font-semibold mb-3">{existingAnalysis.full_name}</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Last analyzed:</span>
              <span>{formatDate(existingAnalysis.analysis_date || '')}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Files analyzed:</span>
              <span>{existingAnalysis.file_count || 0}</span>
            </div>
            
            {existingAnalysis.overall_score !== undefined && (
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Overall score:</span>
                <div className="flex items-center gap-2">
                  <span className={`font-semibold ${getScoreColor(existingAnalysis.overall_score)}`}>
                    {existingAnalysis.overall_score}/100
                  </span>
                  <Badge variant="outline" className="text-xs">
                    Grade {getScoreGrade(existingAnalysis.overall_score)}
                  </Badge>
                </div>
              </div>
            )}
            
            {existingAnalysis.has_file_analysis && (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs bg-quality/10 text-quality border-quality/30">
                  Enhanced Analysis Available
                </Badge>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Button 
            onClick={onViewExisting} 
            className="w-full gap-2"
            disabled={isLoading}
          >
            <Eye className="h-4 w-4" />
            View Previous Analysis
          </Button>
          
          <Button 
            onClick={onReanalyze} 
            variant="outline" 
            className="w-full gap-2"
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Re-analyzing...' : 'Re-analyze Repository'}
          </Button>
          
          <Button 
            onClick={onClose} 
            variant="ghost" 
            className="w-full"
            disabled={isLoading}
          >
            Cancel
          </Button>
        </div>

        {/* Warning Note */}
        <div className="mt-4 p-3 rounded-lg bg-warning/10 border border-warning/20">
          <p className="text-xs text-warning">
            <strong>Note:</strong> Re-analyzing will replace the existing analysis with fresh data. 
            This may take a few minutes depending on the repository size.
          </p>
        </div>
      </Card>
    </div>
  );
}
