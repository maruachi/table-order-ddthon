import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Customer SPA dev server on 5173 (matches backend CORS config).
export default defineConfig({
  plugins: [vue()],
  server: { port: 5173 },
})
