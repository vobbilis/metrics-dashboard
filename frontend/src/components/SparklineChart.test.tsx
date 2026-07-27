import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { SparklineChart } from './SparklineChart'

// Mock recharts since jsdom has no layout engine — ResponsiveContainer
// renders with 0 width/height, causing Recharts to render nothing.
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <svg data-testid="area-chart">{children}</svg>
  ),
  Area: () => <path data-testid="area" />,
  YAxis: () => null,
}))

describe('SparklineChart', () => {
  it('renders nothing when data is empty', () => {
    const { container } = render(<SparklineChart data={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders a chart when given multiple data points', () => {
    const data = [{ value: 10 }, { value: 20 }, { value: 30 }]
    const { container } = render(<SparklineChart data={data} />)
    expect(container.querySelector('[data-testid="area-chart"]')).not.toBeNull()
  })

  it('renders a chart when given a single data point (flat line)', () => {
    const data = [{ value: 42 }]
    const { container } = render(<SparklineChart data={data} />)
    expect(container.querySelector('[data-testid="area-chart"]')).not.toBeNull()
  })

  it('accepts custom height', () => {
    const data = [{ value: 10 }, { value: 20 }]
    const { container } = render(<SparklineChart data={data} height={40} />)
    expect(container.querySelector('[data-testid="area-chart"]')).not.toBeNull()
  })
})
