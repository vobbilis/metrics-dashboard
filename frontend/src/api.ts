const BASE = '/api'

export type AlertOperator = 'gt' | 'lt' | 'eq'
export type AlertState = 'ok' | 'firing'

export interface AlertRule {
  id: string
  metric_name: string
  operator: AlertOperator
  threshold: number
  state: AlertState
  created_at: string
}

export interface AlertRuleIn {
  metric_name: string
  operator: AlertOperator
  threshold: number
}

export interface AlertRuleUpdate {
  metric_name?: string
  operator?: AlertOperator
  threshold?: number
}

export interface AlertEvent {
  rule_id: string
  metric_name: string
  old_state: AlertState
  new_state: AlertState
  timestamp: string
}

export interface Metric {
  id: string
  name: string
  value: number
  tags: Record<string, string>
  timestamp: string
}

export interface MetricIn {
  name: string
  value: number
  tags?: Record<string, string>
}

export async function fetchMetrics(tags?: string[], start?: string, end?: string): Promise<Metric[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) {
    for (const t of tags) {
      params.append('tag', t)
    }
  }
  if (start) params.append('start', start)
  if (end) params.append('end', end)
  const qs = params.toString()
  const url = qs ? `${BASE}/metrics?${qs}` : `${BASE}/metrics`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`)
  return res.json()
}

export async function submitMetric(metric: MetricIn): Promise<Metric> {
  const res = await fetch(`${BASE}/metrics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric),
  })
  if (!res.ok) throw new Error(`Failed to submit metric: ${res.status}`)
  return res.json()
}

export async function deleteMetric(name: string): Promise<{ deleted: number }> {
  const res = await fetch(`${BASE}/metrics/${name}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete metric: ${res.status}`)
  return res.json()
}

export async function fetchAlerts(): Promise<AlertRule[]> {
  const res = await fetch(`${BASE}/alerts`)
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`)
  return res.json()
}

export async function fetchMetricHistory(
  name: string,
  limit: number = 20,
  start?: string,
  end?: string,
): Promise<Metric[]> {
  const params = new URLSearchParams()
  params.append('limit', String(limit))
  if (start) params.append('start', start)
  if (end) params.append('end', end)
  const res = await fetch(`${BASE}/metrics/${name}/history?${params.toString()}`)
  if (!res.ok) throw new Error(`Failed to fetch metric history: ${res.status}`)
  return res.json()
}

export async function createAlert(rule: AlertRuleIn): Promise<AlertRule> {
  const res = await fetch(`${BASE}/alerts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  })
  if (!res.ok || res.status !== 201)
    throw new Error(`Failed to create alert: ${res.status}`)
  return res.json()
}

export async function deleteAlert(ruleId: string): Promise<{ deleted: number }> {
  const res = await fetch(`${BASE}/alerts/${ruleId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete alert: ${res.status}`)
  return res.json()
}

export async function updateAlert(ruleId: string, update: AlertRuleUpdate): Promise<AlertRule> {
  const res = await fetch(`${BASE}/alerts/${ruleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
  if (!res.ok) throw new Error(`Failed to update alert: ${res.status}`)
  return res.json()
}

export async function fetchAlertEvents(): Promise<AlertEvent[]> {
  const res = await fetch(`${BASE}/alerts/events`)
  if (!res.ok) throw new Error(`Failed to fetch alert events: ${res.status}`)
  return res.json()
}
