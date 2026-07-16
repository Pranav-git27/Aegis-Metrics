// File Location: frontend/src/api.js
// Centralized API client for the Aegis Metrics backend.
// Backend runs locally on http://localhost:8000 (FastAPI).

export const API_BASE_URL = 'http://localhost:8000'

/**
 * Fetch aggregated dashboard overview metrics.
 * GET /api/v1/analytics/overview
 * @returns {Promise<{total_logs:number,total_alerts:number,anomaly_rate_percentage:number,critical_alerts_count:number}>}
 */
export async function fetchOverview() {
  const res = await fetch(`${API_BASE_URL}/api/v1/analytics/overview`, {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    throw new Error(`Overview request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

/**
 * Fetch all active (unresolved) security alerts, sorted by anomaly score desc.
 * GET /api/v1/alerts/active
 * @returns {Promise<Array<{alert_id:string,log_id:string,anomaly_score:number,risk_level:string,is_resolved:boolean}>>}
 */
export async function fetchActiveAlerts() {
  const res = await fetch(`${API_BASE_URL}/api/v1/alerts/active`, {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    throw new Error(`Active alerts request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

/**
 * Mark a single alert as resolved.
 * PUT /api/v1/alerts/{alert_id}/resolve
 * @param {string} alertId
 * @returns {Promise<object>} confirmation payload from the backend
 */
export async function resolveAlert(alertId) {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/alerts/${encodeURIComponent(alertId)}/resolve`,
    {
      method: 'PUT',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    },
  )
  if (!res.ok) {
    throw new Error(`Resolve request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}
