// SSE helper (U4) for the customer app — mirrors frontend-admin api/sse.js.
// EventSource can't set headers, so the token is passed as a query param;
// the backend SSE endpoint (U4) validates it (customer token = 'to_customer_token').
import { getToken } from './token'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Open an SSE connection.
 * @param {string} path e.g. '/realtime/table/stream'
 * @param {(event: object) => void} onEvent parsed event payload handler
 * @returns {EventSource}
 */
export function openSse(path, onEvent) {
  const token = getToken()
  const url = `${BASE}${path}?token=${encodeURIComponent(token || '')}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data))
    } catch {
      /* ignore malformed frames */
    }
  }
  return es
}
