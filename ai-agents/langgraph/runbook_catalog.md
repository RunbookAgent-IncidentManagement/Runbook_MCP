# Runbook Catalog — AuraCommerce AI Incident Management

Enterprise-grade runbook definitions mapped to the LangGraph Runbook Agent.

---

## RB-001 Restart Deployment

**Trigger Conditions:**
- Incident Category: `POD_FAILURE`
- Health check fails (`/health` returns non-200)
- Kubernetes event: `Liveness probe failed` or `Back-off restarting failed container`
- Severity: `P1`

**Steps:**
1. `kubectl rollout restart deployment/{service}`
2. Wait 30s for new pods to become Ready
3. Verify readiness probe passes (`/health` 200)

**Verification Rules:**
- All pods in `Running` state (`kubectl get pods`)
- Readiness probe returns 200 for 3 consecutive checks
- No `CrashLoopBackOff` events in last 60s

**Escalation Rules:**
- If restart does not restore health within 120s → escalate to `P1` on-call engineer via SNS (`escalation-topic`)
- If deployment is unstable after 2 restarts → trigger `RB-002` (Rollback) automatically

---

## RB-002 Rollback Deployment

**Trigger Conditions:**
- Incident Category: `DEPLOYMENT_FAILURE`
- Deployment history shows new revision (`v2.0.0`) is unhealthy
- Previous revision (`v1.9.2`) is healthy
- Severity: `P2`

**Steps:**
1. `kubectl rollout undo deployment/{service}`
2. Confirm rollback to previous stable revision
3. Monitor metrics (CPU, memory, error rate) for 3 minutes

**Verification Rules:**
- Deployment pods running previous image tag
- Error rate returns to baseline (< 1%)
- Response time < 500ms (from Prometheus metrics)

**Escalation Rules:**
- If rollback fails to restore service → escalate `P2` to SRE team
- If previous revision also fails → escalate to `P1` incident commander and trigger `RB-001` (Restart)

---

## RB-003 Scale Service

**Trigger Conditions:**
- Incident Category: `HIGH_CPU` or `MEMORY_PRESSURE`
- CPU utilization > 70% for > 5 minutes (HPA metric)
- Memory utilization > 85% for > 5 minutes
- Severity: `P3`

**Steps:**
1. `kubectl scale deployment/{service} --replicas=6`
2. Update HPA `minReplicas` temporarily if needed
3. Watch CPU/memory return to < 50%

**Verification Rules:**
- New pods in `Running` state
- Average CPU across pods < 50% within 3 minutes
- Queue depth (if applicable) decreases

**Escalation Rules:**
- If CPU/memory does not drop after scale within 5 minutes → escalate `P3` (indicates deeper resource leak or traffic spike requiring `RB-006` or `RB-005`)

---

## RB-004 Restart Consumer

**Trigger Conditions:**
- Incident Category: `QUEUE_BACKLOG`
- Queue depth > 1000 (Amazon SQS / RabbitMQ metric)
- Consumer pods not processing messages (`notification-service` or `order-service` consumer)
- Severity: `P2`

**Steps:**
1. `kubectl rollout restart deployment/{consumer-service}`
2. Verify consumer logs show message processing (`event consumed`)
3. Monitor queue depth decrease

**Verification Rules:**
- Queue depth decreases by > 20% within 2 minutes
- No error logs (`ERROR: connection refused`) in consumer output
- Consumer health check passes

**Escalation Rules:**
- If queue depth continues to grow after restart → escalate to `P2` and trigger `RB-005` (DB Connectivity) or `RB-006` (Backlog Recovery)

---

## RB-005 Database Connectivity Recovery

**Trigger Conditions:**
- Incident Category: `DATABASE_CONNECTIVITY`
- Database connection refused / timeout errors in service logs
- PostgreSQL health check fails (`pg_isready` fails)
- Severity: `P1`

**Steps:**
1. Verify PostgreSQL service status (`kubectl get pods -n database` or `docker ps` locally)
2. Check `DATABASE_URL` configuration (`ConfigMap` / `Secret` reference)
3. Restart database connection pool in service (if applicable) or restart service
4. Verify SQL queries return results (`SELECT 1`)

**Verification Rules:**
- `pg_isready` returns `accepting connections`
- Service health check passes
- No `connection refused` errors in last 60s

**Escalation Rules:**
- If DB does not recover within 3 minutes → escalate `P1` to infrastructure team (potential RDS / EKS storage layer issue)
- If DB is down but service has read-only fallback → escalate `P2` instead

---

## RB-006 Queue Backlog Recovery

**Trigger Conditions:**
- Incident Category: `QUEUE_BACKLOG`
- Queue depth > 1000 messages
- Consumer lag > 5 minutes
- Severity: `P2`

**Steps:**
1. Scale consumer deployment (`kubectl scale deployment/{consumer} --replicas=4`)
2. If scale does not resolve within 3 minutes: restart consumer (`RB-004`)
3. Monitor queue depth decrease to < 100

**Verification Rules:**
- Queue depth < 100 within 5 minutes of action
- Consumer lag < 30 seconds
- No message duplication errors

**Escalation Rules:**
- If queue depth remains > 1000 after scale + restart → escalate `P2` and investigate upstream producer (`order-service`, `payment-service`) for infinite retry loops
- If backlog is caused by DB connectivity (`RB-005`) → trigger `RB-005` first

---

## Catalog Mapping (Agent Integration)

| Incident Category | Severity | Recommended Runbook | Primary Action |
|---|---|---|---|
| `POD_FAILURE` | P1 | RB-001 | Restart Deployment |
| `DEPLOYMENT_FAILURE` | P2 | RB-002 | Rollback Deployment |
| `HIGH_CPU` | P3 | RB-003 | Scale Service |
| `MEMORY_PRESSURE` | P3 | RB-003 | Scale Service |
| `SERVICE_DOWN` | P1 | RB-001 | Restart Deployment |
| `QUEUE_BACKLOG` | P2 | RB-006 | Queue Backlog Recovery |
| `DATABASE_CONNECTIVITY` | P1 | RB-005 | DB Connectivity Recovery |
| `CONFIGURATION_ERROR` | P3 | RB-006 / RB-002 | Patch Config / Rollback |

---

*Catalog Status: Complete | Ready for LangGraph Runbook Agent Integration*
