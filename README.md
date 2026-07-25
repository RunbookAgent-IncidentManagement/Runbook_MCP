# AuraCommerce — Enterprise E-Commerce & AI Incident Management Platform

> **Phase:** Application Core Implemented | AWS / Terraform / CI-CD: Design Complete, Implementation Phase 2

---

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (optional, provided by docker-compose)

### 1. Start Backend Services

```bash
docker-compose up --build
```

Services will be available at:
- Product Service: http://localhost:8001/docs
- Cart Service: http://localhost:8002/docs
- Order Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs
- Notification Service: http://localhost:8005/docs
- Auth Service: http://localhost:8006/docs
- PostgreSQL: localhost:5432 (user: postgres, pass: postgres, db: ecommerce)

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:3000

---

## Project Structure

```
ecommerce-platform/
├── frontend/                      # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx                # Main router, pages, components
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html                 # Custom theme with Tailwind CDN
│   ├── package.json
│   └── vite.config.js             # Proxy to backend services
│
├── backend/
│   ├── shared/                    # Shared library (DB, Events, Migrations)
│   │   ├── database.py
│   │   ├── events.py
│   │   ├── migrations/
│   │   └── alembic.ini
│   ├── auth-service/              # Cognito stub
│   ├── product-service/           # Product CRUD, Search, Categories
│   ├── cart-service/              # Cart operations
│   ├── order-service/             # Order lifecycle + event publishing
│   ├── payment-service/           # Simulated gateway + events
│   └── notification-service/      # Event consumption + SNS stub
│
├── k8s/                           # Kubernetes manifests (base + ingress)
│   ├── base/product/
│   ├── base/cart/
│   ├── base/order/
│   ├── base/payment/
│   ├── base/notification/
│   ├── ingress/ingress.yaml
│   └── observability/
│
├── ai-agents/
│   └── langgraph/
│       └── agent_design.md        # Full LangGraph RCA + Runbook specs
│
├── terraform/                     # IaC structure (Phase 2)
│   ├── modules/                   # VPC, EKS, RDS, SQS, SNS, Lambda, etc.
│   └── envs/dev, qa, prod
│
├── docs/
│   └── ARCHITECTURE.md            # Complete architecture document
│
├── docker-compose.yml             # Local orchestration
└── README.md                      # This file
```

---

## Microservices (Implemented)

All services use **Python 3.12**, **FastAPI**, **SQLAlchemy 2.0**, and **Pydantic 2**.

### Product Service (`backend/product-service`)
- Endpoints: `GET /products`, `GET /products/{id}`, `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}`, `GET /categories`
- Database: `products` table with UUID PK, indexed `category` and `sku`.
- Features: Search by name/description/sku, pagination (`page`, `limit`), category filtering.

### Cart Service (`backend/cart-service`)
- Endpoints: `GET /cart/{user_id}`, `POST /cart/{user_id}/items`, `PUT /cart/{user_id}/items/{item_id}`, `DELETE /cart/{user_id}/items/{item_id}`, `DELETE /cart/{user_id}`
- Database: `cart_items` table linked by `user_id` and `product_id`.

### Order Service (`backend/order-service`)
- Endpoints: `POST /orders`, `GET /orders/{id}`, `GET /orders/user/{user_id}`, `PATCH /orders/{id}/status`
- Database: `orders` + `order_items` (FK to `orders.id`).
- Events: Publishes simulated `order.created` events to a log-based event bus (stubbed for actual SQS/EventBridge in Phase 2).

### Payment Service (`backend/payment-service`)
- Endpoints: `POST /payments/process`, `GET /payments/{id}`, `GET /payments/order/{order_id}`
- Database: `payments` table with `transaction_ref`.
- Simulation: 95% success rate, 0.5s delay, random failure injection for demo purposes.
- Events: Publishes simulated `payment.processed` / `payment.failed` events.

### Notification Service (`backend/notification-service`)
- Endpoints: `POST /notifications/send`, `GET /notifications/user/{user_id}`, `POST /notifications/consume-event`
- Database: `notifications` table.
- Integration: Consumes simulated events; stubbed SNS integration (email/sms channels).

### Auth Service (`backend/auth-service`)
- Endpoints: `POST /auth/login`, `GET /auth/verify`
- Integration: Amazon Cognito stubbed; CORS middleware enabled for frontend.

---

## Frontend (React + Vite)

- **Framework:** React 18, React Router 6, Lucide Icons
- **Styling:** Tailwind CSS (via CDN for rapid prototyping; production uses PostCSS build)
- **Pages:**
  - `/` — Product Catalog (search, categories, add to cart stub)
  - `/cart` — Cart management overview
  - `/orders` — Order lifecycle visualization + Incident Simulation Scenarios
- **Features:** Responsive layout, dark theme, gradient backgrounds, simulated incident scenario cards with runbook tags.

---

## Event-Driven Design (Implemented in Code)

Although the AWS messaging layer (SQS, EventBridge, SNS) is stubbed for Phase 2, the code architecture is fully event-driven:

- `backend/shared/events.py` defines `BaseEvent`, `EventType`, and event payload schemas.
- `order-service/app/main.py` logs `EVENT_PUBLISHED: type=order.created` with structured payload.
- `payment-service/app/main.py` consumes order data and publishes `payment.processed` / `payment.failed`.
- `notification-service/app/main.py` provides `/notifications/consume-event` endpoint to receive business events and trigger notifications.

In Phase 2, these log-based stubs will be replaced with actual boto3 calls to SQS (`send_message`), EventBridge (`put_events`), and SNS (`publish`).

