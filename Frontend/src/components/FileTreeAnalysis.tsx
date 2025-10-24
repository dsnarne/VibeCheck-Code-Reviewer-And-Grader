import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  FileCode, 
  Folder, 
  FolderOpen, 
  Search, 
  AlertTriangle, 
  Info, 
  CheckCircle,
  Code,
  FileText,
  Image,
  Settings
} from "lucide-react";
import { useState, useMemo } from "react";
import { CodeIssue } from "@/lib/api";

interface FileAnalysis {
  file_path: string;
  file_type: string;
  metrics: {
    lines_of_code: number;
    cyclomatic_complexity: number;
    maintainability_index: number;
    comment_ratio: number;
    function_count: number;
    class_count: number;
    max_function_length: number;
    avg_function_length: number;
  };
  issues: CodeIssue[];
  is_key_file: boolean;
  key_file_reason?: string;
}

interface FileTreeAnalysisProps {
  fileAnalyses: FileAnalysis[];
  onFileSelect?: (file: FileAnalysis) => void;
}

interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: TreeNode[];
  analysis?: FileAnalysis;
  isExpanded?: boolean;
}

export function FileTreeAnalysis({ fileAnalyses, onFileSelect }: FileTreeAnalysisProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFile, setSelectedFile] = useState<FileAnalysis | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // Build tree structure from file analyses
  const fileTree = useMemo(() => {
    const tree: TreeNode = { name: "root", path: "", type: "folder", children: [] };
    
    fileAnalyses.forEach(analysis => {
      const pathParts = analysis.file_path.split('/').filter(Boolean);
      let current = tree;
      
      pathParts.forEach((part, index) => {
        const isLast = index === pathParts.length - 1;
        const currentPath = pathParts.slice(0, index + 1).join('/');
        
        if (isLast) {
          // This is a file
          const fileNode: TreeNode = {
            name: part,
            path: analysis.file_path,
            type: 'file',
            analysis
          };
          current.children!.push(fileNode);
        } else {
          // This is a folder
          let folderNode = current.children?.find(child => child.name === part && child.type === 'folder');
          if (!folderNode) {
            folderNode = {
              name: part,
              path: currentPath,
              type: 'folder',
              children: []
            };
            current.children!.push(folderNode);
          }
          current = folderNode;
        }
      });
    });
    
    return tree;
  }, [fileAnalyses]);

  // Filter tree based on search query
  const filteredTree = useMemo(() => {
    if (!searchQuery) return fileTree;
    
    const filterNode = (node: TreeNode): TreeNode | null => {
      if (node.type === 'file') {
        const matches = node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                       node.path.toLowerCase().includes(searchQuery.toLowerCase());
        return matches ? node : null;
      } else {
        const filteredChildren = node.children
          ?.map(filterNode)
          .filter(Boolean) as TreeNode[];
        
        if (filteredChildren.length > 0) {
          return { ...node, children: filteredChildren };
        }
        return null;
      }
    };
    
    return filterNode(fileTree) || { name: "root", path: "", type: "folder", children: [] };
  }, [fileTree, searchQuery]);

  const getFileIcon = (filePath: string, fileType: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    
    if (fileType === 'python' || ext === 'py') return <Code className="h-4 w-4 text-blue-500" />;
    if (fileType === 'javascript' || ext === 'js') return <Code className="h-4 w-4 text-yellow-500" />;
    if (fileType === 'typescript' || ext === 'ts') return <Code className="h-4 w-4 text-blue-600" />;
    if (ext === 'md') return <FileText className="h-4 w-4 text-gray-500" />;
    if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(ext || '')) return <Image className="h-4 w-4 text-green-500" />;
    if (['json', 'yaml', 'yml', 'xml'].includes(ext || '')) return <Settings className="h-4 w-4 text-orange-500" />;
    
    return <FileCode className="h-4 w-4 text-muted-foreground" />;
  };

  const getIssueSeverityColor = (issues: any[]) => {
    const highIssues = issues.filter(i => i.severity === 'high').length;
    const mediumIssues = issues.filter(i => i.severity === 'medium').length;
    
    if (highIssues > 0) return "text-destructive";
    if (mediumIssues > 0) return "text-warning";
    return "text-quality";
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const handleFileClick = (file: FileAnalysis) => {
    setSelectedFile(file);
    onFileSelect?.(file);
  };

  const renderTreeNode = (node: TreeNode, depth = 0) => {
    const isExpanded = expandedFolders.has(node.path);
    const hasIssues = node.analysis?.issues.length || 0;
    const issueColor = node.analysis ? getIssueSeverityColor(node.analysis.issues) : "";

    return (
      <div key={node.path} className="select-none">
        <div
          className={`flex items-center gap-2 py-1 px-2 rounded hover:bg-muted/50 cursor-pointer ${
            selectedFile?.file_path === node.path ? 'bg-primary/10' : ''
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === 'folder') {
              toggleFolder(node.path);
            } else if (node.analysis) {
              handleFileClick(node.analysis);
            }
          }}
        >
          {node.type === 'folder' ? (
            isExpanded ? (
              <FolderOpen className="h-4 w-4 text-blue-500" />
            ) : (
              <Folder className="h-4 w-4 text-blue-500" />
            )
          ) : (
            getFileIcon(node.path, node.analysis?.file_type || '')
          )}
          
          <span className="text-sm truncate flex-1">{node.name}</span>
          
          {node.analysis && (
            <div className="flex items-center gap-1">
              {node.analysis.is_key_file && (
                <Badge variant="outline" className="text-xs bg-primary/10 text-primary">
                  Key
                </Badge>
              )}
              {hasIssues > 0 && (
                <Badge 
                  variant="outline" 
                  className={`text-xs ${issueColor} border-current`}
                >
                  {hasIssues}
                </Badge>
              )}
            </div>
          )}
        </div>
        
        {node.type === 'folder' && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-destructive" />;
      case 'medium':
        return <Info className="h-4 w-4 text-warning" />;
      case 'low':
        return <CheckCircle className="h-4 w-4 text-quality" />;
      default:
        return <Info className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="grid grid-cols-3 gap-6 h-96">
      {/* File Tree - Left Panel (1/3) */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8"
          />
        </div>
        <div className="overflow-y-auto h-80">
          {filteredTree.children?.map(node => renderTreeNode(node))}
        </div>
      </Card>

      {/* File Analysis - Right Panel (2/3) */}
      <Card className="col-span-2 p-4">
        {selectedFile ? (
          <div className="h-full overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-2">{selectedFile.file_path}</h3>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Type: {selectedFile.file_type}</span>
                <span>Lines: {selectedFile.metrics.lines_of_code}</span>
                <span>Functions: {selectedFile.metrics.function_count}</span>
                <span>Classes: {selectedFile.metrics.class_count}</span>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-3 rounded-lg bg-muted/30">
                <div className="text-sm text-muted-foreground">Complexity</div>
                <div className="text-lg font-semibold">{selectedFile.metrics.cyclomatic_complexity}</div>
              </div>
              <div className="p-3 rounded-lg bg-muted/30">
                <div className="text-sm text-muted-foreground">Maintainability</div>
                <div className="text-lg font-semibold">{selectedFile.metrics.maintainability_index.toFixed(1)}</div>
              </div>
              <div className="p-3 rounded-lg bg-muted/30">
                <div className="text-sm text-muted-foreground">Comment Ratio</div>
                <div className="text-lg font-semibold">{(selectedFile.metrics.comment_ratio * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 rounded-lg bg-muted/30">
                <div className="text-sm text-muted-foreground">Avg Function Length</div>
                <div className="text-lg font-semibold">{selectedFile.metrics.avg_function_length.toFixed(1)}</div>
              </div>
            </div>

            {/* Issues */}
            {selectedFile.issues.length > 0 ? (
              <div>
                <h4 className="text-md font-semibold mb-3">Issues ({selectedFile.issues.length})</h4>
                <div className="space-y-3">
                  {selectedFile.issues.map((issue, index) => (
                    <div key={index} className="p-3 rounded-lg border bg-muted/30">
                      <div className="flex items-start gap-2 mb-2">
                        {getSeverityIcon(issue.severity)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium">Line {issue.line}</span>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${
                                issue.severity === 'high' ? 'border-destructive text-destructive' :
                                issue.severity === 'medium' ? 'border-warning text-warning' :
                                'border-quality text-quality'
                              }`}
                            >
                              {issue.severity}
                            </Badge>
                            <span className="text-xs text-muted-foreground">{issue.type}</span>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">{issue.description}</p>
                          {issue.snippet && (
                            <code className="text-xs bg-muted px-2 py-1 rounded block font-mono mb-2">
                              {issue.snippet}
                            </code>
                          )}
                          {issue.suggestion && (
                            <p className="text-xs text-quality italic">
                              💡 {issue.suggestion}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 text-quality" />
                <p>No issues found in this file</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <FileCode className="h-12 w-12 mx-auto mb-4" />
              <p>Select a file from the tree to view its analysis</p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
