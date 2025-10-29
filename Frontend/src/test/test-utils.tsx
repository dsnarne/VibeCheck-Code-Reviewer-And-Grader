import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

// Custom render function that includes any providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { ...options })

// Test data factories
export const createMockScoringData = (overrides = {}) => ({
  scores: [
    { title: "Quality", score: 85, color: "hsl(var(--quality))", icon: null, description: "Code maintainability & complexity" },
    { title: "Security", score: 72, color: "hsl(var(--security))", icon: null, description: "Vulnerabilities & best practices" },
    { title: "Git Hygiene", score: 90, color: "hsl(var(--git))", icon: null, description: "Commit quality & PR practices" },
    { title: "Style", score: 78, color: "hsl(var(--style))", icon: null, description: "Consistency & conventions" },
    { title: "Originality", score: 65, color: "hsl(var(--originality))", icon: null, description: "Unique implementations" },
    { title: "Team Balance", score: 88, color: "hsl(var(--team))", icon: null, description: "Contribution distribution" },
  ],
  radar_data: [
    { category: "Quality", score: 85, fullMark: 100 },
    { category: "Security", score: 72, fullMark: 100 },
    { category: "Git", score: 90, fullMark: 100 },
    { category: "Style", score: 78, fullMark: 100 },
    { category: "Originality", score: 65, fullMark: 100 },
    { category: "Team", score: 88, fullMark: 100 },
  ],
  files: [
    { name: "main.py", path: "src/main.py", score: 92, issues: ["Excellent code quality"] },
    { name: "utils.py", path: "src/utils.py", score: 85, issues: ["Good structure"] },
  ],
  analysis: "This repository shows strong code quality with excellent git practices.",
  recommendations: ["Add comprehensive type hints", "Implement security scanning"],
  overall_score: 80,
  ai_percentage: 15,
  previous_score: 75,
  ...overrides
})

export const createMockAnalysisData = (overrides = {}) => ({
  repo_id: 'test-repo-id',
  repo: 'test-repo',
  error: undefined,
  warning: undefined,
  stored_in_db: true,
  files_stored: true,
  file_count: 10,
  file_storage: {
    base_path: '/test/path',
    file_count: 10,
    files_ready_for_embedding: true,
    skipped_files: [],
    skipped_count: 0
  },
  languages: { Python: 1000, JavaScript: 500 },
  team: {
    giniContribution: 0.3,
    topContributorsShare: 0.7,
    contributions: [{ author: 'user1', netLines: 1000 }],
    perAuthorLanguage: []
  },
  commits: {
    count: 50,
    medianCompartmentalization: 0.8,
    meanCompartmentalization: 0.75
  },
  ...overrides
})

// Wait for animations to complete
export const waitForAnimation = async (timeout = 1000) => {
  await new Promise(resolve => setTimeout(resolve, timeout))
}

// Helper to simulate user interactions
export const simulateRepositoryAnalysis = async (screen: any, repoUrl = 'https://github.com/test/repo') => {
  const { fireEvent } = await import('@testing-library/react')
  const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
  const analyzeButton = screen.getByText('Analyze Repository')
  
  fireEvent.change(repoInput, { target: { value: repoUrl } })
  fireEvent.click(analyzeButton)
  
  return { repoInput, analyzeButton }
}

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }
