#!/usr/bin/env bash
# ==============================================================================
# Setup & Launch Script for E-Commerce RunBook Agent System (AWS Free Tier Mode)
# Uses Docker Hub images (secretpower/*-rba:v1), FastMCP stdio servers,
# Mistral LLM classifier, and LangGraph Agentic Runner Service.
# ==============================================================================
set -e

# Dynamically calculate absolute project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🚀 Starting Automated Setup for E-Commerce RunBook Agent System..."
echo "📂 Project Root: ${PROJECT_ROOT}"

# 1. Setup 2GB Swap Memory (Prevents OOM on t3.small)
if [ $(free -m | awk '/^Swap:/{print $2}') -eq 0 ]; then
  echo "🔧 Configuring 2GB Swap memory to prevent OOM..."
  sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab || true
  echo "✅ Swap enabled."
else
  echo "✅ Swap memory already active."
fi

# 2. Check & Install K3s Kubernetes
if ! command -v k3s &> /dev/null; then
  echo "📦 Installing K3s lightweight Kubernetes..."
  curl -sfL https://get.k3s.io | sh -
fi

mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config 2>/dev/null || true
sudo chown $(id -u):$(id -g) ~/.kube/config 2>/dev/null || true
export KUBECONFIG=~/.kube/config

# 3. Detect / Install Docker Compose and Start PostgreSQL & Redis
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
  COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
else
  echo "📦 Installing docker-compose..."
  sudo apt update -y && sudo apt install -y docker-compose 2>/dev/null || sudo apt install -y docker-compose-v2 2>/dev/null || true
  if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
  elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  fi
fi

if [ -n "$COMPOSE_CMD" ]; then
  echo "🐘 Starting PostgreSQL & Redis via $COMPOSE_CMD..."
  $COMPOSE_CMD up -d postgres redis || true
else
  echo "⚠️ Docker Compose unavailable; skipping compose databases."
fi

# 4. Apply Kubernetes Base Manifests & Delete Stale Deployments
echo "☸️ Applying Kubernetes manifests (secretpower/*-rba:v1) to 'ecommerce' namespace..."
kubectl create namespace ecommerce 2>/dev/null || true

# Purge stale deployments/ReplicaSets from previous runs
kubectl delete rs --all -n ecommerce 2>/dev/null || true

# Apply base manifests (database + shared code + microservices)
for dir in postgres redis shared product cart order payment notification auth; do
  kubectl apply -f "${PROJECT_ROOT}/k8s/base/$dir/" --namespace=ecommerce 2>/dev/null || true
done

# Apply Public Access Ingress & NodePort manifests
kubectl apply -f "${PROJECT_ROOT}/k8s/ingress/public-access.yaml" --namespace=ecommerce 2>/dev/null || true

# 5. Set Docker Hub Images (secretpower/*-rba:v1) & Single-Node Resource Optimization
echo "🐳 Setting container images to secretpower/*-rba:v1 from Docker Hub..."
for deploy in cart-service order-service payment-service product-service notification-service auth-service; do
  svc_short=$(echo $deploy | sed 's/-service//')
  image_tag="secretpower/${svc_short}-rba:v1"
  
  echo "  --> Setting deployment/$deploy image to $image_tag..."
  kubectl set image deployment/$deploy api=$image_tag -n ecommerce 2>/dev/null || true
  kubectl scale deployment $deploy -n ecommerce --replicas=1 2>/dev/null || true
  kubectl set resources deployment $deploy -n ecommerce -c=api --requests=memory=64Mi,cpu=50m --limits=memory=256Mi,cpu=250m 2>/dev/null || true
  kubectl patch deployment $deploy -n ecommerce -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","imagePullPolicy":"IfNotPresent"}]}}}}' 2>/dev/null || true
done

# Delete stale ReplicaSets from old deployments to clean up old image tags
kubectl delete rs -n ecommerce $(kubectl get rs -n ecommerce -o jsonpath='{range .items[?(@.spec.replicas==0)]}{.metadata.name}{" "}{end}') 2>/dev/null || true
kubectl rollout restart deployment -n ecommerce 2>/dev/null || true

# 6. Verify Python Agent Dependencies
echo "📦 Installing/verifying Agentic Python dependencies (FastAPI, uvicorn, pydantic)..."
python3 -m pip install fastapi uvicorn pydantic requests pyyaml mcp langgraph --break-system-packages 2>/dev/null || \
pip3 install fastapi uvicorn pydantic requests pyyaml 2>/dev/null || true

# 7. Set Environment Variables for FastMCP & LLM Classification
export KUBECONFIG=~/.kube/config
export K8S_NAMESPACE="ecommerce"
export K8S_DRY_RUN="${K8S_DRY_RUN:-false}"
export HUGGINGFACE_API_URL="${HUGGINGFACE_API_URL:-https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2}"

# 8. Start FastMCP stdio Servers & FastAPI Runner Service
echo "🤖 Launching FastMCP stdio Servers and FastAPI Runner Service..."
pkill -f "kubernetes_mcp_server" || true
pkill -f "jira_mcp_server" || true
pkill -f "services/runbook-runner" || true
pkill -f "uvicorn" || true

nohup python3 "${PROJECT_ROOT}/mcp-servers/kubernetes_mcp_server.py" > /tmp/k8s_mcp.log 2>&1 &
nohup python3 "${PROJECT_ROOT}/mcp-servers/jira_mcp_server.py" > /tmp/jira_mcp.log 2>&1 &
nohup python3 "${PROJECT_ROOT}/services/runbook-runner/app/main.py" > /tmp/runbook_runner.log 2>&1 &

sleep 3

# Verify FastAPI Health
if curl -s http://localhost:8000/health > /dev/null; then
  echo "✅ FastAPI Agent Runner Service is HEALTHY on http://localhost:8000"
else
  echo "⚠️ FastAPI Runner starting... Logs (/tmp/runbook_runner.log):"
  tail -n 10 /tmp/runbook_runner.log 2>/dev/null || true
fi

echo ""
echo "✨ Setup Complete!"
echo "--------------------------------------------------------"
echo "🔍 Check Pod Status:    kubectl get pods -n ecommerce"
echo "🔍 Check Runner Health:  curl http://localhost:8000/health"
echo "💥 Test Incident:       python3 scripts/incidents/simulate_payment_crash.py"
echo "🧪 Smoke Test:          python3 scripts/test_agent_pipeline.py"
echo "--------------------------------------------------------"
