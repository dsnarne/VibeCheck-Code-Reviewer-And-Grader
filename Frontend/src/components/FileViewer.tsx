import { Card } from "@/components/ui/card";
import { FileCode } from "lucide-react";

interface FileData {
  path: string;
  content: string;
  file_info: any;
}

interface FileViewerProps {
  file: FileData | null;
  onClose: () => void;
}

export function FileViewer({ file, onClose }: FileViewerProps) {
  if (!file) return null;

  const lines = file.content.split('\n');
  const lineCount = lines.length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <FileCode className="h-5 w-5" />
            <div>
              <h3 className="font-semibold">{file.path}</h3>
              <p className="text-sm text-muted-foreground">
                {lineCount} lines
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-md transition-colors text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>

        {/* Code Display */}
        <div className="flex-1 overflow-auto bg-muted/10 p-4">
          <div className="space-y-0 font-mono text-sm">
            {lines.map((line, index) => {
              const lineNum = index + 1;

              return (
                <div
                  key={index}
                  className="flex hover:bg-muted/30 transition-colors py-0.5"
                >
                  <span className="text-muted-foreground mr-4 w-12 text-right select-none text-xs">
                    {lineNum}
                  </span>
                  <span className="flex-1 break-all whitespace-pre-wrap">{line || ' '}</span>
                </div>
              );
            })}
          </div>
        </div>
      </Card>
    </div>
  );
}