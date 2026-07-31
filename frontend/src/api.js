// File Location: frontend/src/api.js
// Centralized API client for the Aegis Metrics backend.
// Backend runs locally on http://localhost:8000 (FastAPI).

export const API_BASE_URL = 'http://localhost:8000'

/**
 * Fetch aggregated dashboard overview metrics.
 * GET /api/v1/analytics/overview
 * @returns {Promise<{total_logs:number,total_alerts:number,anomaly_rate_percentage:number,quarantined_devices:number}>}
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
