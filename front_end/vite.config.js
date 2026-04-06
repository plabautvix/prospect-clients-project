import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api/backend': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/backend/, '')
      },
      '/api/whatsapp': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/whatsapp/, '/api/whatsapp')
      },
      '/api/send': {
        target: 'http://localhost:3001',
        changeOrigin: true
      },
      '/api/sent': {
        target: 'http://localhost:3001',
        changeOrigin: true
      }
    }
  }
})
