import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': { target: proxyTarget },
      '/health': { target: proxyTarget },
      '/metrics': { target: proxyTarget },
      '/ws': { target: proxyTarget, ws: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
  },
})
