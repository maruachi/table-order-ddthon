// Table session token storage (U0 shell) — localStorage, survives refresh (NFR-5).
const KEY = 'to_customer_token'

export function getToken() {
  return localStorage.getItem(KEY)
}

export function setToken(token) {
  localStorage.setItem(KEY, token)
}

export function clearToken() {
  localStorage.removeItem(KEY)
}
