# LangGraph AI Agent Layer — Design Specification (Complete)

Enterprise-grade AI Incident Management Layer for AuraCommerce.
Two sequential LangGraph agents: RCA Agent (classification + root cause) and Runbook Agent (remediation + verification). Both support human escalation to SNS/Slack.

---

## AGENT 1: RCA AGENT

**File:** `rca_agent.py`
**Purpose:** Receive alerts, analyze signals, classify incidents, determine root cause, assign severity, select runbook.

### Incident Categories (Enum)

- `POD_FAILURE`
- `DEPLOYMENT_FAILURE`
- `HIGH_CPU`
- `MEMORY_PRESSURE`
- `SERVICE_DOWN`
- `QUEUE_BACKLOG`
- `DATABASE_CONNECTIVITY`
- `CONFIGURATION_ERROR`

### Severity Levels

- `P1` — Service down / DB down / Payment crash / Critical security
- `P2` — Deployment failure / Queue backlog / Consumer down / Partial outage
- `P3` — High CPU / Memory pressure / Config error / Degraded performance
- `P4` — Low-priority anomaly / Monitoring threshold exceeded

### State Model (`RCAState`)

```python
class RCAState(TypedDict):
    alert_id: str
    alert_name: str
    affected_service: Optional[str]
    logs: List[str]
    metrics: Dict[str, Any]
    k8s_events: List[str]
    deployment_history: List[str]
    incident_category: Optional[str]
    severity: Optional[str]
    root_cause: Optional[str]
    confidence: float
    recommended_runbook: Optional[str]
    status: str  # analyzing | classified | escalated | completed
    human_escalated: bool
```

### Nodes

1. **fetch_logs** — Tool: CloudWatch Logs Insights / `kubectl logs`
2. **analyze_metrics** — Tool: Prometheus Metrics API / CloudWatch Metrics
3. **analyze_k8s_events** — Tool: `kubectl get events --sort-by='.lastTimestamp'`
4. **analyze_deployments** — Tool: `kubectl rollout history deployment/{service}`
5. **classify_incident** — LLM Node: Structured classification prompt
6. **assign_severity** — Decision logic based on category + service impact
7. **select_runbook** — Mapping dictionary (`POD_FAILURE` → `RB-001`, etc.)
8. **escalate_or_complete** — Conditional: `confidence < 0.7` or no runbook match → escalate

### LLM Prompt (Classify Incident Node)

```
You are the AuraCommerce RCA Agent. Analyze the following signals and classify the incident.

Logs: {logs}
Metrics: CPU={cpu}%, Memory={memory}%, QueueDepth={queue_depth}
Kubernetes Events: {k8s_events}
Deployment History: {deployment_history}
Affected Service: {service}

Output ONLY a JSON object:
{
  "incident_category": "POD_FAILURE|DEPLOYMENT_FAILURE|HIGH_CPU|MEMORY_PRESSURE|SERVICE_DOWN|QUEUE_BACKLOG|DATABASE_CONNECTIVITY|CONFIGURATION_ERROR",
  "severity": "P1|P2|P3|P4",
  "root_cause": "One sentence technical explanation",
  "confidence": 0.0-1.0,
  "recommended_runbook": "RB-001|RB-002|...|RB-006"
}
```

### Sample Output

```json
{
  "incident_type": "POD_FAILURE",
  "affected_service": "payment-service",
  "severity": "P1",
  "confidence": 0.94,
  "recommended_runbook": "RB-001"
}
```

---

## AGENT 2: RUNBOOK AGENT

**File:** `runbook_agent.py`
**Purpose:** Load runbook, validate conditions, execute remediation, verify recovery, generate report, escalate on failure.

### Supported Actions

- `Restart Pod` → `RB-001`
- `Restart Deployment` → `RB-001` / `RB-004`
- `Rollback Deployment` → `RB-002`
- `Scale Deployment` → `RB-003`
- `Restart Consumer` → `RB-004`
- `Patch Config` → `RB-006`
- `Restart Service` → `RB-001`

### State Model (`RunbookState`)

