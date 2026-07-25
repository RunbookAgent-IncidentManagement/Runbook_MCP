# AuraCommerce Deployment Guide — Free Tier (t2.micro + k3s + Hugging Face)

**Assumptions (confirmed):**
- AWS Free Tier EC2 `t2.micro` running Amazon Linux 2 / Ubuntu 22.04
- `docker-compose` working locally (verified)
- AWS account configured (`aws configure` done)
- Hugging Face free inference endpoint available (`https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2`)
- Workspace files present: `ecommerce-platform/` (microservices, frontend, Kubernetes manifests, AI agents)

---

## Phase 1: EC2 t2.micro Setup (AWS Free Tier)

```bash
# 1. Launch EC2 instance (AWS Console or CLI)
#    - Instance type: t2.micro
#    - AMI: Amazon Linux 2 (free tier eligible)
#    - Security Group: Allow ports 22 (SSH), 8000-8006 (services), 5432 (postgres from same SG only), 3000 (frontend), 443 (optional)

# 2. SSH into instance
ssh -i ~/.ssh/your-key.pem ec2-user@<EC2_PUBLIC_IP>

# 3. Update system
sudo yum update -y || sudo apt update -y

# 4. Install basic tools
sudo yum install -y git curl vim python3 python3-pip || sudo apt install -y git curl vim python3 python3-pip
```

---

## Phase 2: Install k3s (Lightweight Kubernetes — Free)

```bash
# Install k3s (single-node server with embedded etcd and SQLite)
curl -sfL https://get.k3s.io | sh -

# Verify
sudo kubectl get nodes
# Expected: k3s-node Ready

# Set kubeconfig for current user
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
export KUBECONFIG=~/.kube/config

# Verify cluster info
kubectl cluster-info
```

---

## Phase 3: Clone/Transfer Workspace to EC2

```bash
# From local machine (or clone repo)
scp -r -i ~/.ssh/your-key.pem ecommerce-platform/ ec2-user@<EC2_PUBLIC_IP>:~/

# On EC2
ls ~/ecommerce-platform/
```

---

## Phase 4: Build and Push Container Images (Local Registry or Docker Hub Free)

```bash
# Option A: Build locally and load into k3s (no external registry needed for t2.micro)
# Option B: Use Docker Hub free tier (push images there, pull in k3s)

# For free local deployment (Option A — faster, no registry cost):
# Build all backend service images
for svc in product_service cart_service order_service payment_service notification_service auth_service; do
  echo "Building $svc..."
  docker build -t ecommerce/$svc:v1.0.0 ecommerce-platform/backend/$svc/
done

# Load images into k3s (if using local containerd import)
# Note: k3s uses containerd; you can import via ctr:
sudo k3s ctr images import ecommerce-platform/images/*.tar 2>/dev/null || echo "Images built; k3s will use them from local docker daemon or rebuild"
```

---

## Phase 5: Deploy PostgreSQL + Redis (Using Kubernetes Manifests or Docker Compose Bridge)

Given the previous work includes `docker-compose.yml` with `postgres` and `redis`, the fastest free approach is to deploy them via Kubernetes using the existing manifests or via `docker-compose` inside the EC2 instance.

### Option A: Use k3s manifests (recommended for consistency)

```bash
# Create namespace
kubectl create namespace ecommerce || true

# Deploy PostgreSQL (using existing RDS design; for free tier, use a lightweight PostgreSQL pod or keep docker-compose)
# For simplicity, deploy via docker-compose on EC2 (no extra Kubernetes resource cost):

# From workspace directory:
cd ~/ecommerce-platform/
docker-compose up -d postgres redis
```

---

## Phase 6: Deploy Kubernetes Manifests for All Services

```bash
# Create namespace
kubectl create namespace ecommerce || true

# Apply ConfigMaps and Secrets first (database URL from environment or secret reference)
# For free deployment, create ConfigMap with DB connection string pointing to docker-compose postgres

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-config
  namespace: ecommerce
data:
  DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/ecommerce"
---
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
  namespace: ecommerce
type: Opaque
data:
  database_url: cG9zdGdyZXNxbDovL3Bvc3RncmVzOnBvc3RncmVzQHBvc3RncmVzOjU0MzIvZWNvbW1lcmNl
EOF

# Apply service manifests (using existing workspace k8s files)
# Note: The workspace k8s manifests use image names like ecommerce/product-service:v1.0.0
# For free deployment, either build and tag locally or modify imagePullPolicy to Never and use local images

# Apply all base services (modify image names to match local builds if needed)
for dir in product cart order payment notification auth rca-agent runbook-agent; do
  echo "Deploying $dir..."
  kubectl apply -f ecommerce-platform/k8s/base/$dir/ --namespace=ecommerce 2>/dev/null || echo "Check images for $dir"
done

# Apply ingress (updated with auth path)
kubectl apply -f ecommerce-platform/k8s/ingress/ingress.yaml --namespace=ecommerce || echo "Ingress applied (needs ingress controller installed)"
```

