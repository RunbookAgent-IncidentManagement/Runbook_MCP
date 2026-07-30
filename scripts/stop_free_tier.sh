#!/usr/bin/env bash
# ==============================================================================
# Stop & Cleanup Script for E-Commerce RunBook Agent System (AWS Free Tier Mode)
# ==============================================================================

# Change directory to project root (one level up from script location using absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🛑 Stopping E-Commerce RunBook Agent System..."

# 1. Kill background Python FastMCP servers & FastAPI runner processes
echo "🧹 Stopping Python agent processes (FastMCP stdio & FastAPI Runner)..."
pkill -f "kubernetes_mcp_server" || true
pkill -f "jira_mcp_server" || true
pkill -f "services/runbook-runner" || true
pkill -f "uvicorn" || true

# 2. Stop Docker Compose PostgreSQL & Redis
echo "🐘 Stopping Docker containers (PostgreSQL & Redis)..."
if command -v docker-compose &> /dev/null; then
  docker-compose down || true
elif docker compose version &> /dev/null 2>&1; then
  docker compose down || true
fi

# 3. Scale down Kubernetes deployments to 0 (frees CPU and memory)
echo "☸️ Scaling down Kubernetes deployments to 0 in 'ecommerce' namespace..."
kubectl scale deployment --all -n ecommerce --replicas=0 2>/dev/null || true

echo "✅ Environment Stopped Successfully! You can now turn off your EC2 instance."
