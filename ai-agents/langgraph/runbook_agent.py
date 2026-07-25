"""
Agent 2: Runbook Agent (Remediation + Verification)
LangGraph StateGraph for AuraCommerce runbook execution.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
import subprocess
import time


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


# ------------------------------------------------------------------
# Tool Stubs (Production-ready interfaces)
# ------------------------------------------------------------------

def load_runbook(state: RunbookState) -> RunbookState:
    """Load runbook definition from catalog by runbook_id."""
    runbook_id = state.get("runbook_id", "RB-001")
    # In production: load from database / S3 / file system (`runbook_catalog.md`)
    state["runbook_id"] = runbook_id
    state["status"] = "loading"
    return state


def validate_conditions(state: RunbookState) -> RunbookState:
    """Check prerequisites based on runbook trigger conditions."""
    conditions = []
    runbook_id = state.get("runbook_id")
    incident = state.get("incident_details", {})
    service = incident.get("affected_service", "unknown")

    if runbook_id == "RB-001" or runbook_id == "RB-004":
        conditions.extend(["Deployment exists", "Pod unhealthy or consumer lag detected"])
    elif runbook_id == "RB-002":
        conditions.extend(["Deployment history available", "Previous revision healthy"])
    elif runbook_id == "RB-003":
        conditions.extend(["Deployment exists", "CPU or memory threshold exceeded"])
    elif runbook_id == "RB-005":
        conditions.extend(["Database connection refused or timeout detected"])
    elif runbook_id == "RB-006":
        conditions.extend(["Queue depth exceeds threshold", "Consumer lag detected"])
    else:
        conditions.append("Generic conditions met")

    state["conditions_met"] = conditions
    state["status"] = "validating"
    return state


def execute_remediation(state: RunbookState) -> RunbookState:
    """Execute kubectl / remediation actions mapped to runbook."""
    actions = []
    runbook_id = state.get("runbook_id")
    service = state.get("incident_details", {}).get("affected_service", "service")
    deployment_name = f"{service}"  # Kubernetes service/deployment names use hyphens

    if runbook_id == "RB-001":
        actions.append(f"kubectl rollout restart deployment/{deployment_name}")
    elif runbook_id == "RB-002":
        actions.append(f"kubectl rollout undo deployment/{deployment_name}")
    elif runbook_id == "RB-003":
        actions.append(f"kubectl scale deployment/{deployment_name} --replicas=6")
    elif runbook_id == "RB-004":
        actions.append(f"kubectl rollout restart deployment/{deployment_name}-consumer")
    elif runbook_id == "RB-005":
        actions.append("kubectl rollout restart deployment/postgres")
        actions.append(f"kubectl exec -it <postgres-pod> -- psql -c 'SELECT 1;'")
        actions.append(f"kubectl rollout restart deployment/{deployment_name}")
    elif runbook_id == "RB-006":
        actions.append(f"kubectl scale deployment/{deployment_name}-consumer --replicas=4")
        actions.append(f"kubectl rollout restart deployment/{deployment_name}-consumer")

    state["actions_executed"] = actions
    state["status"] = "executing"
    return state


def verify_recovery(state: RunbookState) -> RunbookState:
    """Verify recovery based on runbook-specific rules."""
    runbook_id = state.get("runbook_id")
    service = state.get("incident_details", {}).get("affected_service", "unknown")
    verification_result = False

    # Stubbed verification logic (production would query Prometheus / Kubernetes / DB)
    if runbook_id == "RB-001":
        # Check readiness probe and no CrashLoopBackOff
        verification_result = True  # Simulated: probes pass, pods Running
    elif runbook_id == "RB-002":
        # Check previous revision pods running, error rate baseline
        verification_result = True
    elif runbook_id == "RB-003":
        # Check CPU < 50%, memory stable, pods Running
        verification_result = True
    elif runbook_id == "RB-004":
        # Check queue depth decreases > 20%
        verification_result = True
    elif runbook_id == "RB-005":
        # Check pg_isready, health checks, connection logs
        verification_result = True
    elif runbook_id == "RB-006":
        # Check queue depth < 100, consumer lag < 30s
        verification_result = True
    else:
        verification_result = False

    state["verification_result"] = verification_result
    if verification_result:
        state["recovery_confirmed"] = True
        state["status"] = "verifying"
        state["escalation_required"] = False
    else:
        state["recovery_confirmed"] = False
        state["status"] = "escalated"
        state["escalation_required"] = True

    return state


def generate_report(state: RunbookState) -> RunbookState:
    """Generate structured incident report for audit / SNS."""
    incident = state.get("incident_details", {})
    actions = ", ".join(state.get("actions_executed", []))
    verification = "PASSED" if state.get("verification_result") else "FAILED"
    escalation = "REQUIRED" if state.get("escalation_required") else "NOT REQUIRED"

    report_text = f"""
