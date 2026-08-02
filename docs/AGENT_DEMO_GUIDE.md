# 🚀 AuraCommerce LangGraph Agentic Workflow — AWS Free Tier Guide

> **Core Objective**: Comprehensive guide for testing **Autonomous LangGraph Agentic Workflows** (LLM Alert Classification → Declarative Catalog Resolution → FastMCP Stdio Tools → K3s Pod Health Verification → Retry Loop → Fallback Runbook Transition → Jira Escalation) on an AWS Free Tier EC2 instance using **Docker Hub container images (`secretpower/*-rba:v1`)**.

---

## 📐 LangGraph Agentic Architecture

```
                       [ K3s Pod Crash Alert / Webhook ]
                                      │
                                      ▼ (HTTP POST /execute)
                        ┌───────────────────────────┐
                        │  FastAPI Runner Service   │
                        │  (http://...:8000/mcp-ui) │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENTIC STATE MACHINE                      │
│                                                                         │
│  1. classify_alert ──────► 2. load_runbook ──────► 3. execute_remediation│
│     (Mistral 7B / HF)        (YAML Catalog)           (FastMCP Stdio)   │
│                                                               │         │
│                                                               ▼         │
│  6. escalate_to_jira ◄───── 5. retry_or_escalate ◄── 4. verify_recovery │
│     (Jira Ticket INC-101)   (Attempts <= 2 /           (get_pod_status) │
│                              Fallback RB-002)                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ Quick Start Checklist

| Step | Action | Command / Location | Time |
|---|---|---|---|
| **1. Provision** | Launch EC2 `t3.small` (Ubuntu 22.04) | AWS Console | 1 min |
| **2. Security Group** | Allow Ports `80`, `8000`, `30000-32767` | AWS Security Group | 1 min |
| **3. Setup** | Run One-Click Launch Script | `./scripts/setup_free_tier.sh` | 1 min |
| **4. Smoke Test** | Verify Pipeline Components | `python3 scripts/test_agent_pipeline.py` | 10 sec |
| **5. Live Demo** | Trigger LangGraph Remediation | `python3 scripts/incidents/simulate_payment_crash.py` | 30 sec |

---

## 🧪 Detailed Step-by-Step Testing Guide

### 🌟 SCENARIO 1: Autonomous Remediation (Self-Healing Success)

**Story**: `payment-service` experiences a `CrashLoopBackOff` alert. The LangGraph Agent classifies the error, loads `RB-001` (Restart Deployment), calls the `kubernetes.rollout_restart` FastMCP tool over stdio, waits 5 seconds for pod probes, and verifies recovery (`healthy: true`).

#### Execution Commands (EC2 Terminal):

```bash
cd /home/ubuntu/Runbook_MCP
git pull origin main

# 1. Ensure healthy deployment is active
kubectl apply -f k8s/demo/payment-service-v1-healthy.yaml -n ecommerce
sleep 5

# 2. Trigger incident alert
python3 scripts/incidents/simulate_payment_crash.py
```

#### What Happens Under the Hood:
1. **Webhook Ingestion**: Alert payload received at `http://localhost:8000/execute`.
2. **Mistral LLM Classification**: Analyzes log trace (`OutOfMemoryError`) → Maps to `RB-001` (`POD_FAILURE`).
3. **FastMCP Execution**: Calls `kubernetes_mcp_server.rollout_restart(deployment="payment-service")`.
4. **Empirical Verification**: Queries `kubernetes_mcp_server.get_pod_status(pod_name="payment-service")` → `1/1 Ready`.
5. **Result**: `status: "completed"`, `recovery_confirmed: true`, `attempts: 1`.

---

### ⚡ SCENARIO 2: Multi-Attempt Retry, Fallback Runbook & Jira Escalation

**Story**: A broken container image (`v2.0.0-broken`) is deployed. The agent attempts `RB-001` restart twice. When verification fails, it automatically switches to fallback runbook `RB-002` (Rollback Deployment). When `RB-002` fails, the agent invokes the Jira FastMCP server over stdio to generate ticket `INC-101`.

#### Execution Commands (EC2 Terminal):

```bash
# 1. Deploy broken container release to K3s
kubectl apply -f k8s/demo/payment-service-v2-broken.yaml -n ecommerce
sleep 5

# 2. Trigger incident alert
python3 scripts/incidents/simulate_payment_crash.py

# 3. Restore healthy payment deployment
kubectl apply -f k8s/demo/payment-service-v1-healthy.yaml -n ecommerce
```

#### What Happens Under the Hood:
1. **Attempt 1 (`RB-001`)**: Agent calls `rollout_restart` → Health check fails (`healthy: false`).
2. **Attempt 2 (`RB-001`)**: Agent retries `rollout_restart` → Health check fails again.
3. **Fallback Transition**: Max retries reached → Agent transitions to fallback runbook `RB-002` (Rollback Deployment).
4. **Attempt 1 (`RB-002`)**: Agent calls `rollout_undo` → Health check fails.
5. **Jira Escalation**: All retries and fallback runbooks exhausted → Agent calls `jira_mcp_server.create_ticket` → Generates ticket **`INC-101`**!

---

### 🔬 SCENARIO 3: Dry-Run Mode & Failure Simulation

**Story**: Test full state machine retries, fallback transitions, and Jira ticket generation in offline dry-run mode without modifying your live K3s cluster.

#### Execution Commands (EC2 Terminal):

```bash
export K8S_DRY_RUN="true"
export FORCE_UNHEALTHY="true"

python3 scripts/incidents/simulate_payment_crash.py
```

---

## 🌐 Public IP Endpoints (Replace `<YOUR_EC2_PUBLIC_IP>` with your EC2 IP)

1. **Frontend Web App**: `http://<YOUR_EC2_PUBLIC_IP>/` or `http://<YOUR_EC2_PUBLIC_IP>:30000/`
2. **FastMCP Interactive Web Inspector Console**: `http://<YOUR_EC2_PUBLIC_IP>:8000/mcp-ui`
3. **FastAPI Agent OpenAPI Documentation**: `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`
4. **Agent Health Status**: `http://<YOUR_EC2_PUBLIC_IP>:8000/health`

---

## 🛑 Stopping the Environment

```bash
./scripts/stop_free_tier.sh
```
