import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ScoreCard } from '@/components/ScoreCard'
import { Code } from 'lucide-react'

// Mock Progress component
vi.mock('@/components/ui/progress', () => ({
  Progress: vi.fn(({ value, className, style, ...props }) => (
    <div 
      data-testid="progress" 
      data-value={value}
      className={className}
      style={style}
      {...props}
    />
  ))
}))

describe('ScoreCard Component', () => {
  const mockProps = {
    title: 'Quality',
    score: 85,
    color: 'hsl(var(--quality))',
    icon: <Code className="h-6 w-6" />,
    description: 'Code maintainability & complexity'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with correct title and score', async () => {
    render(<ScoreCard {...mockProps} />)
    
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('Code maintainability & complexity')).toBeInTheDocument()
    
    // Score should animate from 0 to 85
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('renders without icon when not provided', () => {
    const propsWithoutIcon = { ...mockProps, icon: undefined }
    
    render(<ScoreCard {...propsWithoutIcon} />)
    
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('renders without description when not provided', () => {
    const propsWithoutDescription = { ...mockProps, description: undefined }
    
    render(<ScoreCard {...propsWithoutDescription} />)
    
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.queryByText('Code maintainability & complexity')).not.toBeInTheDocument()
  })

  it('animates score from 0 to target value', async () => {
    render(<ScoreCard {...mockProps} />)
    
    // Initially should show 0
    expect(screen.getByText('0')).toBeInTheDocument()
    
    // Should animate to target score
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('handles zero score correctly', async () => {
    const zeroScoreProps = { ...mockProps, score: 0 }
    render(<ScoreCard {...zeroScoreProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  it('handles maximum score correctly', async () => {
    const maxScoreProps = { ...mockProps, score: 100 }
    render(<ScoreCard {...maxScoreProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('applies correct CSS classes for animation', () => {
    const { container } = render(<ScoreCard {...mockProps} />)
    
    const card = container.querySelector('.transition-all')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('duration-300')
  })

  it('applies hover effects', () => {
    const { container } = render(<ScoreCard {...mockProps} />)
    
    const card = container.querySelector('.hover\\:shadow-lg')
    expect(card).toBeInTheDocument()
  })

  it('passes correct props to Progress component', async () => {
    render(<ScoreCard {...mockProps} />)
    
    const progress = screen.getByTestId('progress')
    expect(progress).toBeInTheDocument()
    
    // Wait for animation to complete
    await waitFor(() => {
      expect(progress).toHaveAttribute('data-value', '85')
    }, { timeout: 1000 })
  })

  it('handles score changes correctly', async () => {
    const { rerender } = render(<ScoreCard {...mockProps} />)
    
    // Wait for initial animation
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
    }, { timeout: 1000 })
    
    // Change score
    rerender(<ScoreCard {...mockProps} score={95} />)
    
    // Should animate to new score
    await waitFor(() => {
      expect(screen.getByText('95')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('rounds score values correctly', async () => {
    const decimalScoreProps = { ...mockProps, score: 85.7 }
    render(<ScoreCard {...decimalScoreProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('86')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('handles negative scores gracefully', async () => {
    const negativeScoreProps = { ...mockProps, score: -10 }
    render(<ScoreCard {...negativeScoreProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('handles very large scores correctly', async () => {
    const largeScoreProps = { ...mockProps, score: 150 }
    render(<ScoreCard {...largeScoreProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('maintains accessibility with proper structure', () => {
    render(<ScoreCard {...mockProps} />)
    
    // Check that title is properly structured
    const title = screen.getByText('Quality')
    expect(title).toBeInTheDocument()
    expect(title.tagName).toBe('H3')
  })

  it('applies correct color styling', () => {
    render(<ScoreCard {...mockProps} />)
    
    const scoreElement = screen.getByText('85')
    expect(scoreElement).toHaveStyle({ color: 'hsl(var(--quality))' })
  })

  it('handles rapid score changes', async () => {
    const { rerender } = render(<ScoreCard {...mockProps} />)
    
    // Rapidly change scores
    rerender(<ScoreCard {...mockProps} score={50} />)
    rerender(<ScoreCard {...mockProps} score={75} />)
    rerender(<ScoreCard {...mockProps} score={90} />)
    
    // Should eventually show the final score
    await waitFor(() => {
      expect(screen.getByText('90')).toBeInTheDocument()
    }, { timeout: 1000 })
  })
})
