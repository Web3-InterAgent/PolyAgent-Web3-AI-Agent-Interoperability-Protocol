import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,      // 前端使用3000端口，避免与后端5000端口冲突
    host: '0.0.0.0', // 允许外部访问（云服务器必须）
    proxy: {
      // 代理所有API请求到后端Flask服务器
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/youxuan-shopping': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/market-trade': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/config': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/agents': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})