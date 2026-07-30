#!/usr/bin/env bash
# ==============================================================================
# Helper Script to Launch the Interactive FastMCP Developer Inspector Dashboard
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export KUBECONFIG=~/.kube/config
export K8S_NAMESPACE="ecommerce"

echo "🎨 Launching FastMCP Interactive Web Inspector..."
echo "--------------------------------------------------------"
echo "🌐 Inspector URL: http://<YOUR_EC2_PUBLIC_IP>:5173"
echo "--------------------------------------------------------"

if ! command -v npx &> /dev/null; then
  echo "📦 Installing Node.js & npx for FastMCP Inspector..."
  sudo apt update -y && sudo apt install -y nodejs npm 2>/dev/null || true
fi

# Launch official FastMCP Dev Inspector
npx -y @modelcontextprotocol/inspector python3 mcp-servers/kubernetes_mcp_server.py
