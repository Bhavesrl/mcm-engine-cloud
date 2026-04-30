import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // mode 'flask'  → build per Flask, servito su /explorer/
  // mode default  → build per Vercel, servito su /
  base: mode === 'flask' ? '/explorer/' : '/',
}))
