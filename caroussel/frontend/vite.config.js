import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  root: 'frontend',
  publicDir: 'frontend/public',
  resolve: {
    alias: {
      '@': './frontend/src'
    }
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'frontend/dist',
    emptyOutDir: true,
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        index: 'frontend/index.html'
      }
    }
  }
})
