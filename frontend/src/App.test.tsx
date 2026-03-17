import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import App from './App'
import * as api from './api'

vi.mock('./api')

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.fetchMetrics).mockResolvedValue([])
    vi.mocked(api.fetchAlerts).mockResolvedValue([])
    vi.mocked(api.fetchMetricHistory).mockResolvedValue([])
    vi.mocked(api.fetchAlertEvents).mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the dashboard heading', async () => {
    render(<App />)
    expect(screen.getByText('Metrics Dashboard')).toBeInTheDocument()
  })

  it('shows empty state when no metrics', async () => {
    render(<App />)
    expect(
      await screen.findByText('No metrics yet. Submit one above or wait for host metrics.')
    ).toBeInTheDocument()
  })

  it('renders metrics when returned from API', async () => {
    vi.mocked(api.fetchMetrics).mockResolvedValue([
      {
        id: '1',
        name: 'cpu',
        value: 42.5,
        tags: {},
        timestamp: new Date().toISOString(),
      },
    ])
    render(<App />)
    expect(await screen.findByText('cpu')).toBeInTheDocument()
  })

  it('renders alerts when returned from API', async () => {
    vi.mocked(api.fetchAlerts).mockResolvedValue([
      {
        id: 'alert-1',
        metric_name: 'cpu',
        operator: 'gt',
        threshold: 80,
        state: 'firing',
        created_at: new Date().toISOString(),
      },
    ])
    render(<App />)
    expect(await screen.findByText('cpu')).toBeInTheDocument()
    expect(await screen.findByText('> 80')).toBeInTheDocument()
    expect(await screen.findByText('firing')).toBeInTheDocument()
  })

  it('shows empty alerts section when no alerts', async () => {
    render(<App />)
    expect(await screen.findByText('No alerts configured.')).toBeInTheDocument()
  })

  describe('Alert Integration Tests', () => {
    it('polls metrics, alerts, and alert events synchronously', async () => {
      vi.useFakeTimers()

      render(<App />)

      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(1)
      expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(1)
      expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(1)

      await vi.advanceTimersByTimeAsync(5000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(2)
      expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(2)
      expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(2)

      await vi.advanceTimersByTimeAsync(5000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(3)
      expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(3)
      expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(3)
    })

    it('handles alert fetch errors gracefully', async () => {
      vi.mocked(api.fetchAlerts).mockRejectedValue(
        new Error('Alert service down')
      )
      vi.mocked(api.fetchMetrics).mockResolvedValue([
        {
          id: '1',
          name: 'cpu',
          value: 42.5,
          tags: {},
          timestamp: new Date().toISOString(),
        },
      ])

      render(<App />)

      expect(await screen.findByText('cpu')).toBeInTheDocument()
      expect(
        await screen.findByText('No alerts configured.')
      ).toBeInTheDocument()
    })

    it('shows firing alert state', async () => {
      vi.mocked(api.fetchAlerts).mockResolvedValue([
        {
          id: 'alert-firing',
          metric_name: 'memory',
          operator: 'gt',
          threshold: 90,
          state: 'firing',
          created_at: new Date().toISOString(),
        },
      ])

      render(<App />)

      expect(await screen.findByText('memory')).toBeInTheDocument()
      expect(await screen.findByText('> 90')).toBeInTheDocument()
      expect(await screen.findByText('firing')).toBeInTheDocument()
    })
  })

  describe('Tag Filtering', () => {
    it('renders the tag filter input and button', async () => {
      render(<App />)
      expect(
        await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      ).toBeInTheDocument()
      expect(screen.getByText('Add Filter')).toBeInTheDocument()
    })

    it('shows validation error when tag has no colon', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'invalid')
      await user.click(screen.getByText('Add Filter'))

      expect(
        await screen.findByText('Tag must contain a colon (e.g. env:prod)')
      ).toBeInTheDocument()
    })

    it('adds a valid tag chip and passes it to fetchMetrics', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'env:prod')
      await user.click(screen.getByText('Add Filter'))

      expect(await screen.findByText('env:prod')).toBeInTheDocument()
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledWith(['env:prod'], undefined, undefined)
    })

    it('removes a tag chip when clicking remove button', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'env:prod')
      await user.click(screen.getByText('Add Filter'))

      expect(await screen.findByText('env:prod')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Remove env:prod'))

      expect(vi.mocked(api.fetchMetrics)).toHaveBeenLastCalledWith([], undefined, undefined)
    })
  })

  describe('BUG-003: Polling interval must not reset on filter change', () => {
    it('does not reset polling interval when activeTags changes', async () => {
      vi.useFakeTimers()
      render(<App />)

      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(1)

      await vi.advanceTimersByTimeAsync(4000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(1)

      const input = screen.getByPlaceholderText('Filter by tag (e.g. env:prod)')
      fireEvent.change(input, { target: { value: 'env:prod' } })
      fireEvent.click(screen.getByText('Add Filter'))

      await vi.advanceTimersByTimeAsync(0)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(2)

      await vi.advanceTimersByTimeAsync(1000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(3)
    })

    it('polling continues on schedule after removing a tag filter', async () => {
      vi.useFakeTimers()
      render(<App />)

      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(1)

      const input = screen.getByPlaceholderText('Filter by tag (e.g. env:prod)')
      fireEvent.change(input, { target: { value: 'env:prod' } })
      fireEvent.click(screen.getByText('Add Filter'))
      await vi.advanceTimersByTimeAsync(0)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(2)

      await vi.advanceTimersByTimeAsync(5000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(3)

      fireEvent.click(screen.getByLabelText('Remove env:prod'))
      await vi.advanceTimersByTimeAsync(0)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(4)

      await vi.advanceTimersByTimeAsync(5000)
      expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(5)
    })
  })

  it('renders Export CSV link with correct attributes', async () => {
    render(<App />)

    const exportLink = await screen.findByText('Export CSV')
    expect(exportLink).toBeInTheDocument()
    expect(exportLink).toHaveAttribute('href', '/api/metrics/export?format=csv')
    expect(exportLink).toHaveClass('export-btn')
    expect(exportLink).toHaveAttribute('download', 'metrics.csv')
  })

  describe('BUG-005: Export CSV includes active tag filters', () => {
    it('export link includes tag params when tags are active', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'env:prod')
      await user.click(screen.getByText('Add Filter'))

      const exportLink = await screen.findByText('Export CSV')
      expect(exportLink).toHaveAttribute(
        'href',
        '/api/metrics/export?format=csv&tag=env%3Aprod'
      )
    })

    it('export link has no tag params when no tags active', async () => {
      render(<App />)

      const exportLink = await screen.findByText('Export CSV')
      expect(exportLink).toHaveAttribute('href', '/api/metrics/export?format=csv')
    })

    it('export link includes multiple tag params', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'env:prod')
      await user.click(screen.getByText('Add Filter'))

      await user.type(input, 'region:us')
      await user.click(screen.getByText('Add Filter'))

      const exportLink = await screen.findByText('Export CSV')
      const href = exportLink.getAttribute('href')!
      expect(href).toContain('format=csv')
      expect(href).toContain('tag=env%3Aprod')
      expect(href).toContain('tag=region%3Aus')
    })

    it('export link reverts to base URL when all tags removed', async () => {
      const user = userEvent.setup()
      render(<App />)

      const input = await screen.findByPlaceholderText('Filter by tag (e.g. env:prod)')
      await user.type(input, 'env:prod')
      await user.click(screen.getByText('Add Filter'))

      let exportLink = await screen.findByText('Export CSV')
      expect(exportLink.getAttribute('href')).toContain('tag=')

      await user.click(screen.getByLabelText('Remove env:prod'))

      exportLink = screen.getByText('Export CSV')
      expect(exportLink).toHaveAttribute('href', '/api/metrics/export?format=csv')
    })
  })

  describe('AlertPanel Integration', () => {
    it('renders alert create form', async () => {
      render(<App />)
      expect(await screen.findByTestId('alert-metric-input')).toBeInTheDocument()
      expect(screen.getByTestId('alert-operator-select')).toBeInTheDocument()
      expect(screen.getByTestId('alert-threshold-input')).toBeInTheDocument()
      expect(screen.getByTestId('alert-submit-btn')).toBeInTheDocument()
    })

    it('renders alert history when events exist', async () => {
      vi.mocked(api.fetchAlertEvents).mockResolvedValue([
        {
          rule_id: 'r1',
          metric_name: 'cpu',
          old_state: 'ok',
          new_state: 'firing',
          timestamp: new Date().toISOString(),
        },
      ])
      render(<App />)
      expect(await screen.findByText('History')).toBeInTheDocument()
      expect(await screen.findByText('cpu')).toBeInTheDocument()
    })

    it('does not render history section when no events', async () => {
      render(<App />)
      await screen.findByTestId('alert-metric-input')
      expect(screen.queryByText('History')).not.toBeInTheDocument()
    })

    it('handles fetchAlertEvents error gracefully', async () => {
      vi.mocked(api.fetchAlertEvents).mockRejectedValue(
        new Error('Events service down')
      )
      render(<App />)
      expect(await screen.findByTestId('alert-metric-input')).toBeInTheDocument()
      expect(screen.queryByText('History')).not.toBeInTheDocument()
    })
  })
})
