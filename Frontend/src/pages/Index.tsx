import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Code, Shield, GitBranch, Palette, Lightbulb, Users, Loader2 } from "lucide-react";
import { ScoreCard } from "@/components/ScoreCard";
import { RadarChart } from "@/components/RadarChart";
import { FileList } from "@/components/FileList";
import { OverallScore } from "@/components/OverallScore";
import { apiService, ScoringResponse } from "@/lib/api";

const Index = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [scoringData, setScoringData] = useState<ScoringResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        // Get ChatGPT scoring
        const scoringResponse = await apiService.getRepositoryScoring(analysisResponse.repo_id);
        setScoringData(scoringResponse);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  // Use scoring data if available, otherwise use default
  const scores = scoringData?.scores || defaultScores;
  const radarData = scoringData?.radar_data || [];
  const files = scoringData?.files || [];
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
          {scores.map((score, index) => (
            <ScoreCard key={index} {...score} />
          ))}
        </div>

        {/* Radar Chart */}
        <div className="mb-8">
          <RadarChart data={radarData} />
        </div>

        {/* File List */}
        <FileList files={files} />

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