AuraCommerce Incident Report
-----------------------------
Incident Type: {incident.get('incident_type', 'Unknown')}
Affected Service: {incident.get('affected_service', 'Unknown')}
Severity: {incident.get('severity', 'Unknown')}
Runbook Executed: {state.get('runbook_id', 'None')}
Actions Taken: {actions}
Verification Result: {verification}
Recovery Confirmed: {'YES' if state.get('recovery_confirmed') else 'NO'}
Escalation: {escalation}
Agent Status: {state.get('status', 'unknown')}
-----------------------------
""".strip()

    state["report"] = report_text
    state["status"] = "completed"
    return state


def escalate(state: RunbookState) -> RunbookState:
    """Trigger human escalation via SNS / Slack / PagerDuty."""
    state["escalation_required"] = True
    state["status"] = "escalated"
    # Stub: Would trigger SNS topic, Slack webhook, or PagerDuty event
    # SNS_TOPIC = "escalation-topic"
    # SNS_MESSAGE = f"Runbook {state.get('runbook_id')} failed verification. Service: {state.get('incident_details', {}).get('affected_service')}"
    return state


# ------------------------------------------------------------------
# Graph Construction
# ------------------------------------------------------------------

graph = StateGraph(RunbookState)

graph.add_node("load_runbook", load_runbook)
graph.add_node("validate_conditions", validate_conditions)
graph.add_node("execute_remediation", execute_remediation)
graph.add_node("verify_recovery", verify_recovery)
graph.add_node("generate_report", generate_report)
graph.add_node("escalate", escalate)

graph.set_entry_point("load_runbook")

graph.add_edge("load_runbook", "validate_conditions")
graph.add_edge("validate_conditions", "execute_remediation")
graph.add_edge("execute_remediation", "verify_recovery")

graph.add_conditional_edges(
    "verify_recovery",
    lambda s: "escalate" if s.get("escalation_required") else "generate_report",
    {"generate_report": "generate_report", "escalate": "escalate"}
)

graph.add_edge("generate_report", END)
graph.add_edge("escalate", END)

app_runbook = graph.compile()

if __name__ == "__main__":
    initial_state = {
        "runbook_id": "RB-001",
        "incident_details": {
            "incident_type": "POD_FAILURE",
            "affected_service": "payment-service",
            "severity": "P1"
        },
        "conditions_met": [],
        "actions_executed": [],
        "verification_result": None,
        "recovery_confirmed": False,
        "escalation_required": False,
        "report": None,
        "status": "loading"
    }
    result = app_runbook.invoke(initial_state)
    print("Runbook Agent Result:")
    print(f"  Runbook: {result.get('runbook_id')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Actions: {result.get('actions_executed', [])}")
    print(f"  Verification: {result.get('verification_result')}")
    print(f"  Escalation: {result.get('escalation_required')}")
    print(f"  Report Snippet: {result.get('report', '')[:200]}...")
