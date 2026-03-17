import { useState } from 'react'
import {
  createAlert,
  deleteAlert,
  updateAlert,
  type AlertEvent,
  type AlertOperator,
  type AlertRule,
  type AlertRuleIn,
  type AlertRuleUpdate,
} from '../api'

interface Props {
  alerts: AlertRule[]
  events: AlertEvent[]
  onAlertChange: () => void
}

const opSymbol = (op: string) => (op === 'gt' ? '>' : op === 'lt' ? '<' : '=')

export function AlertPanel({ alerts, events, onAlertChange }: Props) {
  const [metricName, setMetricName] = useState('')
  const [operator, setOperator] = useState<AlertOperator>('gt')
  const [threshold, setThreshold] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const resetForm = () => {
    setMetricName('')
    setOperator('gt')
    setThreshold('')
    setEditingId(null)
    setError(null)
  }

  const handleEdit = (alert: AlertRule) => {
    setMetricName(alert.metric_name)
    setOperator(alert.operator)
    setThreshold(String(alert.threshold))
    setEditingId(alert.id)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!metricName.trim() || !threshold.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      if (editingId) {
        const update: AlertRuleUpdate = {
          metric_name: metricName.trim(),
          operator,
          threshold: parseFloat(threshold),
        }
        await updateAlert(editingId, update)
      } else {
        const rule: AlertRuleIn = {
          metric_name: metricName.trim(),
          operator,
          threshold: parseFloat(threshold),
        }
        await createAlert(rule)
      }
      resetForm()
      onAlertChange()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (ruleId: string) => {
    try {
      await deleteAlert(ruleId)
      onAlertChange()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  return (
    <div className="alerts-section">
      <div className="section-title">Alerts</div>

      <form onSubmit={handleSubmit} className="alert-form">
        <input
          data-testid="alert-metric-input"
          type="text"
          placeholder="metric name"
          value={metricName}
          onChange={(e) => setMetricName(e.target.value)}
          required
        />
        <select
          data-testid="alert-operator-select"
          value={operator}
          onChange={(e) => setOperator(e.target.value as AlertOperator)}
        >
          <option value="gt">&gt;</option>
          <option value="lt">&lt;</option>
          <option value="eq">=</option>
        </select>
        <input
          data-testid="alert-threshold-input"
          type="number"
          placeholder="threshold"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          step="any"
          required
        />
        <button data-testid="alert-submit-btn" type="submit" disabled={submitting}>
          {editingId ? 'Update Alert' : 'Create Alert'}
        </button>
        {editingId && (
          <button data-testid="alert-cancel-btn" type="button" onClick={resetForm}>
            Cancel
          </button>
        )}
        {error && <span className="alert-form-error">{error}</span>}
      </form>

      {alerts.length === 0 ? (
        <p className="empty-state" style={{ padding: '1rem' }}>No alerts configured.</p>
      ) : (
        <div className="alert-list-container">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-row ${alert.state === 'firing' ? 'alert-row--firing' : 'alert-row--ok'}`}
            >
              <span className="alert-metric">{alert.metric_name}</span>
              <span className="alert-condition">
                {opSymbol(alert.operator)} {alert.threshold}
              </span>
              <span
                className={`alert-badge ${alert.state === 'firing' ? 'alert-badge--firing' : 'alert-badge--ok'}`}
              >
                {alert.state}
              </span>
              <div className="alert-actions">
                <button data-testid={`edit-alert-${alert.id}`} type="button" onClick={() => handleEdit(alert)}>
                  Edit
                </button>
                <button
                  data-testid={`delete-alert-${alert.id}`}
                  type="button"
                  className="alert-delete-btn"
                  onClick={() => handleDelete(alert.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {events.length > 0 && (
        <div className="alert-history">
          <div className="section-title">History</div>
          <div className="alert-timeline">
            {[...events].reverse().map((event, i) => (
              <div
                key={i}
                className={`alert-timeline-item ${event.new_state === 'firing' ? 'alert-timeline-item--firing' : 'alert-timeline-item--ok'}`}
              >
                <span className="alert-timeline-time">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
                <span className="alert-timeline-metric">{event.metric_name}</span>
                <span className="alert-timeline-transition">
                  {event.old_state} &rarr; {event.new_state}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
