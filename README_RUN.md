RUNNING WITH DOCKER DESKTOP (REQUIRED FOR FULL STACK)
======================================================
1. Use Docker service-name proxy (for frontend inside Docker network):
   cp frontend/vite.config.docker.js frontend/vite.config.js

2. Build and start everything (postgres provides DB for all backends):
   docker-compose down -v
   docker-compose up --build

3. Wait for all services to report healthy:
   - product-service:8000  (needs postgres healthcheck first)
   - cart-service:8000
   - order-service:8000
   - payment-service:8000
   - notification-service:8000
   - auth-service:8000
   - frontend:3000

4. Open browser:
   http://localhost:3000

ERROR EXPLANATIONS:
- 500 on /api/products  -> Product service can't reach postgres (run docker-compose)
- 404 on /cart/demo-user -> Proxy points to wrong target or service not running
- 500 on /auth/login     -> Auth service needs DATABASE_URL env (provided by compose)

The "AWS config" (vite.config.docker.js) uses Docker service names:
  /api -> product-service:8000
  /cart -> cart-service:8000
  /orders -> order-service:8000
  /auth -> auth-service:8000
