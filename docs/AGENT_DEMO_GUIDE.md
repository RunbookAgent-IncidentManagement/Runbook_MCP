# 🚀 AuraCommerce Agentic Workflow — AWS Free Tier (`t3.small`) Demonstration Guide

> **Core Objective**: Demonstrate **Autonomous AI Agentic Workflows** (LLM Incident Classification → FastMCP Stdio Tools → Kubernetes Pod Health Verification → 2-Attempt Retries → Jira Ticket Escalation) on a lightweight AWS Free Tier EC2 instance.

---

## 📐 Agentic Architecture Overview

```
                      [ K3s Pod Crash Alert ]
                                 │
                                 ▼ (HTTP POST)
                   ┌───────────────────────────┐
                   │  FastAPI Runner Service   │
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

## ⏱️ Quick Start Checklist (Run Demo in < 5 Minutes)

| Step | Action | Command / Location | Time |
|---|---|---|---|
| **1. Provision** | Launch EC2 `t3.small` (Ubuntu 22.04) | AWS Console | 1 min |
| **2. Prep** | Configure 2GB Swap & Install K3s | Copy-paste terminal commands | 1 min |
| **3. Transfer** | Copy workspace & set HuggingFace Token | `scp` / `export HUGGINGFACE_TOKEN=...` | 1 min |
| **4. Launch** | Run One-Click Setup Script | `./scripts/setup_free_tier.sh` | 1 min |
| **5. Demo** | Trigger Live Agentic Incident Flows | `python scripts/incidents/simulate_payment_crash.py` | 30 sec |

---

## 🔧 Step-by-Step Deployment Setup

### Step 1: Launch EC2 Instance (`t3.small`)
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: `t3.small` (2 vCPUs, 2 GiB RAM — Free Tier eligible)
- **Security Group Inbound Rules**:
  - `22` (SSH) — My IP
  - `8000` (FastAPI Agent Runner API)

### Step 2: SSH & System Optimization (EC2 Terminal)
Connect to your EC2 instance and enable a **2 GB Swap File** to ensure smooth execution of K3s and Python processes:

```bash
# SSH into your EC2 instance
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>

# System update & 2GB Swap Memory Configuration
sudo apt update && sudo apt install -y git curl python3 python3-pip python3-venv docker.io
sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab || true

# Verify 2GB swap is active
free -h
```

---

### Step 3: Install K3s Lightweight Kubernetes
```bash
# Install single-node K3s
curl -sfL https://get.k3s.io | sh -

# Configure kubectl permissions
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
export KUBECONFIG=~/.kube/config

# Verify cluster node status
kubectl get nodes
```

---

### Step 4: Transfer Workspace & Configure Environment
From your **Local Terminal**, copy the repository to EC2:

```bash
scp -r -i /path/to/your-key.pem "RunBook_for_Ecommerce" ubuntu@<YOUR_EC2_PUBLIC_IP>:~/
```

Then on your **EC2 Terminal**:

```bash
cd ~/RunBook_for_Ecommerce

# Export your Hugging Face API Key (Inference API)
export HUGGINGFACE_TOKEN="hf_your_actual_token_here"
export HUGGINGFACE_API_URL="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# Jira credentials (Optional — runs in mock mode if token is omitted)
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_TOKEN=""
export JIRA_PROJECT_KEY="INC"

# Set K8S_DRY_RUN to false to interact with real K3s cluster
export K8S_DRY_RUN="false"
```

---

### Step 5: Launch Environment with One Command

Run the automated launch script:

```bash
chmod +x scripts/setup_free_tier.sh scripts/stop_free_tier.sh
./scripts/setup_free_tier.sh
```

**What `./scripts/setup_free_tier.sh` automates:**
1. Verifies 2GB Swap Memory and K3s cluster readiness.
2. Creates Kubernetes namespace `ecommerce`.
3. Deploys healthy payment microservice deployment (`k8s/demo/payment-service-v1-healthy.yaml`).
4. Launches **Kubernetes FastMCP Server** & **Jira FastMCP Server** over stdio.
5. Starts the **FastAPI Agent Runner Service** on port `8000`.

---

## 🎭 Demonstrating the Agentic Workflows Live

Now you are ready to demonstrate the AI Agentic Capabilities to your audience!

---

### 🌟 DEMO SCENARIO 1: Autonomous Remediation (Self-Healing)

**Story**: A payment microservice suffers a transient crash (`CrashLoopBackOff`). The AI Agent classifies the error using Mistral LLM, selects `RB-001`, invokes the Kubernetes FastMCP tool to restart the deployment, and verifies health recovery autonomously.

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
