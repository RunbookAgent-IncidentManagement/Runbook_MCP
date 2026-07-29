#!/usr/bin/env bash
# ==============================================================================
# Stop & Cleanup Script for E-Commerce RunBook System (AWS Free Tier Mode)
# ==============================================================================

echo "🛑 Stopping E-Commerce RunBook System..."

# 1. Kill background Python agent & MCP processes
echo "🧹 Stopping Python agent processes (MCP & Runbook Runner)..."
pkill -f "kubernetes_mcp_server" || true
pkill -f "jira_mcp_server" || true
pkill -f "runbook-runner" || true

# 2. Stop Docker Compose PostgreSQL & Redis
echo "🐘 Stopping Docker containers (PostgreSQL & Redis)..."
docker-compose down || true

# 3. Scale down Kubernetes deployments (frees memory/CPU)
echo "☸️ Scaling down Kubernetes deployments to 0..."
kubectl scale deployment --all -n ecommerce --replicas=0 2>/dev/null || true

echo "✅ Environment Stopped Successfully! You can now turn off your EC2 instance."
