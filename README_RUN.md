# 🚀 AuraCommerce Agentic RunBook System — Run & Testing Guide

> **Architecture**: FastAPI Webhook Service + LangGraph State Machine Agent + FastMCP Stdio Tools (Kubernetes & Jira) + K3s Cluster + Docker Hub Images (`secretpower/*-rba:v1`).

---

## 🏃 Quick Command Cheat Sheet

### 1. Launch Complete Environment (One-Command Setup)
On your **AWS EC2 Terminal**:

```bash
cd /home/ubuntu/Runbook_MCP
git pull origin main

chmod +x scripts/setup_free_tier.sh scripts/stop_free_tier.sh
./scripts/setup_free_tier.sh
```

---

### 2. Verify Pipeline Health (5-Second Smoke Test)
```bash
python3 scripts/test_agent_pipeline.py
```

---

## 🧪 Testing the LangGraph Runbook Agent & Remediation Workflows

### 🌟 TEST SCENARIO 1: Autonomous Remediation (Self-Healing)
**Goal**: Verify that the LangGraph Agent classifies a `CrashLoopBackOff` alert, loads `RB-001`, invokes `kubernetes.rollout_restart` via FastMCP over stdio, and verifies `1/1 Ready` recovery.

```bash
# 1. Ensure healthy deployment is applied
kubectl apply -f k8s/demo/payment-service-v1-healthy.yaml -n ecommerce
sleep 5

# 2. Trigger incident alert to FastAPI Agent Runner
python3 scripts/incidents/simulate_payment_crash.py
```

**Expected Outcome**:
- `status`: `"completed"`
- `runbook_id`: `"RB-001"`
- `recovery_confirmed`: `true`
- `escalation_required`: `false`

---

### ⚡ TEST SCENARIO 2: Multi-Attempt Retry, Fallback Runbook & Jira Escalation
**Goal**: Deploy a broken release (`v2.0.0-broken`). Verify that the LangGraph Agent attempts `RB-001` restart twice, transitions to fallback runbook `RB-002` (Rollback Deployment), verifies failure, and creates Jira ticket `INC-101`.

```bash
# 1. Deploy broken container release to K3s
kubectl apply -f k8s/demo/payment-service-v2-broken.yaml -n ecommerce
sleep 5

# 2. Trigger incident alert
python3 scripts/incidents/simulate_payment_crash.py

# 3. Restore healthy payment container release
kubectl apply -f k8s/demo/payment-service-v1-healthy.yaml -n ecommerce
```

**Expected Outcome**:
- `status`: `"escalated"`
- `attempts`: `2`
- `recovery_confirmed`: `false`
- `escalation_required`: `true`
- `jira_ticket`: `{"ticket_key": "INC-101", "status": 201}`

---

### 🔬 TEST SCENARIO 3: Dry-Run Mode & Unhealthy Simulation (Offline / Non-K8s Test)
**Goal**: Test full state machine retries, fallback transitions (`RB-001` → `RB-002`), and Jira ticket creation in offline dry-run mode without modifying K3s.

```bash
export K8S_DRY_RUN="true"
export FORCE_UNHEALTHY="true"

python3 scripts/incidents/simulate_payment_crash.py
```

---

## 🌐 Public IP Web Endpoints

Replace `<YOUR_EC2_PUBLIC_IP>` with your EC2 Public IP address:

1. **E-Commerce Frontend Web App**: `http://<YOUR_EC2_PUBLIC_IP>/` or `http://<YOUR_EC2_PUBLIC_IP>:30000/`
2. **FastMCP Interactive Web Inspector Console**: `http://<YOUR_EC2_PUBLIC_IP>:8000/mcp-ui`
3. **FastAPI Agent OpenAPI Documentation**: `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`
4. **Agent Health Status**: `http://<YOUR_EC2_PUBLIC_IP>:8000/health`

---

## 🛑 Stopping the Environment

To stop background runner processes and scale down resources when closing for the day:

```bash
./scripts/stop_free_tier.sh
```
