#!/usr/bin/env bash
# ==============================================================================
# Helper Script to Launch FastMCP Native Web & SSE Testing Servers
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export KUBECONFIG=~/.kube/config
export K8S_NAMESPACE="ecommerce"

echo "🎨 Launching FastMCP Web/SSE Servers..."
echo "--------------------------------------------------------"
echo "🌐 Kubernetes FastMCP Server: http://<YOUR_EC2_PUBLIC_IP>:8001"
echo "🌐 Jira FastMCP Server:       http://<YOUR_EC2_PUBLIC_IP>:8002"
echo "--------------------------------------------------------"

pkill -f "kubernetes_mcp_server.py --sse" || true
pkill -f "jira_mcp_server.py --sse" || true

PORT=8001 python3 mcp-servers/kubernetes_mcp_server.py --sse &
PORT=8002 python3 mcp-servers/jira_mcp_server.py --sse &

sleep 2
echo "✅ FastMCP Native Web/SSE Servers active on ports 8001 and 8002!"
