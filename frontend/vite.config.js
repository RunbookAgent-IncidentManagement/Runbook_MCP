import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Docker Compose version: all services resolve by container name
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, host: '0.0.0.0', open: false, proxy: {
    '/api': { target: 'http://product-service:8000', changeOrigin: true },
    '/cart': { target: 'http://cart-service:8000', changeOrigin: true },
    '/orders': { target: 'http://order-service:8000', changeOrigin: true },
    '/payments': { target: 'http://payment-service:8000', changeOrigin: true },
    '/notifications': { target: 'http://notification-service:8000', changeOrigin: true },
    '/auth': { target: 'http://auth-service:8000', changeOrigin: true }
  }}
});
