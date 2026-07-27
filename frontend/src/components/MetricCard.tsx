import { useEffect, useState } from 'react'
import { deleteMetric, fetchMetricHistory, type Metric } from '../api'
import type { TimeRange } from './TimeRangeBar'
import { SparklineChart } from './SparklineChart'

interface Props {
  metric: Metric
  timeRange?: TimeRange
  colorIndex?: number
  onDelete: () => void
}

function formatValue(value: number): { display: string; unit: string } {
  if (value >= 1_000_000) return { display: (value / 1_000_000).toFixed(1), unit: 'M' }
  if (value >= 1_000) return { display: (value / 1_000).toFixed(1), unit: 'K' }
  if (Number.isInteger(value)) return { display: String(value), unit: '' }
  return { display: value.toFixed(1), unit: value > 0 && value < 100 ? '%' : '' }
}

export function MetricCard({ metric, timeRange, colorIndex = 0, onDelete }: Props) {
  const [historyData, setHistoryData] = useState<{ value: number }[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const loadHistory = async () => {
      try {
        const startISO = timeRange?.start ? new Date(timeRange.start).toISOString() : undefined
        const endISO = timeRange?.end ? new Date(timeRange.end).toISOString() : undefined
        const history = await fetchMetricHistory(metric.name, 20, startISO, endISO)
        if (!cancelled) {
          setHistoryData(history.map((m) => ({ value: m.value })))
        }
      } catch {
        if (!cancelled) {
          setHistoryData([])
        }
      } finally {
        if (!cancelled) {
          setHistoryLoading(false)
        }
      }
    }
    loadHistory()
    return () => {
      cancelled = true
    }
  }, [metric.name, timeRange])

  const handleDelete = async () => {
    try {
      await deleteMetric(metric.name)
      onDelete()
    } catch (err) {
      console.error('Failed to delete metric:', err)
    }
  }

  const { display, unit } = formatValue(metric.value)
  const isPercent = metric.name.includes('percent') || metric.name.includes('pct')

  return (
    <div className="metric-panel">
      <div className="panel-header">
        <span className="panel-title">{metric.name}</span>
        <div className="panel-actions">
          <button className="panel-action-btn" onClick={handleDelete} aria-label={`Delete ${metric.name}`}>
            ×
          </button>
        </div>
      </div>
      <div className="panel-body">
        <div className="panel-big-value">
          {display}
          <span className="unit">{isPercent ? '%' : unit}</span>
        </div>
        {!historyLoading && historyData.length > 0 && (
          <div className="panel-chart">
            <SparklineChart data={historyData} colorIndex={colorIndex} />
          </div>
        )}
      </div>
      <div className="panel-footer">
        <span>{new Date(metric.timestamp).toLocaleTimeString()}</span>
        {Object.entries(metric.tags).map(([k, v]) => (
          <span key={k} className="panel-tag">
            {k}:{v}
          </span>
        ))}
      </div>
    </div>
  )
}
