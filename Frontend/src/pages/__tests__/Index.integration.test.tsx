import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Index from '@/pages/Index'
import { apiService } from '@/lib/api'

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    createUser: vi.fn(),
    analyzeAndStoreRepository: vi.fn(),
    getRepositoryScoring: vi.fn(),
  }
}))

// Mock the components that might cause issues
vi.mock('@/components/OverallScore', () => ({
  OverallScore: vi.fn(({ score, repoName }) => (
    <div data-testid="overall-score">
      <div data-testid="score">{score}</div>
      <div data-testid="repo-name">{repoName}</div>
    </div>
  ))
}))

vi.mock('@/components/FileList', () => ({
  FileList: vi.fn(({ files }) => (
    <div data-testid="file-list">
      {files.map((file: any, index: number) => (
        <div key={index} data-testid={`file-${index}`}>{file.name}</div>
      ))}
    </div>
  ))
}))

describe('Score Breakdown Integration Tests', () => {
  const mockScoringData = {
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
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock implementations
    vi.mocked(apiService.createUser).mockResolvedValue({
      user: { id: 'test-user-id', email: 'test@example.com', name: 'Test User', github_username: 'test' },
      message: 'User created'
    })
    
    vi.mocked(apiService.analyzeAndStoreRepository).mockResolvedValue({
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
      }
    })
    
    vi.mocked(apiService.getRepositoryScoring).mockResolvedValue(mockScoringData)
  })

  it('shows loading state initially', () => {
    render(<Index />)
    
    expect(screen.getByText('Generating score breakdown...')).toBeInTheDocument()
    expect(screen.getByTestId('overall-score')).toBeInTheDocument()
  })

  it('displays score cards with default values initially', () => {
    render(<Index />)
    
    // Should show default scores (0)
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('Security')).toBeInTheDocument()
    expect(screen.getByText('Git Hygiene')).toBeInTheDocument()
  })

  it('shows radar chart with default data initially', () => {
    render(<Index />)
    
    expect(screen.getByText('Score Breakdown')).toBeInTheDocument()
    expect(screen.getByText('6 categories analyzed')).toBeInTheDocument()
  })

  it('handles successful repository analysis', async () => {
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    // Enter repository URL
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    
    // Click analyze button
    fireEvent.click(analyzeButton)
    
    // Should show loading state
    expect(screen.getByText('Analyzing...')).toBeInTheDocument()
    
    // Wait for analysis to complete
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument() // Quality score
      expect(screen.getByText('72')).toBeInTheDocument() // Security score
    }, { timeout: 3000 })
    
    // Should show radar chart with real data
    expect(screen.getByText('Score Breakdown')).toBeInTheDocument()
    expect(screen.getByText('85/100')).toBeInTheDocument() // Quality in legend
    expect(screen.getByText('72/100')).toBeInTheDocument() // Security in legend
  })

  it('shows analysis and recommendations after successful analysis', async () => {
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('Analysis')).toBeInTheDocument()
      expect(screen.getByText('Recommendations')).toBeInTheDocument()
      expect(screen.getByText('This repository shows strong code quality with excellent git practices.')).toBeInTheDocument()
      expect(screen.getByText('Add comprehensive type hints')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(apiService.analyzeAndStoreRepository).mockRejectedValue(new Error('API Error'))
    
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('validates repository URL input', async () => {
    render(<Index />)
    
    const analyzeButton = screen.getByText('Analyze Repository')
    
    // Try to analyze without URL
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a repository URL')).toBeInTheDocument()
    })
  })

  it('shows file list after successful analysis', async () => {
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('file-list')).toBeInTheDocument()
      expect(screen.getByTestId('file-0')).toBeInTheDocument()
      expect(screen.getByText('main.py')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('updates overall score after analysis', async () => {
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      const scoreElement = screen.getByTestId('score')
      expect(scoreElement).toHaveTextContent('80')
    }, { timeout: 3000 })
  })

  it('handles empty scoring data gracefully', async () => {
    vi.mocked(apiService.getRepositoryScoring).mockResolvedValue({
      scores: [],
      radar_data: [],
      files: [],
      analysis: '',
      recommendations: [],
      overall_score: 0,
      ai_percentage: 0,
    })
    
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    await waitFor(() => {
      // Should still show default data
      expect(screen.getByText('Score Breakdown')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('maintains responsive design', () => {
    render(<Index />)
    
    // Check that grid layouts are present
    const scoreGrid = screen.getByText('Quality').closest('.grid')
    expect(scoreGrid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
  })

  it('handles rapid successive analysis requests', async () => {
    render(<Index />)
    
    const repoInput = screen.getByPlaceholderText('Enter GitHub repository URL (e.g., https://github.com/owner/repo)')
    const analyzeButton = screen.getByText('Analyze Repository')
    
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo' } })
    fireEvent.click(analyzeButton)
    
    // Immediately start another analysis
    fireEvent.change(repoInput, { target: { value: 'https://github.com/test/repo2' } })
    fireEvent.click(analyzeButton)
    
    // Should handle gracefully without errors
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})

