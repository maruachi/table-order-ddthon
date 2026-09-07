// Admin JWT storage (U0 shell) — localStorage, survives refresh (US-A1, NFR-5).
const KEY = 'to_admin_token'

export function getToken() {
  return localStorage.getItem(KEY)
}

export function setToken(token) {
  localStorage.setItem(KEY, token)
}

export function clearToken() {
  localStorage.removeItem(KEY)
}
