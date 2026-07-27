import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { TimeRangeBar } from './TimeRangeBar'

describe('TimeRangeBar', () => {
  it('renders start and end inputs', () => {
    render(<TimeRangeBar timeRange={{ start: '', end: '' }} onTimeRangeChange={() => {}} />)
    expect(screen.getByTestId('time-range-start')).toBeInTheDocument()
    expect(screen.getByTestId('time-range-end')).toBeInTheDocument()
  })

  it('does not show clear button when empty', () => {
    render(<TimeRangeBar timeRange={{ start: '', end: '' }} onTimeRangeChange={() => {}} />)
    expect(screen.queryByTestId('time-range-clear')).not.toBeInTheDocument()
  })

  it('shows clear button when start has value', () => {
    render(
      <TimeRangeBar timeRange={{ start: '2026-03-15T14:00', end: '' }} onTimeRangeChange={() => {}} />,
    )
    expect(screen.getByTestId('time-range-clear')).toBeInTheDocument()
  })

  it('calls onTimeRangeChange on start input change', () => {
    const onChange = vi.fn()
    render(<TimeRangeBar timeRange={{ start: '', end: '' }} onTimeRangeChange={onChange} />)
    fireEvent.change(screen.getByTestId('time-range-start'), {
      target: { value: '2026-03-15T14:00' },
    })
    expect(onChange).toHaveBeenCalledWith({ start: '2026-03-15T14:00', end: '' })
  })

  it('calls onTimeRangeChange with empty values on clear', () => {
    const onChange = vi.fn()
    render(
      <TimeRangeBar timeRange={{ start: '2026-03-15T14:00', end: '2026-03-16T14:00' }} onTimeRangeChange={onChange} />,
    )
    fireEvent.click(screen.getByTestId('time-range-clear'))
    expect(onChange).toHaveBeenCalledWith({ start: '', end: '' })
  })
})
