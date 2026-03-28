import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api/auth':      { target: 'http://localhost:8082', changeOrigin: true },
      '/api/inventory': { target: 'http://localhost:8081', changeOrigin: true },
      '/api/pos':       { target: 'http://localhost:8080', changeOrigin: true },
    }
  }
})
