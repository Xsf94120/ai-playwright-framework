import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    proxy: {
      // Mirror Vercel's behaviour: strip the /api prefix before forwarding to
      // the FastAPI backend (which defines routes without the prefix).
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
