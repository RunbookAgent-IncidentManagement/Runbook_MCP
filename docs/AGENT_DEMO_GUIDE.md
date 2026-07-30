# 🚀 AuraCommerce Agentic Workflow — AWS Free Tier (`t3.small`) Demonstration Guide

> **Core Objective**: Demonstrate **Autonomous AI Agentic Workflows** (LLM Incident Classification → FastMCP Stdio Tools → Kubernetes Pod Health Verification → 2-Attempt Retries → Jira Ticket Escalation) on a lightweight AWS Free Tier EC2 instance using **Docker Hub container images (`secretpower/*-rba:v1`)**.

---

## 📐 Agentic Architecture Overview

```
                      [ K3s Pod Crash Alert / Webhook ]
                                     │
                                     ▼ (HTTP POST)
                       ┌───────────────────────────┐
                       │  FastAPI Runner Service   │
                       │   (http://...:8000/docs)  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENTIC STATE MACHINE                      │
│                                                                         │
│  1. LLM Classification ──► 2. Declarative Catalog ──► 3. FastMCP Exec   │
│     (Mistral 7B / HF)         (runbook_actions.yaml)     (rollout_restart)│
│                                                               │         │
│                                                               ▼         │
│  5. Jira Ticket Creation ◄── 4. Retry Evaluator ◄── Verification        │
│     (Escalation after 2      (Attempts <= 2)         (get_pod_status)   │
│      failed retries)                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Hub Container Image Mapping

| Component | Container Image Tag | Kubernetes Manifest | Exposed Port / NodePort |
|---|---|---|---|
| **Frontend Web App** | `secretpower/frontend-rba:v1` | [k8s/base/frontend/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/frontend/deployment.yaml) | `http://<IP>/` & Port `30000` |
| **Product Service** | `secretpower/product-rba:v1` | [k8s/base/product/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/product/deployment.yaml) | `http://<IP>/products` & Port `30001` |
| **Cart Service** | `secretpower/cart-rba:v1` | [k8s/base/cart/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/cart/deployment.yaml) | `http://<IP>/cart` & Port `30002` |
| **Order Service** | `secretpower/order-rba:v1` | [k8s/base/order/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/order/deployment.yaml) | `http://<IP>/orders` & Port `30003` |
| **Payment Service** | `secretpower/payment-rba:v1` | [k8s/base/payment/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/payment/deployment.yaml) | `http://<IP>/payments` & Port `30004` |
| **Notification Service** | `secretpower/notification-rba:v1` | [k8s/base/notification/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/notification/deployment.yaml) | `http://<IP>/notifications` & Port `30005` |
| **Auth Service** | `secretpower/auth-rba:v1` | [k8s/base/auth/deployment.yaml](file:///c:/Users/Pruthvi%20Bhat/OneDrive/Desktop/UST/RunBook_for_Ecommerce/k8s/base/auth/deployment.yaml) | `http://<IP>/auth` & Port `30006` |

---

## ⏱️ Quick Start Checklist (Run Demo in < 5 Minutes)

| Step | Action | Command / Location | Time |
|---|---|---|---|
| **1. Provision** | Launch EC2 `t3.small` (Ubuntu 22.04) | AWS Console | 1 min |
| **2. Security Group** | Allow Ports `80`, `8000`, `30000-32767` | AWS Security Group | 1 min |
| **3. Transfer** | Copy workspace or `git clone` | `git clone ...` | 1 min |
| **4. Launch** | Run One-Click Setup Script | `./scripts/setup_free_tier.sh` | 1 min |
| **5. Demo** | Trigger Live Agentic Incident Flows | `python3 scripts/incidents/simulate_payment_crash.py` | 30 sec |

---

## 🔧 Step-by-Step Deployment Setup

### Step 1: Launch EC2 Instance (`t3.small`)
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: `t3.small` (2 vCPUs, 2 GiB RAM — Free Tier eligible)
- **Security Group Inbound Rules**:
  - `22` (SSH) — My IP
  - `80` (HTTP Traefik Ingress)
  - `8000` (FastAPI Agent Runner API & Interactive FastMCP Console)
  - `30000 - 32767` (Kubernetes NodePorts for direct service access)

### Step 2: System Setup & One-Click Launch (EC2 Terminal)

```bash
# 1. SSH into your EC2 instance
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>

# 2. Clone repository & navigate to root
git clone https://github.com/RunbookAgent-IncidentManagement/Runbook_MCP.git
cd Runbook_MCP

# 3. Export Hugging Face API Key (Optional — rule engine fallback triggers if omitted)
export HUGGINGFACE_TOKEN="hf_your_actual_token_here"
export HUGGINGFACE_API_URL="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# 4. Set K8S_DRY_RUN to false to interact with real K3s cluster
export K8S_DRY_RUN="false"

# 5. Run One-Click Setup Script
chmod +x scripts/setup_free_tier.sh scripts/stop_free_tier.sh
./scripts/setup_free_tier.sh
```

**What `./scripts/setup_free_tier.sh` automates:**
1. Configures 2GB Swap Memory (prevents OOM on Free Tier).
2. Installs K3s lightweight Kubernetes cluster.
3. Applies base database (`postgres`), redis, `shared-code` ConfigMap, and frontend manifests.
4. Deploys all 6 microservices using `secretpower/*-rba:v1` Docker Hub images with `replicas: 1`, `requests.memory=64Mi`, and `requests.cpu=50m`.
5. Deploys K3s Traefik Ingress (Port 80) and NodePorts (`30000-30006`).
6. Launches FastMCP stdio servers and FastAPI Agent Runner service (`http://0.0.0.0:8000`).

---

## 🌐 Public Access Endpoints (Replace `<YOUR_EC2_PUBLIC_IP>` with your EC2 IP)

### 1. Frontend E-Commerce Web Application
- **Main Web App (Port 80)**: `http://<YOUR_EC2_PUBLIC_IP>/`
- **Direct NodePort (Port 30000)**: `http://<YOUR_EC2_PUBLIC_IP>:30000/`

### 2. FastAPI Runbook Agent & Interactive FastMCP Testing Console
- **Interactive Swagger UI**: `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`
- **Agent Health**: `http://<YOUR_EC2_PUBLIC_IP>:8000/health`
- **Runbook Catalog**: `http://<YOUR_EC2_PUBLIC_IP>:8000/runbooks`
- **Interactive FastMCP Tool Tester**: `http://<YOUR_EC2_PUBLIC_IP>:8000/docs#operations-mcp-call_mcp_tool`
  - `GET /mcp/tools` — Lists all registered FastMCP tools & arguments.
  - `POST /mcp/tools/call` — Interactively executes any FastMCP tool (`get_pod_status`, `rollout_restart`, `scale_deployment`, `create_ticket`).

---

## 🎭 Demonstrating the Agentic Workflows Live

### 🌟 DEMO SCENARIO 1: Autonomous Remediation (Self-Healing)

**Story**: A payment microservice suffers a transient crash (`CrashLoopBackOff`). The AI Agent classifies the error using Mistral LLM, selects `RB-001`, invokes the Kubernetes FastMCP tool over stdio to restart the deployment, and verifies health recovery autonomously.

#### Execution Command:
```bash
python3 scripts/incidents/simulate_payment_crash.py
```

#### What Happens Under the Hood (Agentic Workflow Steps):
1. **Alert Payload**: Webhook sends `CrashLoopBackOff` alert to `http://localhost:8000/execute`.
2. **Mistral LLM Classification**: Analyzes log trace (`OutOfMemoryError: Metaspace`) → Maps to `RB-001` (Restart Deployment).
3. **FastMCP Stdio Tool Execution**: Agent calls `kubernetes_mcp_server.rollout_restart(deployment="payment-service")`.
4. **Real Pod Status Verification**: Agent queries `kubernetes_mcp_server.get_pod_status(pod_name="payment-service")` → `HEALTHY (1/1)`.
5. **Completion**: Incident resolved autonomously in `Attempt 1/2`.

---

### ⚡ DEMO SCENARIO 2: Multi-Attempt Retry & Jira Escalation

**Story**: A broken application release (`v2.0.0-broken`) is deployed. The agent attempts remediation twice (`Attempt 1/2` and `Attempt 2/2`). When verification fails after 2 attempts, the agent automatically triggers the escalation path and files a Jira incident ticket via the Jira FastMCP server.

#### Step 1: Deploy Broken Release to K3s
```bash
kubectl apply -f k8s/demo/payment-service-v2-broken.yaml -n ecommerce
```

#### Step 2: Trigger Alert & Watch Escalation Flow
```bash
python3 scripts/incidents/simulate_payment_crash.py
```

#### What Happens Under the Hood:
1. **Attempt 1**: Agent calls `rollout_restart` → Verification checks pod status → `UNHEALTHY (exit 1)`.
2. **Attempt 2 (Retry Loop)**: Agent detects `attempts < 2` → Automatically retries `rollout_restart` → Verification fails again.
3. **Automatic Escalation**: Max retries reached (`attempts == 2`) → Agent calls `jira_mcp_server.create_ticket(title="P1 Incident Unresolved: payment-service Pod CrashLoop")`.
4. **Result**: Jira ticket key `INC-101` generated with full audit trail!

#### Step 3: Clean Up Broken Release
```bash
kubectl apply -f k8s/demo/payment-service-v1-healthy.yaml -n ecommerce
```

---

## 🧪 Pipeline Smoke Test Command

To verify all components (Mistral LLM, FastMCP tools, LangGraph state machine, Jira ticket creation) in under 5 seconds:

```bash
python3 scripts/test_agent_pipeline.py
```

---

## 🛑 Stopping the Environment

When you finish your demonstration or want to power off your EC2 instance:

```bash
./scripts/stop_free_tier.sh
```

---

## 📌 Summary of Agentic Capabilities Demonstrated

- **LLM Reasoning**: HuggingFace Mistral-7B classifies unstructured logs into declarative runbooks.
- **Protocol Compliance**: Tools execute over FastMCP `stdio` transport.
- **State Machine Control**: LangGraph manages execution state, attempt counters, and retry loops.
- **Empirical Verification**: Checks real pod status via Kubernetes API before declaring success.
- **Autonomous Escalation**: Automatically creates Jira tickets when remediation retries are exhausted.
- **Interactive Tool Console**: Interactive Swagger UI on Port `8000` for live tool inspection and invocation.
