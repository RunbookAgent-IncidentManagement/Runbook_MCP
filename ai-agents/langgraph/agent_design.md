# LangGraph AI Agent Layer — Direct Catalog Specification

Enterprise-grade AI Incident Management Layer for AuraCommerce using direct Runbook Catalog mapping and the LangGraph Runbook Agent.

---

## DIRECT RUNBOOK CATALOG AGENT

**File:** `runbook_agent.py`
**Catalog Reference:** `runbook_catalog.md`
**Purpose:** Receive alert events, select matching runbook from the Catalog (RB-001 through RB-006), validate conditions, execute remediation via MCP tools (Kubernetes / Jira), verify recovery, and escalate on failure.

### Supported Runbooks & Actions

- `RB-001`: **Restart Deployment** (Pod Crash / Service Down) → `kubectl rollout restart deployment/{service}`
- `RB-002`: **Rollback Deployment** (Deployment Failure) → `kubectl rollout undo deployment/{service}`
- `RB-003`: **Scale Service** (High CPU / Memory Pressure) → `kubectl scale deployment/{service} --replicas=6`
- `RB-004`: **Restart Consumer** (Queue Backlog / Consumer Stall) → `kubectl rollout restart deployment/{consumer}`
- `RB-005`: **DB Connectivity Recovery** (Database Connection Failure) → `kubectl rollout restart deployment/postgres`
- `RB-006`: **Queue Backlog Recovery** (High Queue Depth) → `kubectl scale deployment/{consumer} --replicas=4`

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

1. **load_runbook** — Load runbook from `runbook_catalog.md` by `runbook_id`
2. **validate_conditions** — Check prerequisites (deployment exists, DB healthy, etc.)
3. **execute_remediation** — Execute `kubectl` / MCP actions mapped to runbook
4. **verify_recovery** — Check health probes, metrics, deployment status
5. **generate_report** — Structured incident report (incident, service, actions, verification, escalation)
6. **escalate** — Human escalation via SNS / Slack / Jira ticket creation

### Workflow (Graph)

```
load_runbook → validate_conditions → execute_remediation → verify_recovery
                                                         ↓
                                                verification_result?
                                                         ↓
                                              True  → generate_report → END
                                              False → escalate (Jira Ticket) → END
```

---

## Direct Catalog Alert Mapping

| Event / Alert Category | Severity | Direct Catalog Runbook | Primary MCP Action |
|---|---|---|---|
| `POD_FAILURE` / `CrashLoopBackOff` | P1 | RB-001 | Restart Deployment (`kubectl rollout restart`) |
| `DEPLOYMENT_FAILURE` | P2 | RB-002 | Rollback Deployment (`kubectl rollout undo`) |
| `HIGH_CPU` / `MEMORY_PRESSURE` | P3 | RB-003 | Scale Service (`kubectl scale --replicas=6`) |
| `DATABASE_CONNECTIVITY` | P1 | RB-005 | DB Connectivity Recovery |
| `QUEUE_BACKLOG` | P2 | RB-006 | Queue Backlog Recovery |

---

## Status

- **Design Spec**: Single Direct Runbook Agent Architecture (`runbook_agent.py` + `runbook_catalog.md`)
- **Runbook Catalog**: Complete (RB-001 to RB-006)
- **MCP Servers**: Kubernetes MCP + Jira MCP operational
- **Runner Service**: Direct HTTP Alert Ingestion (`services/runbook-runner/app/main.py`)
