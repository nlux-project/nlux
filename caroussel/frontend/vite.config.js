import { defineConfig } from 'vite'

// Run from caroussel/frontend/:  npm run dev | npm run build
export default defineConfig({
  root: '.',
  publicDir: 'public',
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      // Carousel API -> carousel server (:8089)
      '/api': 'http://localhost:8089',
      // Image proxy passthrough -> nlux backend (:8000)
      '/iiif': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets',
  },
})