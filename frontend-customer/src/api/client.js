// Axios client (U0 shell): injects bearer token, handles 401 -> setup/login.
import axios from 'axios'
import { getToken, clearToken } from './token'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearToken()
      // Redirect to setup screen (owned by U1). Router guard also enforces this.
      if (window.location.pathname !== '/setup') window.location.assign('/setup')
    }
    return Promise.reject(error)
  },
)

export default client
