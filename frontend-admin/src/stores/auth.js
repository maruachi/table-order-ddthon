// Admin auth store (U0 shell). U1 populates token on successful admin login.
import { defineStore } from 'pinia'
import { getToken, setToken, clearToken } from '../api/token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getToken(),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    login(token) {
      this.token = token
      setToken(token)
    },
    logout() {
      this.token = null
      clearToken()
    },
  },
})
