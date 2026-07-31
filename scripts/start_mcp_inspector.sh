#!/usr/bin/env bash
# ==============================================================================
# Helper Script to Launch Official MCP Interactive Web Inspector UI
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export KUBECONFIG=~/.kube/config
export K8S_NAMESPACE="ecommerce"

echo "🎨 Launching Official MCP Interactive Web Inspector UI..."
echo "--------------------------------------------------------"

if ! command -v npx &> /dev/null; then
  echo "📦 Installing Node.js & npx..."
  sudo apt update -y && sudo apt install -y nodejs npm 2>/dev/null || true
fi

echo "🚀 Starting @modelcontextprotocol/inspector on http://0.0.0.0:5173..."
HOST=0.0.0.0 CLIENT_HOST=0.0.0.0 npx -y @modelcontextprotocol/inspector --host 0.0.0.0 --port 5173 python3 mcp-servers/kubernetes_mcp_server.py
