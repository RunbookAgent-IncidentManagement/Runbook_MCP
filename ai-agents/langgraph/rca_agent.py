"""
Agent 1: RCA Agent (Root Cause Analysis)
LangGraph StateGraph for AuraCommerce incident classification.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum
import os


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentCategory(str, Enum):
    POD_FAILURE = "POD_FAILURE"
    DEPLOYMENT_FAILURE = "DEPLOYMENT_FAILURE"
    HIGH_CPU = "HIGH_CPU"
    MEMORY_PRESSURE = "MEMORY_PRESSURE"
    SERVICE_DOWN = "SERVICE_DOWN"
    QUEUE_BACKLOG = "QUEUE_BACKLOG"
    DATABASE_CONNECTIVITY = "DATABASE_CONNECTIVITY"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


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
    status: str
    human_escalated: bool


# ------------------------------------------------------------------
# Tool Stubs (Production-ready interfaces)
# ------------------------------------------------------------------

def fetch_logs(state: RCAState) -> RCAState:
    """Tool: Query CloudWatch Logs Insights / kubectl logs."""
    state["logs"] = [
        "Simulated log: connection refused to db (postgres:5432)",
        "Simulated log: retry exhausted (3 attempts)",
        "Simulated log: liveness probe failed (timeout 1s)"
    ]
    return state


def analyze_metrics(state: RCAState) -> RCAState:
    """Tool: Prometheus / CloudWatch Metrics API."""
    state["metrics"] = {
        "cpu_percent": 92.5,
        "memory_percent": 88.1,
        "queue_depth": 1240,
        "error_rate_percent": 4.2
    }
    return state


def analyze_k8s_events(state: RCAState) -> RCAState:
    """Tool: kubectl get events --sort-by='.lastTimestamp'."""
    service = state.get("affected_service", "unknown")
    state["k8s_events"] = [
        f"Pod {service}-7d4b9f5 crashed (exit code 1)",
        "Liveness probe failed: timeout exceeded",
        "Back-off restarting failed container (pod healthy after 2 restarts)",
        "Deployment revision 2 (v2.0.0-broken) rolled out 14m ago"
    ]
    return state


def analyze_deployments(state: RCAState) -> RCAState:
    """Tool: kubectl rollout history deployment/{service}."""
    state["deployment_history"] = [
        "Revision 2 (v2.0.0-broken) — 14m ago",
        "Revision 1 (v1.9.2-stable) — 2h ago"
    ]
    return state


# ------------------------------------------------------------------
# LLM Nodes (Prompt-driven classification)
# ------------------------------------------------------------------

LLM_CLASSIFY_PROMPT = """
You are the AuraCommerce RCA Agent. Analyze the following incident signals and output ONLY a JSON object.

Signals:
- Alert: {alert_name} (service: {service})
- Logs: {logs}
- Metrics: {metrics}
- Kubernetes Events: {k8s_events}
- Deployment History: {deployment_history}

Incident Categories:
POD_FAILURE | DEPLOYMENT_FAILURE | HIGH_CPU | MEMORY_PRESSURE | SERVICE_DOWN | QUEUE_BACKLOG | DATABASE_CONNECTIVITY | CONFIGURATION_ERROR

Severity: P1 (critical), P2 (high), P3 (medium), P4 (low)

