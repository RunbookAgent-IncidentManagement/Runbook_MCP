#!/usr/bin/env bash
# ==============================================================================
# Setup & Launch Script for E-Commerce RunBook System (AWS Free Tier Mode)
# ==============================================================================
set -e

echo "🚀 Starting Automated Setup for E-Commerce RunBook System..."

# 1. Setup 2GB Swap if not present
if [ $(free -m | awk '/^Swap:/{print $2}') -eq 0 ]; then
  echo "🔧 Configuring 2GB Swap memory to prevent OOM on t2.micro / t3.micro..."
  sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab || true
  echo "✅ Swap enabled."
else
  echo "✅ Swap memory already active."
fi

# 2. Check & Install K3s
if ! command -v k3s &> /dev/null; then
  echo "📦 Installing K3s lightweight Kubernetes..."
  curl -sfL https://get.k3s.io | sh -
fi

mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config 2>/dev/null || true
sudo chown $(id -u):$(id -g) ~/.kube/config 2>/dev/null || true
export KUBECONFIG=~/.kube/config

# 3. Start PostgreSQL and Redis via Docker Compose
echo "🐘 Starting PostgreSQL & Redis..."
docker-compose up -d postgres redis

# 4. Build and Import Container Images into K3s containerd
echo "🐳 Building microservice Docker images and importing into K3s containerd..."
for svc in product cart order payment notification auth; do
  echo "  --> Building ecommerce/${svc}-service:v1.0.0..."
  docker build -t ecommerce/${svc}-service:v1.0.0 backend/${svc}_service/ > /dev/null
  
  echo "  --> Importing ecommerce/${svc}-service:v1.0.0 into K3s..."
  docker save ecommerce/${svc}-service:v1.0.0 | sudo k3s ctr images import - > /dev/null
done
echo "✅ All images imported into K3s."

# 5. Apply Kubernetes Manifests
echo "☸️ Applying Kubernetes manifests to 'ecommerce' namespace..."
kubectl create namespace ecommerce 2>/dev/null || true

for dir in product cart order payment notification auth; do
  kubectl apply -f k8s/base/$dir/ --namespace=ecommerce
done

# 6. Apply Single-Node Free Tier Resource Adjustments
echo "⚙️ Configuring deployments for Single-Node Free Tier (1 Replica, 64Mi RAM request)..."
for deploy in cart-service order-service payment-service product-service notification-service auth-service; do
  kubectl scale deployment $deploy -n ecommerce --replicas=1 2>/dev/null || true
  kubectl set resources deployment $deploy -n ecommerce -c=api --requests=memory=64Mi,cpu=50m --limits=memory=256Mi,cpu=250m 2>/dev/null || true
  kubectl patch deployment $deploy -n ecommerce -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","imagePullPolicy":"Never"}]}}}}' 2>/dev/null || true
done

kubectl rollout restart deployment -n ecommerce

# 7. Start MCP Servers & Runbook Runner in Background
echo "🤖 Launching MCP Servers and Runbook Runner Service..."
pkill -f "kubernetes_mcp_server" || true
pkill -f "jira_mcp_server" || true
pkill -f "runbook-runner" || true

nohup python3 mcp-servers/kubernetes_mcp_server.py > /tmp/k8s_mcp.log 2>&1 &
nohup python3 mcp-servers/jira_mcp_server.py > /tmp/jira_mcp.log 2>&1 &
nohup python3 services/runbook-runner/app/main.py > /tmp/runbook_runner.log 2>&1 &

echo "✨ Setup Complete!"
echo "--------------------------------------------------------"
echo "🔍 Check Pod Status:    kubectl get pods -n ecommerce"
echo "🔍 Check Runner Health:  curl http://localhost:8000/health"
echo "💥 Test Incident:       python3 scripts/incidents/simulate_payment_crash.py"
echo "--------------------------------------------------------"
