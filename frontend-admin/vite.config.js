import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Admin SPA dev server on 5174 (matches backend CORS config).
export default defineConfig({
  plugins: [vue()],
  server: { port: 5174 },
})