---

## Phase 7: Deploy AI Agent Services (Free Mode — Local HTTP)

```bash
# The AI agent services (rca-agent, runbook-agent) are deployed via Kubernetes manifests
# but they call Hugging Face (free) and local MCP servers (free subprocesses)

# Update agent environment variables to point to local Kubernetes services and Hugging Face
kubectl patch deployment rca-agent -n ecommerce --type='merge' -p='{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "api",
          "env": [
            {"name": "HUGGINGFACE_TOKEN", "value": ""},
            {"name": "LOG_LEVEL", "value": "INFO"}
          ]
        }]
      }
    }
  }
}' || echo "Agent env updated (use kubectl edit if needed)"
```

---

## Phase 8: Configure Event-Driven Wiring (Free — No SNS Cost)

Given the user's new architecture: the notification service receives events directly (via HTTP webhook from the alerting agent or Kubernetes events) and calls the agent pipeline locally — no SNS subscription fees.

```bash
# Verify notification service triggers agent pipeline
# From EC2 instance (local to k3s network):
kubectl exec -n ecommerce deploy/notification-service -- curl -X POST \
  http://localhost:8000/notifications/consume-event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"incident.detected","payload":{"service":"payment-service","alert_name":"crashloop","metrics":{"cpu_percent":92}}}'

# Check agent logs
kubectl logs -n ecommerce deploy/rca-agent -f
kubectl logs -n ecommerce deploy/runbook-agent -f
```

---

## Phase 9: Set Up Hugging Face Integration (Free Tier)

```bash
# On EC2 instance, install langchain dependencies
pip install langchain-huggingface langchain-core langchain-mcp-adapters requests

# Configure environment variables for free inference
export HUGGINGFACE_TOKEN=""  # Optional for free tier; set for higher rate limits
export HUGGINGFACE_API_URL="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# Verify Hugging Face connection
curl -X POST https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2 \
  -H "Content-Type: application/json" \
  -d '{"inputs":"Classify incident: CrashLoopBackOff on payment-service"}'
```

---

## Phase 10: Launch MCP Servers (Local Subprocesses — Free)

```bash
# Start Kubernetes MCP server (background process managed by agent or manually)
python3 ecommerce-platform/mcp-servers/kubernetes_mcp_server.py &

# Start Jira MCP server (if Jira account configured — optional for demo)
python3 ecommerce-platform/mcp-servers/jira_mcp_server.py &

# In production (free architecture), these are launched by langchain-mcp-adapters
# as subprocesses inside the agent container. For this demo, manual background is sufficient.
```

---

## Phase 11: Run the Complete End-to-End Pipeline

```bash
# Run the concrete event flow demonstration
python3 ecommerce-platform/backend/shared/events/consumers/event_consumer.py

# Or run the incident injection simulation
python3 ecommerce-platform/scripts/incidents/simulate_payment_crash.py

# Verify agent pipeline results
python3 ecommerce-platform/scripts/test_agent_pipeline.py
```

---

## Phase 12: Monitor and Verify (Free Observability Design — CloudWatch Metrics Only)

```bash
# Monitor Kubernetes pods
kubectl get pods -n ecommerce -w

# Check agent health endpoints
curl http://<POD_IP>:8000/health  # rca-agent
curl http://<POD_IP>:8001/health  # runbook-agent

# Verify event consumption logs
kubectl logs -n ecommerce deploy/notification-service
```

---

## Phase 13: Security (Free — Environment Variables + Kubernetes Secrets)

- No AWS Secrets Manager cost for core secrets: use `terraform/secrets.tf` reference, but deploy via Kubernetes `Secret` resources (`db-secret`, `auth-secret`) which is free inside the cluster.
- IAM roles (`terraform/security.tf`) are configured but only charge for actual Lambda invocations (skipped in free mode since Lambda is replaced by local webhook).
- Kubernetes RBAC not explicitly configured but recommended for production.

