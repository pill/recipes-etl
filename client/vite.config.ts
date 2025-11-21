import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// bypass CORS
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy semantic search to API server (handles embedding generation)
      '/api/recipes/_search': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy other Elasticsearch requests directly
      '/api/recipes': {
        target: 'http://localhost:9200',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/recipes/, '/recipes')
      }
    }
  }
})
