// U4 Session API (admin). Uses U0 client.js (token injection + 401 handling).
// Contract: GET /sessions/dashboard, POST /sessions/close, GET /sessions/history.
import client from './client'

/**
 * Real-time dashboard snapshot (US-A2). Returns active-session table cards.
 * @param {number} previewN latest orders to preview per table (default 3)
 * @returns {Promise<object>} dashboard payload (table cards)
 */
export function getDashboard(previewN = 3) {
  return client
    .get('/sessions/dashboard', { params: { preview_n: previewN } })
    .then((r) => r.data)
}

/**
 * Close the active session for a table (US-A6).
 * @param {number} tableId
 * @returns {Promise<object>} ClosedSessionSummary
 */
export function closeSession(tableId) {
  return client.post('/sessions/close', { table_id: tableId }).then((r) => r.data)
}

/**
 * Past session history, ordered by closed_at desc (US-A7).
 * @param {{table_id?: number, date_from?: string, date_to?: string, offset: number, limit: number}} params
 * @returns {Promise<object>} Page of history orders
 */
export function getHistory(params) {
  return client.get('/sessions/history', { params }).then((r) => r.data)
}