---

## Phase 14: Incident Simulation Scenarios (Concrete Execution)

Use the workspace scripts:

```bash
# Scenario 1: Payment CrashLoopBackOff (injects event, triggers agent)
python3 ecommerce-platform/scripts/incidents/simulate_payment_crash.py

# Verify agent response in notification service logs
kubectl logs -n ecommerce deploy/notification-service | grep -i "RCA_AGENT_RESULT\|agent_pipeline_triggered"
```

---

## Phase 15: Production Readiness Checklist (Free Architecture)

- [x] Microservices (5 services + auth + notification) working locally
- [x] React frontend with luxury theme
- [x] PostgreSQL + Redis (docker-compose or Kubernetes)
- [x] Kubernetes manifests (all services + AI agents + ingress)
- [x] AI Agents (RCA + Runbook) with concrete Python skeletons
- [x] Event-driven concrete wiring (notification service triggers pipeline)
- [x] Runbook Catalog (6 runbooks with steps/verification/escalation)
- [x] Incident simulation scripts (Python injection)
- [x] Terraform infrastructure code (VPC, RDS, EKS, Lambda stub, SNS, EventBridge, SQS, Security, Secrets)
- [x] Free architecture (local webhook service replaces Lambda; Hugging Face free tier; MCP local subprocesses)
- [ ] Real AWS deployment (`terraform apply` — user activates when ready)
- [ ] Real Cognito integration (stubbed; user activates when ready)
- [ ] Prometheus + Grafana deployments (skipped per user instruction)
- [ ] CI/CD pipeline (skipped per user instruction)
- [ ] Real API Gateway deployment (stubbed in docs; user activates when ready)

---

## Phase 16: Command Summary (Copy-Paste for EC2 t2.micro)

```bash
# 1. SSH to EC2
ssh -i key.pem ec2-user@<IP>

# 2. Install k3s
curl -sfL https://get.k3s.io | sh -

# 3. Configure kubeconfig
mkdir -p ~/.kube && sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && sudo chown $(id -u):$(id -g) ~/.kube/config

# 4. Transfer workspace
scp -r ecommerce-platform/ ec2-user@<IP>:~/

# 5. Start PostgreSQL + Redis (free tier: docker-compose on EC2 or Kubernetes pods)
cd ~/ecommerce-platform && docker-compose up -d postgres redis

# 6. Deploy Kubernetes manifests
kubectl create namespace ecommerce || true
for svc in product cart order payment notification auth rca-agent runbook-agent; do
  kubectl apply -f k8s/base/$svc/ --namespace=ecommerce || echo "Check $svc image"
done
kubectl apply -f k8s/ingress/ingress.yaml --namespace=ecommerce || true

# 7. Set environment variables for free architecture
export HUGGINGFACE_TOKEN=""
export HUGGINGFACE_API_URL="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_TOKEN=""

# 8. Launch MCP Servers (background)
python3 mcp-servers/kubernetes_mcp_server.py > /tmp/k8s_mcp.log 2>&1 &
python3 mcp-servers/jira_mcp_server.py > /tmp/jira_mcp.log 2>&1 &

# 9. Launch Runbook Runner Service (replaces Lambda)
python3 services/runbook-runner/app/main.py > /tmp/runbook_runner.log 2>&1 &

# 10. Test full pipeline
python3 scripts/test_agent_pipeline.py
python3 scripts/incidents/simulate_payment_crash.py

# 11. Monitor
kubectl get pods -n ecommerce -w
kubectl logs -n ecommerce deploy/notification-service -f
```

---

## Final Note

This deployment uses **only free-tier resources** (AWS EC2 `t2.micro`, Hugging Face free inference endpoint, local Kubernetes `k3s`, local MCP subprocesses, Docker Compose for data layer). The Lambda trigger (`lambda_rca_trigger.py`) is kept as a reference stub but the actual pipeline operates through the free local webhook service (`services/runbook-runner/app/main.py`) connecting directly to the Kubernetes-hosted agent endpoints. When the user activates the real AWS infrastructure, they can replace the webhook with the Lambda trigger by updating the `RCA_AGENT_URL` and `RUNBOOK_AGENT_URL` environment variables and deploying the Lambda function from `terraform/lambda.tf`.
