import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchMetricHistory } from './api'

// Mock fetch globally
const mockFetch = vi.fn() as any
vi.stubGlobal('fetch', mockFetch)

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchMetricHistory', () => {
    it('should fetch metric history with default limit', async () => {
      const mockMetrics = [
        {
          id: '1',
          name: 'cpu',
          value: 42.5,
          tags: { host: 'server1' },
          timestamp: '2026-02-28T10:00:00Z',
        },
        {
          id: '2',
          name: 'cpu',
          value: 45.2,
          tags: { host: 'server1' },
          timestamp: '2026-02-28T10:01:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMetrics),
      })

      const result = await fetchMetricHistory('cpu')

      expect(mockFetch).toHaveBeenCalledWith('/api/metrics/cpu/history?limit=20')
      expect(result).toEqual(mockMetrics)
    })

    it('should fetch metric history with custom limit', async () => {
      const mockMetrics = [
        {
          id: '1',
          name: 'memory',
          value: 80.5,
          tags: { host: 'server2' },
          timestamp: '2026-02-28T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMetrics),
      })

      const result = await fetchMetricHistory('memory', 5)

      expect(mockFetch).toHaveBeenCalledWith('/api/metrics/memory/history?limit=5')
      expect(result).toEqual(mockMetrics)
    })

    it('should throw error when response is not ok', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      })

      await expect(fetchMetricHistory('nonexistent')).rejects.toThrow(
        'Failed to fetch metric history: 404'
      )
    })
  })
})