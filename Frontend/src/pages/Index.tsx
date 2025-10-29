import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Search, Plus, Code, Shield, GitBranch, Palette, Lightbulb, Users, Loader2 } from "lucide-react";
import { ScoreCard } from "@/components/ScoreCard";
import { RadarChart } from "@/components/RadarChart";
import { FileList } from "@/components/FileList";
import { OverallScore } from "@/components/OverallScore";
import { apiService, ScoringResponse, CodeIssue } from "@/lib/api";

const Index = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [scoringData, setScoringData] = useState<ScoringResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [issuesData, setIssuesData] = useState<Record<string, CodeIssue[]>>({});
  const [repoId, setRepoId] = useState<string | null>(null);

  // Load the latest repository on mount
  useEffect(() => {
    const loadLatestRepo = async () => {
      if (!scoringData && !isLoading) {
        try {
          // First try to get repos list to find the latest
          const reposResponse = await fetch('http://localhost:8000/api/repos?limit=1');
          if (reposResponse.ok) {
            const repos = await reposResponse.json();
            if (repos && repos.length > 0) {
              const latestRepoId = repos[0].id;
              setRepoId(latestRepoId);
              
              // Load scoring data for this repo
              const scoringResponse = await apiService.getRepositoryScoring(latestRepoId);
              setScoringData(scoringResponse);
              console.log('Loaded latest repository:', latestRepoId);
            }
          }
        } catch (error) {
          console.error("Failed to load latest repository:", error);
        }
      }
    };
    loadLatestRepo();
  }, []); // Run once on mount

  // Default data for when no analysis is loaded
  const defaultScores = [
    { title: "Quality", score: 0, color: "hsl(var(--quality))", icon: <Code className="h-6 w-6" />, description: "Code maintainability & complexity" },
    { title: "Security", score: 0, color: "hsl(var(--security))", icon: <Shield className="h-6 w-6" />, description: "Vulnerabilities & best practices" },
    { title: "Git Hygiene", score: 0, color: "hsl(var(--git))", icon: <GitBranch className="h-6 w-6" />, description: "Commit quality & PR practices" },
    { title: "Style", score: 0, color: "hsl(var(--style))", icon: <Palette className="h-6 w-6" />, description: "Consistency & conventions" },
    { title: "Originality", score: 0, color: "hsl(var(--originality))", icon: <Lightbulb className="h-6 w-6" />, description: "Unique implementations" },
    { title: "Team Balance", score: 0, color: "hsl(var(--team))", icon: <Users className="h-6 w-6" />, description: "Contribution distribution" },
  ];

  const handleAnalyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // First, create a user (you might want to implement proper user management)
      const userResponse = await apiService.createUser({
        email: "demo@example.com",
        name: "Demo User",
        github_username: "demo"
      });

      // Analyze the repository
      const analysisResponse = await apiService.analyzeAndStoreRepository({
        repo_url: repoUrl,
        user_id: userResponse.user.id,
        window_days: 90,
        max_commits: 500,
        download_zipball: true
      });

      if (analysisResponse.error) {
        setError(analysisResponse.error);
        return;
      }

      if (analysisResponse.repo_id) {
        setRepoId(analysisResponse.repo_id);
        
        // Get ChatGPT scoring
        const scoringResponse = await apiService.getRepositoryScoring(analysisResponse.repo_id);
        setScoringData(scoringResponse);

        // Try to fetch detailed code issues for each category
        try {
          const issuesResponse = await apiService.getRepositoryIssues(analysisResponse.repo_id);
          setIssuesData(issuesResponse.issues || {});

          // Also merge issues into files for the FileList component
          const issuesByPath: Record<string, { issue: string; line: number }[]> = {};
          Object.values(issuesResponse.issues || {}).forEach((arr: any) => {
            (arr as any[]).forEach((iss: any) => {
              const key = iss.path;
              if (!issuesByPath[key]) issuesByPath[key] = [];
              issuesByPath[key].push({ issue: iss.issue, line: iss.line });
            });
          });

          const mergedFiles = (scoringResponse.files || []).map(f => ({
            ...f,
            issues: (issuesByPath[f.path] || []).map(x => `${x.issue} (L${x.line})`),
          }));

          setScoringData({ ...scoringResponse, files: mergedFiles });
        } catch (e) {
          console.warn('Could not fetch issues:', e);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  // Use scoring data if available, otherwise use default
  const scores = (scoringData?.scores || defaultScores).map((score, idx) => ({
    ...score,
    issues: ('issues' in score ? score.issues : []) || []
  }));
  const radarData = scoringData?.radar_data || [];
  const files = (scoringData?.files || []).map(file => ({
    ...file,
    aiPercentage: file.ai_percentage || 0
  }));
  const repoName = scoringData ? scoringData.analysis?.split(" ")[0] || "Repository" : "No Repository";
  const overallScore = scoringData?.overall_score || 0;
  const aiPercentage = scoringData?.ai_percentage || 0;
  const previousScore = scoringData?.previous_score;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Overall Score */}
        <div className="mb-8">
          <OverallScore
            score={overallScore}
            aiPercentage={aiPercentage}
            previousScore={previousScore}
            repoName={repoName}
          />
        </div>

        {/* Repository Analysis Input */}
        <div className="mb-8">
          <div className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">Analyze Repository</h2>
            <div className="flex gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Enter GitHub repository URL (e.g., https://github.com/owner/repo)"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button 
                onClick={handleAnalyzeRepository} 
                disabled={isLoading || !repoUrl.trim()}
                className="gap-2"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                {isLoading ? "Analyzing..." : "Analyze Repository"}
              </Button>
            </div>
            {error && (
              <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-destructive text-sm">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Search & Actions */}
        <div className="flex gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search files, issues, or metrics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Score Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {scores.map((score, index) => {
            // Map category name to issues data
            const categoryKey = score.title.toLowerCase();
            const categoryIssues = issuesData[categoryKey] || [];
            
            // Debug logging
            console.log(`Category: ${score.title} (${categoryKey}), Issues found:`, categoryIssues);
            
            const mappedIssues = categoryIssues.map(issue => ({
              file: issue.file,
              line: issue.line,
              category: issue.category,
              severity: issue.severity === 'error' ? 'high' : issue.severity === 'warning' ? 'medium' : 'low',
              type: issue.issue_type,
              description: issue.issue,
              snippet: issue.codeSnippet,
              suggestion: issue.suggestion
            }));
            
            console.log(`Mapped issues for ${score.title}:`, mappedIssues);
            
            return (
              <ScoreCard 
                key={index} 
                {...score} 
                issues={mappedIssues}
              />
            );
          })}
        </div>

        {/* Radar Chart */}
        <div className="mb-8">
          <RadarChart data={radarData} />
        </div>

        {/* File List */}
        {files.length > 0 ? (
          <FileList files={files} repoId={repoId || undefined} />
        ) : (
          <Card className="p-6 border-border/50">
            <div className="text-center py-8">
              <p className="text-muted-foreground">No files available for display.</p>
              <p className="text-sm text-muted-foreground mt-2">
                Files may not have been stored during repository analysis.
              </p>
            </div>
          </Card>
        )}

        {/* Analysis and Recommendations */}
        {scoringData && (
          <div className="mt-8 space-y-6">
            <div className="bg-card p-6 rounded-lg border">
              <h3 className="text-lg font-semibold mb-4">Analysis</h3>
              <p className="text-muted-foreground">{scoringData.analysis}</p>
            </div>
            
            {scoringData.recommendations && scoringData.recommendations.length > 0 && (
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {scoringData.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-primary font-semibold">•</span>
                      <span className="text-muted-foreground">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* No Data State */}
        {!scoringData && !isLoading && (
          <div className="text-center py-12">
            <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-4">
              <Code className="h-12 w-12 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No Repository Analyzed</h3>
            <p className="text-muted-foreground mb-4">
              Enter a GitHub repository URL above to get started with analysis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
