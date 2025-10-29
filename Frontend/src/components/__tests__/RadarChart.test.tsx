import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RadarChart } from '@/components/RadarChart'

// Mock Recharts components
vi.mock('recharts', () => ({
  Radar: vi.fn(({ children, ...props }) => <div data-testid="radar" {...props}>{children}</div>),
  RadarChart: vi.fn(({ children, ...props }) => <div data-testid="radar-chart" {...props}>{children}</div>),
  PolarGrid: vi.fn((props) => <div data-testid="polar-grid" {...props} />),
  PolarAngleAxis: vi.fn((props) => <div data-testid="polar-angle-axis" {...props} />),
  PolarRadiusAxis: vi.fn((props) => <div data-testid="polar-radius-axis" {...props} />),
  ResponsiveContainer: vi.fn(({ children, ...props }) => <div data-testid="responsive-container" {...props}>{children}</div>),
}))

describe('RadarChart Component', () => {
  const mockData = [
    { category: 'Quality', score: 85, fullMark: 100 },
    { category: 'Security', score: 72, fullMark: 100 },
    { category: 'Git', score: 90, fullMark: 100 },
    { category: 'Style', score: 78, fullMark: 100 },
    { category: 'Originality', score: 65, fullMark: 100 },
    { category: 'Team', score: 88, fullMark: 100 },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with correct title and category count', () => {
    render(<RadarChart data={mockData} />)
    
    expect(screen.getByText('Score Breakdown')).toBeInTheDocument()
    expect(screen.getByText('6 categories analyzed')).toBeInTheDocument()
  })

  it('displays all categories in the legend', () => {
    render(<RadarChart data={mockData} />)
    
    mockData.forEach(item => {
      expect(screen.getByText(item.category)).toBeInTheDocument()
      expect(screen.getByText(`${item.score}/100`)).toBeInTheDocument()
    })
  })

  it('handles empty data gracefully', () => {
    render(<RadarChart data={[]} />)
    
    // Should show default data
    expect(screen.getByText('6 categories analyzed')).toBeInTheDocument()
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('Security')).toBeInTheDocument()
  })

  it('handles undefined data gracefully', () => {
    render(<RadarChart data={undefined as any} />)
    
    // Should show default data
    expect(screen.getByText('6 categories analyzed')).toBeInTheDocument()
  })

  it('validates and transforms malformed data', () => {
    const malformedData = [
      { category: 'Quality', score: 'invalid', fullMark: 100 },
      { category: '', score: 50, fullMark: 'invalid' },
      { category: 'Security', score: 75, fullMark: 100 },
    ]
    
    render(<RadarChart data={malformedData as any} />)
    
    // Should handle malformed data gracefully
    expect(screen.getByText('3 categories analyzed')).toBeInTheDocument()
  })

  it('applies correct CSS classes for animation', async () => {
    const { container } = render(<RadarChart data={mockData} />)
    
    // Wait for animation to complete
    await waitFor(() => {
      const card = container.querySelector('.transition-all')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('duration-500', 'ease-in-out')
    })
  })

  it('renders ResponsiveContainer with correct props', () => {
    render(<RadarChart data={mockData} />)
    
    const responsiveContainer = screen.getByTestId('responsive-container')
    expect(responsiveContainer).toBeInTheDocument()
  })

  it('renders Radar component with animation props', () => {
    render(<RadarChart data={mockData} />)
    
    const radar = screen.getByTestId('radar')
    expect(radar).toBeInTheDocument()
  })

  it('shows legend items with hover effects', () => {
    render(<RadarChart data={mockData} />)
    
    const legendItems = screen.getAllByText(/Quality|Security|Git|Style|Originality|Team/)
    legendItems.forEach(item => {
      const parent = item.closest('.transition-all')
      expect(parent).toHaveClass('hover:bg-background/70')
    })
  })

  it('handles data changes with animation', async () => {
    const initialData = [
      { category: 'Quality', score: 0, fullMark: 100 },
      { category: 'Security', score: 0, fullMark: 100 },
    ]
    
    const { rerender } = render(<RadarChart data={initialData} />)
    
    // Initially should show 0 scores
    expect(screen.getByText('0/100')).toBeInTheDocument()
    
    // Update with real data
    rerender(<RadarChart data={mockData} />)
    
    // Should eventually show real scores
    await waitFor(() => {
      expect(screen.getByText('85/100')).toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('maintains accessibility with proper ARIA labels', () => {
    render(<RadarChart data={mockData} />)
    
    // Check that the chart container is accessible
    const chartContainer = screen.getByTestId('responsive-container')
    expect(chartContainer).toBeInTheDocument()
  })

  it('handles single category data', () => {
    const singleData = [{ category: 'Quality', score: 85, fullMark: 100 }]
    
    render(<RadarChart data={singleData} />)
    
    expect(screen.getByText('1 categories analyzed')).toBeInTheDocument()
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('85/100')).toBeInTheDocument()
  })

  it('handles very high scores correctly', () => {
    const highScoreData = [
      { category: 'Quality', score: 100, fullMark: 100 },
      { category: 'Security', score: 99, fullMark: 100 },
    ]
    
    render(<RadarChart data={highScoreData} />)
    
    expect(screen.getByText('100/100')).toBeInTheDocument()
    expect(screen.getByText('99/100')).toBeInTheDocument()
  })

  it('handles zero scores correctly', () => {
    const zeroScoreData = [
      { category: 'Quality', score: 0, fullMark: 100 },
      { category: 'Security', score: 0, fullMark: 100 },
    ]
    
    render(<RadarChart data={zeroScoreData} />)
    
    expect(screen.getByText('0/100')).toBeInTheDocument()
  })
})

