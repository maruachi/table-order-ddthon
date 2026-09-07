// SSE helper (U0 shell) for the admin dashboard (U4 consumes this).
// EventSource can't set headers, so the token is passed as a query param;
// the backend SSE endpoint (U4) validates it.
import { getToken } from './token'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Open an SSE connection.
 * @param {string} path e.g. '/realtime/admin/stream'
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