```python
class RunbookState(TypedDict):
    runbook_id: str
    incident_details: Dict[str, Any]
    conditions_met: List[str]
    actions_executed: List[str]
    verification_result: Optional[bool]
    recovery_confirmed: bool
    escalation_required: bool
    report: Optional[str]
    status: str  # loading | validating | executing | verifying | completed | escalated
```

### Nodes

1. **load_runbook** — Load from `runbook_catalog.md` by `runbook_id`
2. **validate_conditions** — Check prerequisites (deployment exists, DB healthy, etc.)
3. **execute_remediation** — Execute `kubectl` actions mapped to runbook
4. **verify_recovery** — Check health probes, metrics, deployment status
5. **generate_report** — Structured incident report (incident, service, actions, verification, escalation)
6. **escalate** — Human escalation via SNS / Slack / PagerDuty stub

### Workflow (Graph)

```
load_runbook → validate_conditions → execute_remediation → verify_recovery
                                                         ↓
                                                verification_result?
                                                         ↓
                                              True  → generate_report → END
                                              False → escalate → END
```

### Verification Workflow Rules

- `RB-001`: Readiness probe 200 (3 checks), no `CrashLoopBackOff` events (60s)
- `RB-002`: Previous revision pods running, error rate < 1%, response time < 500ms
- `RB-003`: CPU < 50% within 3 min, new pods `Running`
- `RB-004`: Queue depth decreases > 20% within 2 min, no connection errors
- `RB-005`: `pg_isready` accepting, health check 200, no connection refused errors (60s)
- `RB-006`: Queue depth < 100 within 5 min, consumer lag < 30s

### Human Escalation Workflow

Trigger conditions:
- `confidence < 0.7` (RCA Agent)
- No matching runbook selected
- Runbook verification fails (`recovery_confirmed = False`)
- Action fails twice (retry limit exceeded)

Escalation path:
1. SNS Topic: `escalation-topic` (SMS + Email)
2. Slack Channel: `#incident-response`
3. PagerDuty Integration (stub)
4. Audit Trail: Log to S3 / OpenSearch (`incident-id`, `agent-decisions`, `actions-taken`, `verification-results`)

---

## Integration with Monitoring & Kubernetes

### Lambda Trigger (Stub)

When a CloudWatch alarm fires (e.g., `ALARM: payment-service-health-failed`), an AWS Lambda triggers the RCA Agent endpoint. The agent analyzes signals and returns a structured result. If a runbook is selected, the Lambda triggers the Runbook Agent.

```python
# Lambda trigger (stubbed for AWS integration)
import requests

def lambda_handler(event, context):
    alert = event.get("alert", {})
    rca_resp = requests.post(
        "http://rca-agent-service:8000/analyze",
        json=alert,
        timeout=30
    )
    result = rca_resp.json()
    if result.get("recommended_runbook"):
        requests.post(
            "http://runbook-agent-service:8001/execute",
            json={
                "runbook_id": result["recommended_runbook"],
                "incident_details": result,
                "service": result.get("affected_service")
            },
            timeout=60
        )
    return result
```

---

## Tool Definitions (Shared)

### Kubernetes Events Tool
```python
import subprocess

def kubectl_events(namespace="default", service="payment-service", limit=20):
    cmd = [
        "kubectl", "get", "events",
        "-n", namespace,
        "--field-selector", f"involvedObject.name={service}",
        "--sort-by=.lastTimestamp",
        "-o", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```

### Metrics Tool (Prometheus)
```python
import requests

def query_prometheus(query: str, url: str = "http://prometheus:9090") -> dict:
    resp = requests.get(
        f"{url}/api/v1/query",
        params={"query": query},
        timeout=10
    )
    return resp.json()
```

### CloudWatch Logs Tool
```python
# Stub: would use boto3 to query CloudWatch Logs Insights
# Example query: fields @message | filter @message like /error/
```

---

## Agent Implementation Status

- Design Spec: Complete (`agent_design.md` + `runbook_catalog.md`)
- Python Skeletons: `rca_agent.py` (StateGraph, nodes, prompts) + `runbook_agent.py` (StateGraph, nodes, verification, escalation)
- Kubernetes Integration: Incident simulation cards mapped; Lambda trigger stubbed
- AWS Integration: Ready for Phase 2 (EKS, Lambda, SNS, EventBridge)