---

## Kubernetes (Implemented)

All business services have base manifests:
- `Deployment` (2 replicas, rolling update, resource limits)
- `Service` (ClusterIP)
- `HorizontalPodAutoscaler` (target 70% CPU, min 2, max 10)
- `ConfigMap` (service config: log level, service name)
- `Secret` (database URL encoded in base64)
- `Ingress` (nginx controller, TLS, rewrite rules)

Probes:
- Readiness: `GET /health` (initialDelay 5s, period 10s)
- Liveness: `GET /health` (initialDelay 15s, period 20s)

---

## Database & Migrations

- **Engine:** SQLAlchemy 2.0 with `create_engine` and `declarative_base()`.
- **Migration Tool:** Alembic (`backend/shared/alembic.ini`).
- **Initial Migration:** `001_initial.py` creates all 6 core tables with appropriate indexes, foreign keys, and server defaults.
- **Connection:** `DATABASE_URL` from environment (docker-compose provides PostgreSQL container).

---

## AI Incident Management Layer

### Design Complete (Phase 2 Integration)

The AI layer is fully designed but awaits AWS service integration to become fully operational:

1. **RCA Agent (`ai-agents/langgraph/agent_design.md`)**
   - LangGraph workflow with nodes: `fetch_logs`, `analyze_metrics`, `analyze_k8s_events`, `analyze_deployments`, `classify_incident`, `assign_severity`, `select_runbook`, `escalate_or_complete`.
   - State model with `incident_category`, `severity`, `confidence`, `recommended_runbook`.
   - Tools for Kubernetes events, Prometheus metrics, CloudWatch logs.
   - LLM prompts for structured classification.

2. **Runbook Agent (`ai-agents/langgraph/agent_design.md`)**
   - LangGraph workflow: `load_runbook`, `validate_conditions`, `execute_remediation`, `verify_recovery`, `generate_report`, `escalate`.
   - Tools: `kubectl rollout restart`, `rollout undo`, `scale`, `patch config`, `restart consumer`.
   - Verification rules per runbook (pod status, readiness, metrics, deployment revision).
   - Escalation workflow to SNS / PagerDuty.

3. **Runbook Catalog** (embedded in documentation):
   - RB-001: Restart Deployment
   - RB-002: Rollback Deployment
   - RB-003: Scale Service
   - RB-004: Restart Consumer
   - RB-005: Database Connectivity Recovery
   - RB-006: Queue Backlog Recovery

---

## Incident Simulation Scenarios

The `/orders` page includes interactive cards for 6 scenarios. When clicked, they simulate the incident flow and display the expected RCA agent output, runbook recommendation, and verification rules. These cards are designed to be connected to the actual simulation scripts (e.g., Kubernetes Jobs that inject failures) in Phase 2.

---

## Security Architecture

- **Network:** VPC with public/private subnets (Terraform design). EKS nodes in private subnets. NAT Gateway for outbound.
- **Authentication:** Amazon Cognito stubbed (`auth-service/app/main.py`). Production will use User Pool + App Client.
- **Authorization:** RBAC manifests planned for Kubernetes; IAM roles for EKS pods planned (IRSA).
- **Secrets:** `Secret` objects for DB URLs; AWS Secrets Manager integration planned for Phase 2.
- **Encryption:** TLS 1.3 on Ingress; RDS encryption at rest planned.

---

## Production Readiness (Current Status)

| Category | Completed | Planned (Phase 2) |
|---|---|---|
| Microservices Code | ✅ 5 Services + Auth | — |
| Frontend (React) | ✅ Implemented | — |
| Docker Compose | ✅ Working | — |
| Kubernetes Manifests | ✅ Base + Ingress | Overlays (dev/qa/prod) |
| Database Schema | ✅ SQLAlchemy + Alembic | RDS Provisioning |
| Event Design | ✅ Code + Schema | SQS / EventBridge / SNS |
| AI Agent Design | ✅ LangGraph Specs | AWS Lambda + Integration |
| Terraform / AWS | ✅ Module Design | Full Provisioning |
| CI/CD Pipeline | ✅ Design Document | GitHub Actions / CodePipeline |
| Monitoring / Observability | ✅ Metrics Strategy | Prometheus / Grafana / CloudWatch Dashboards |
| Security / IAM | ✅ Architecture | Implementation |

---

## Next Steps (Phase 2 — AWS & Integration)

1. **Terraform Apply:** Provision VPC, EKS, RDS, SQS, EventBridge, SNS, Lambda, Cognito, API Gateway, CloudWatch.
2. **AWS Integration:** Replace event stubs with boto3 calls to SQS (`send_message`), EventBridge (`put_events`), SNS (`publish`).
3. **Agent Integration:** Deploy RCA and Runbook agents as Lambda functions or EKS services with actual tool integrations (CloudWatch Insights, Kubernetes API, Prometheus).
4. **Observability:** Deploy Prometheus Operator, Grafana dashboards, and CloudWatch Alarms.
5. **CI/CD:** Implement GitHub Actions pipeline with ECR pushes, Terraform apply, and Kubernetes deploy (Kustomize / Helm).
6. **Security Hardening:** Implement Network Policies, Pod Security Standards, IRSA, and Secrets Manager integration.

---

## License & Purpose

This application is a **demonstration architecture** for enterprise architecture review. It is designed to showcase modern microservices patterns, event-driven design, Kubernetes resilience, and AI-powered operational automation. It is not intended for direct production use without Phase 2 hardening, security audits, and compliance validation.
