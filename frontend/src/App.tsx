import { useEffect, useRef, useState } from 'react'
import { fetchAlerts, fetchAlertEvents, fetchMetrics, type AlertEvent, type AlertRule, type Metric } from './api'
import { AlertPanel } from './components/AlertPanel'
import { MetricCard } from './components/MetricCard'
import { MetricForm } from './components/MetricForm'
import { TagFilterBar } from './components/TagFilterBar'
import { TimeRangeBar, type TimeRange } from './components/TimeRangeBar'
import './dashboard.css'

const POLL_INTERVAL_MS = 5000

export default function App() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [alerts, setAlerts] = useState<AlertRule[]>([])
  const [alertEvents, setAlertEvents] = useState<AlertEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTags, setActiveTags] = useState<string[]>([])
  const activeTagsRef = useRef(activeTags)
  activeTagsRef.current = activeTags
  const [timeRange, setTimeRange] = useState<TimeRange>({ start: '', end: '' })
  const timeRangeRef = useRef(timeRange)
  timeRangeRef.current = timeRange

  const toISOParam = (val: string): string | undefined =>
    val ? new Date(val).toISOString() : undefined

  const loadMetrics = async () => {
    try {
      const tr = timeRangeRef.current
      const data = await fetchMetrics(
        activeTagsRef.current,
        toISOParam(tr.start),
        toISOParam(tr.end),
      )
      setMetrics(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const loadAlerts = async () => {
    try {
      const data = await fetchAlerts()
      setAlerts(data)
    } catch (e) {
      console.error('Failed to load alerts:', e)
    }
  }

  const loadAlertEvents = async () => {
    try {
      const data = await fetchAlertEvents()
      setAlertEvents(data)
    } catch (e) {
      console.error('Failed to load alert events:', e)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([loadMetrics(), loadAlerts(), loadAlertEvents()])
    }
    loadData()
    const timer = setInterval(loadData, POLL_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [])

  const isInitialMount = useRef(true)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }
    loadMetrics()
  }, [activeTags, timeRange])

  const csvHref = (() => {
    let url = '/api/metrics/export?format=csv'
    url += activeTags.map(t => `&tag=${encodeURIComponent(t)}`).join('')
    if (timeRange.start) url += `&start=${encodeURIComponent(new Date(timeRange.start).toISOString())}`
    if (timeRange.end) url += `&end=${encodeURIComponent(new Date(timeRange.end).toISOString())}`
    return url
  })()

  const handleAlertChange = () => {
    loadAlerts()
    loadAlertEvents()
  }

  return (
    <>
      <div className="dashboard-header">
        <h1>Metrics Dashboard</h1>
        <div className="header-spacer" />
        <div className="poll-badge">
          <span className="poll-dot" />
          Live &middot; {POLL_INTERVAL_MS / 1000}s
        </div>
        <a href={csvHref} className="export-btn" download="metrics.csv">
          Export CSV
        </a>
      </div>

      <div className="dashboard-toolbar">
        <MetricForm onSubmit={loadMetrics} />
        <TagFilterBar tags={activeTags} onTagsChange={setActiveTags} />
        <TimeRangeBar timeRange={timeRange} onTimeRangeChange={setTimeRange} />
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {loading && <p className="empty-state">Loading...</p>}

      {!loading && metrics.length === 0 && (
        <p className="empty-state">No metrics yet. Submit one above or wait for host metrics.</p>
      )}

      <div className="panel-grid">
        {metrics.map((m, i) => (
          <MetricCard
            key={m.name}
            metric={m}
            timeRange={timeRange}
            colorIndex={i}
            onDelete={() => setMetrics(prev => prev.filter(m2 => m2.name !== m.name))}
          />
        ))}
      </div>

      <AlertPanel alerts={alerts} events={alertEvents} onAlertChange={handleAlertChange} />
    </>
  )
}
