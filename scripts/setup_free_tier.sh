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

# Purge stale ReplicaSets from previous runs
kubectl delete rs --all -n ecommerce 2>/dev/null || true

# Scale up postgres and redis first (in case stop script scaled them down)
kubectl scale deployment postgres -n ecommerce --replicas=1 2>/dev/null || true
kubectl scale deployment redis -n ecommerce --replicas=1 2>/dev/null || true

# Apply base manifests (only directories that exist)
for dir in postgres redis shared frontend product cart order payment notification auth; do
  if [ -d "${PROJECT_ROOT}/k8s/base/$dir/" ]; then
    kubectl apply -f "${PROJECT_ROOT}/k8s/base/$dir/" --namespace=ecommerce 2>/dev/null || true
  fi
done

# Apply Public Access Ingress & NodePort manifests
if [ -f "${PROJECT_ROOT}/k8s/ingress/public-access.yaml" ]; then
  kubectl apply -f "${PROJECT_ROOT}/k8s/ingress/public-access.yaml" --namespace=ecommerce 2>/dev/null || true
fi

# 5. Set Docker Hub Images (secretpower/*-rba:v1) & Single-Node Resource Optimization
echo "🐳 Setting container images to secretpower/*-rba:v1 from Docker Hub..."
for deploy in cart-service order-service payment-service product-service notification-service auth-service; do
  # Only patch deployments that exist
  if kubectl get deployment "$deploy" -n ecommerce &>/dev/null; then
    svc_short=$(echo $deploy | sed 's/-service//')
    image_tag="secretpower/${svc_short}-rba:v1"
    
    echo "  --> Setting deployment/$deploy image to $image_tag..."
    kubectl set image deployment/$deploy api=$image_tag -n ecommerce 2>/dev/null || true
    kubectl scale deployment $deploy -n ecommerce --replicas=1 2>/dev/null || true
    kubectl set resources deployment $deploy -n ecommerce -c=api --requests=memory=64Mi,cpu=50m --limits=memory=256Mi,cpu=250m 2>/dev/null || true
    kubectl patch deployment $deploy -n ecommerce -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","imagePullPolicy":"IfNotPresent"}]}}}}' 2>/dev/null || true
  fi
done

# Delete stale ReplicaSets from old deployments to clean up old image tags
kubectl delete rs -n ecommerce $(kubectl get rs -n ecommerce -o jsonpath='{range .items[?(@.spec.replicas==0)]}{.metadata.name}{" "}{end}') 2>/dev/null || true
kubectl rollout restart deployment -n ecommerce 2>/dev/null || true

# 6. Verify Python Agent Dependencies (visible output so failures are not silently swallowed)
echo "📦 Installing/verifying Agentic Python dependencies..."
sudo apt update -y && sudo apt install -y python3-pip 2>/dev/null || true
echo "   Installing from requirements.txt..."
pip3 install -r "${PROJECT_ROOT}/requirements.txt" --break-system-packages || pip3 install -r "${PROJECT_ROOT}/requirements.txt" || {
  echo "⚠️ WARNING: pip install failed. Some features (MCP, LangGraph, LLM) may use fallback mode."
}

# 7. Load environment variables from .env file and set defaults
echo "🔑 Loading environment variables..."
if [ -f "${PROJECT_ROOT}/.env" ]; then
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
  echo "   ✅ Loaded .env file"
else
  echo "   ⚠️ No .env file found at ${PROJECT_ROOT}/.env — using defaults (mock mode for Jira/LLM)"
fi

export KUBECONFIG=~/.kube/config
export K8S_NAMESPACE="${K8S_NAMESPACE:-ecommerce}"
export K8S_DRY_RUN="${K8S_DRY_RUN:-false}"
export HUGGINGFACE_API_URL="${HUGGINGFACE_API_URL:-https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2}"
# HUGGINGFACE_TOKEN, JIRA_TOKEN, JIRA_URL, JIRA_EMAIL loaded from .env if present

# 8. Start FastAPI Runner Service (stdio MCP servers are dynamically managed by MCPToolClient subprocess sessions)
echo "🤖 Launching FastAPI Runner Service..."
pkill -f "main.py" || true
pkill -f "uvicorn" || true

nohup python3 "${PROJECT_ROOT}/services/runbook-runner/app/main.py" > /tmp/runbook_runner.log 2>&1 &

# Wait for cold start (langgraph + MCP imports can take 5-8s)
echo "   Waiting for FastAPI cold start (8 seconds)..."
sleep 8

# Verify FastAPI Health with retry
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI Agent Runner Service is HEALTHY on http://localhost:8000"
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "⚠️ FastAPI Runner may still be starting. Check logs:"
    tail -n 15 /tmp/runbook_runner.log 2>/dev/null || true
  else
    echo "   Retry $i/$MAX_RETRIES..."
    sleep 3
  fi
done

echo ""
echo "✨ Setup Complete!"
echo "--------------------------------------------------------"
echo "🔍 Check Pod Status:    kubectl get pods -n ecommerce"
echo "🔍 Check Runner Health:  curl http://localhost:8000/health"
echo "💥 Test Incident:       python3 scripts/incidents/simulate_payment_crash.py"
echo "🧪 Smoke Test:          python3 scripts/test_agent_pipeline.py"
echo "--------------------------------------------------------"
