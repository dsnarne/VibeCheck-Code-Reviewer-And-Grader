import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Code, Shield, GitBranch, Palette, Lightbulb, Users } from "lucide-react";
import { ScoreCard } from "@/components/ScoreCard";
import { RadarChart } from "@/components/RadarChart";
import { FileList } from "@/components/FileList";
import { OverallScore } from "@/components/OverallScore";

const Index = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data
  const repoName = "awesome-project";
  const overallScore = 87;
  const aiPercentage = 23;
  const previousScore = 82;

  const scores = [
    { title: "Quality", score: 92, color: "hsl(var(--quality))", icon: <Code className="h-6 w-6" />, description: "Code maintainability & complexity" },
    { title: "Security", score: 88, color: "hsl(var(--security))", icon: <Shield className="h-6 w-6" />, description: "Vulnerabilities & best practices" },
    { title: "Git Hygiene", score: 85, color: "hsl(var(--git))", icon: <GitBranch className="h-6 w-6" />, description: "Commit quality & PR practices" },
    { title: "Style", score: 90, color: "hsl(var(--style))", icon: <Palette className="h-6 w-6" />, description: "Consistency & conventions" },
    { title: "Originality", score: 78, color: "hsl(var(--originality))", icon: <Lightbulb className="h-6 w-6" />, description: "Unique implementations" },
    { title: "Team Balance", score: 89, color: "hsl(var(--team))", icon: <Users className="h-6 w-6" />, description: "Contribution distribution" },
  ];

  const radarData = [
    { category: "Quality", score: 92, fullMark: 100 },
    { category: "Security", score: 88, fullMark: 100 },
    { category: "Git", score: 85, fullMark: 100 },
    { category: "Style", score: 90, fullMark: 100 },
    { category: "Originality", score: 78, fullMark: 100 },
    { category: "Team", score: 89, fullMark: 100 },
  ];

  const files = [
    {
      name: "auth.service.ts",
      path: "src/services/auth.service.ts",
      aiPercentage: 85,
      quality: 72,
      flags: ["High AI%", "Security Review"],
    },
    {
      name: "user.controller.ts",
      path: "src/controllers/user.controller.ts",
      aiPercentage: 45,
      quality: 88,
      flags: ["Good Quality"],
    },
    {
      name: "database.config.ts",
      path: "src/config/database.config.ts",
      aiPercentage: 92,
      quality: 65,
      flags: ["High AI%", "Vibe-Coded"],
    },
    {
      name: "utils.ts",
      path: "src/utils/utils.ts",
      aiPercentage: 15,
      quality: 95,
      flags: ["Excellent"],
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
            VibeCheck
          </h1>
          <p className="text-muted-foreground">Repository Analysis & AI Detection</p>
        </header>

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
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Analyze New Repo
          </Button>
        </div>

        {/* Overall Score */}
        <div className="mb-8">
          <OverallScore
            score={overallScore}
            aiPercentage={aiPercentage}
            previousScore={previousScore}
            repoName={repoName}
          />
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
      </div>
    </div>
  );
};

export default Index;