Output JSON:
{{
  "incident_category": "...",
  "severity": "...",
  "root_cause": "One sentence technical explanation",
  "confidence": 0.0-1.0,
  "recommended_runbook": "RB-001|RB-002|...|RB-006"
}}
""".strip()


def classify_incident(state: RCAState) -> RCAState:
    """LLM Node: Structured incident classification."""
    # In production this calls the LLM (OpenAI / Anthropic / local model)
    # Stubbed here with deterministic logic aligned to design spec
    service = state.get("affected_service", "unknown")
    metrics = state.get("metrics", {})
    events = state.get("k8s_events", [])
    deployments = state.get("deployment_history", [])

    # Deterministic classification logic (stubbed; real agent uses LLM)
    if any("crashed" in e.lower() or "liveness" in e.lower() for e in events):
        state["incident_category"] = IncidentCategory.POD_FAILURE.value
        state["severity"] = Severity.P1.value
        state["root_cause"] = "Pod crash loop due to misconfigured DB connection pool in new deployment."
        state["confidence"] = 0.94
        state["recommended_runbook"] = "RB-001"
    elif any("deployment" in e.lower() for e in events) and len(deployments) > 0:
        state["incident_category"] = IncidentCategory.DEPLOYMENT_FAILURE.value
        state["severity"] = Severity.P2.value
        state["root_cause"] = "New deployment revision introduces configuration error."
        state["confidence"] = 0.91
        state["recommended_runbook"] = "RB-002"
    elif metrics.get("cpu_percent", 0) > 70:
        state["incident_category"] = IncidentCategory.HIGH_CPU.value
        state["severity"] = Severity.P3.value
        state["root_cause"] = "CPU saturation caused by traffic spike."
        state["confidence"] = 0.85
        state["recommended_runbook"] = "RB-003"
    elif metrics.get("queue_depth", 0) > 500:
        state["incident_category"] = IncidentCategory.QUEUE_BACKLOG.value
        state["severity"] = Severity.P2.value
        state["root_cause"] = "Consumer lag exceeding processing capacity."
        state["confidence"] = 0.88
        state["recommended_runbook"] = "RB-006"
    else:
        state["incident_category"] = IncidentCategory.SERVICE_DOWN.value
        state["severity"] = Severity.P1.value
        state["root_cause"] = "Service unreachable; root cause requires deeper analysis."
        state["confidence"] = 0.65
        state["recommended_runbook"] = "RB-001"
    state["status"] = "classified"
    return state


def assign_severity(state: RCAState) -> RCAState:
    """Decision logic: severity mapping per design spec."""
    category = state.get("incident_category")
    if category == IncidentCategory.POD_FAILURE.value or category == IncidentCategory.DEPLOYMENT_FAILURE.value:
        # P1 for payment/db down; P2 for deployment failure
        service = state.get("affected_service", "")
        if service in ("payment-service", "auth-service", "database"):
            state["severity"] = Severity.P1.value
        else:
            state["severity"] = Severity.P2.value
    elif category == IncidentCategory.DATABASE_CONNECTIVITY.value or category == IncidentCategory.SERVICE_DOWN.value:
        state["severity"] = Severity.P1.value
    elif category == IncidentCategory.QUEUE_BACKLOG.value:
        state["severity"] = Severity.P2.value
    elif category in (IncidentCategory.HIGH_CPU.value, IncidentCategory.MEMORY_PRESSURE.value):
        state["severity"] = Severity.P3.value
    elif category == IncidentCategory.CONFIGURATION_ERROR.value:
        state["severity"] = Severity.P3.value
    else:
        state["severity"] = Severity.P4.value
    return state


def select_runbook(state: RCAState) -> RCAState:
    """Mapping dictionary: category → RB-ID."""
    mapping = {
        IncidentCategory.POD_FAILURE.value: "RB-001",
        IncidentCategory.DEPLOYMENT_FAILURE.value: "RB-002",
        IncidentCategory.HIGH_CPU.value: "RB-003",
        IncidentCategory.MEMORY_PRESSURE.value: "RB-003",
        IncidentCategory.SERVICE_DOWN.value: "RB-001",
        IncidentCategory.QUEUE_BACKLOG.value: "RB-006",
        IncidentCategory.DATABASE_CONNECTIVITY.value: "RB-005",
        IncidentCategory.CONFIGURATION_ERROR.value: "RB-006",
    }
    category = state.get("incident_category")
    state["recommended_runbook"] = mapping.get(category, "RB-001")
    state["status"] = "selected_runbook"
    return state


def escalate_or_complete(state: RCAState) -> RCAState:
    """Conditional: escalate if confidence < 0.7 or no runbook match."""
    confidence = state.get("confidence", 0.0)
    runbook = state.get("recommended_runbook")
    if confidence < 0.7 or not runbook:
        state["human_escalated"] = True
        state["status"] = "escalated"
        # Stub: Would trigger SNS / PagerDuty / Slack notification
        # SNS_TOPIC = "escalation-topic"
    else:
        state["status"] = "completed"
    return state


# ------------------------------------------------------------------
# Graph Construction
# ------------------------------------------------------------------

graph = StateGraph(RCAState)

graph.add_node("fetch_logs", fetch_logs)
graph.add_node("analyze_metrics", analyze_metrics)
graph.add_node("analyze_k8s_events", analyze_k8s_events)
graph.add_node("analyze_deployments", analyze_deployments)
graph.add_node("classify_incident", classify_incident)
graph.add_node("assign_severity", assign_severity)
graph.add_node("select_runbook", select_runbook)
graph.add_node("escalate_or_complete", escalate_or_complete)

graph.set_entry_point("fetch_logs")

graph.add_edge("fetch_logs", "analyze_metrics")
graph.add_edge("analyze_metrics", "analyze_k8s_events")
graph.add_edge("analyze_k8s_events", "analyze_deployments")
graph.add_edge("analyze_deployments", "classify_incident")
graph.add_edge("classify_incident", "assign_severity")
graph.add_edge("assign_severity", "select_runbook")
graph.add_edge("select_runbook", "escalate_or_complete")
graph.add_edge("escalate_or_complete", END)

app_rca = graph.compile()

if __name__ == "__main__":
    # Stubbed invocation for local testing
    initial_state = {
        "alert_id": "alert-001",
        "alert_name": "CloudWatch: payment-service-health-failed",
        "affected_service": "payment-service",
        "logs": [],
        "metrics": {},
        "k8s_events": [],
        "deployment_history": [],
        "incident_category": None,
        "severity": None,
        "root_cause": None,
        "confidence": 0.0,
        "recommended_runbook": None,
        "status": "analyzing",
        "human_escalated": False,
    }
    result = app_rca.invoke(initial_state)
    print("RCA Agent Result:", result)
