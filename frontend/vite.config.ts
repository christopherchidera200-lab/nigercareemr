import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react:    ['react', 'react-dom', 'react-router-dom'],
          aws:      ['aws-amplify', '@aws-amplify/auth'],
          charts:   ['recharts'],
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target:       process.env.VITE_API_URL || 'http://localhost:4000',
        changeOrigin: true,
        rewrite:      (path) => path.replace(/^\/api/, ''),
      }
    }
  }
})
