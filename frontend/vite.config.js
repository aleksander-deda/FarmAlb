import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Ensures imports are case-insensitive on Windows
    preserveSymlinks: true,
  },
  server: {
    port: 5173,
  },
})