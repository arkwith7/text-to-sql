import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  // 환경 변수 우선순위: process.env > .env 파일
  const apiTarget = process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL || 
    (mode === 'development' ? 'http://127.0.0.1:8000' : '/api');
    
  console.log(`🔧 Vite Config - Mode: ${mode}, API Target: ${apiTarget}`);
  console.log(`🔧 Process ENV: ${process.env.VITE_API_BASE_URL}`);
  console.log(`🔧 Loaded ENV: ${env.VITE_API_BASE_URL}`);
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(process.cwd(), './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      watch: {
        usePolling: true
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        }
      }
    }
  }
})
