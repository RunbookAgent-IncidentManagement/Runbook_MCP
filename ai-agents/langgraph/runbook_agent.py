#!/usr/bin/env python3
"""
LangGraph Runbook Agent State Machine
Orchestrates runbook execution with:
- LLM alert classification
- MCP tool execution (Kubernetes & Jira over stdio)
- Real pod health verification
- Retry handling loop (MAX_ATTEMPTS = 2)
- Escalation chain (fallback runbook or Jira ticket creation after 2 failures)
"""
import os
import sys
import json
import asyncio
import logging
from typing import TypedDict, Optional, List, Dict, Any

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    END = "__END__"

# Import local agent submodules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from catalog_parser import catalog
from llm_classifier import classifier
from mcp_client import mcp_client

logger = logging.getLogger(__name__)


class RunbookState(TypedDict):
    event_type: str
    service: str
    runbook_id: Optional[str]
    incident_details: Dict[str, Any]
    runbook_spec: Optional[Dict[str, Any]]
    actions_executed: List[Dict[str, Any]]
    verification_result: Optional[bool]
    attempts: int
    max_attempts: int
    recovery_confirmed: bool
    escalation_required: bool
    jira_ticket: Optional[Dict[str, Any]]
    status: str  # classifying | loading | executing | verifying | retrying | completed | escalated


# ------------------------------------------------------------------
# LangGraph Nodes (Async capable)
# ------------------------------------------------------------------

async def classify_alert(state: RunbookState) -> RunbookState:
    """Node: Use Mistral LLM (or keyword fallback) to classify alert to Runbook ID."""
    if state.get("runbook_id"):
        state["status"] = "classified"
        return state

    service = state.get("service", "unknown")
    event_type = state.get("event_type", "unknown")
    incident = state.get("incident_details", {})

    logs = incident.get("logs", [])
    k8s_events = incident.get("k8s_events", [])
    metrics = incident.get("metrics", {})

    llm_res = classifier.classify(service, event_type, logs, k8s_events, metrics)
    state["runbook_id"] = llm_res.get("runbook_id", "RB-001")
    state["incident_details"]["classification"] = llm_res
    state["status"] = "classified"
    logger.info(f"NODE classify_alert: Selected runbook {state['runbook_id']} via {llm_res.get('source')}")
    return state


async def load_runbook(state: RunbookState) -> RunbookState:
    """Node: Load runbook specification from declarative YAML catalog."""
    rb_id = state.get("runbook_id", "RB-001")
    spec = catalog.get_runbook(rb_id)
    if not spec:
        spec = catalog.get_runbook("RB-001")

    state["runbook_spec"] = spec
    state["max_attempts"] = spec.get("max_attempts", 2)
    state["status"] = "loaded"
    logger.info(f"NODE load_runbook: Loaded spec for {rb_id} (Max Attempts: {state['max_attempts']})")
    return state


async def execute_remediation(state: RunbookState) -> RunbookState:
    """Node: Execute remediation tool via MCP stdio server."""
    state["attempts"] = state.get("attempts", 0) + 1
    attempt_num = state["attempts"]
    spec = state.get("runbook_spec", {})
    service = state.get("service", "service")

    tool_spec = spec.get("tool_call", {})
    server = tool_spec.get("server", "kubernetes")
    tool_name = tool_spec.get("name", "rollout_restart")

    raw_args = tool_spec.get("arguments", {})
    args = {}
    for k, v in raw_args.items():
        if isinstance(v, str):
            args[k] = v.format(service=service)
        else:
            args[k] = v

    logger.info(f"NODE execute_remediation (Attempt {attempt_num}/{state['max_attempts']}): Invoking {server}.{tool_name} with {args}")
    tool_result = await mcp_client.call_tool(server, tool_name, args)

    actions = state.get("actions_executed", [])
    actions.append({
        "attempt": attempt_num,
        "server": server,
        "tool": tool_name,
        "args": args,
        "result": tool_result
    })
    state["actions_executed"] = actions
    state["status"] = "executing"
    return state


async def verify_recovery(state: RunbookState) -> RunbookState:
    """Node: Verify real pod health status through Kubernetes MCP tool."""
    service = state.get("service", "unknown")
    spec = state.get("runbook_spec", {})

    verify_spec = spec.get("verification", {}).get("tool_call", {})
    server = verify_spec.get("server", "kubernetes")
    tool_name = verify_spec.get("name", "get_pod_status")

    args = {"pod_name": service}

    # Wait 5 seconds to allow K3s pod rollout to initialize and complete probes
    await asyncio.sleep(5)

    logger.info(f"NODE verify_recovery: Invoking {server}.{tool_name} for pod={service}")
    verify_res = await mcp_client.call_tool(server, tool_name, args)

    is_healthy = bool(verify_res.get("healthy", False) or verify_res.get("dry_run", False))

    state["verification_result"] = is_healthy

    if is_healthy:
        state["recovery_confirmed"] = True
        state["escalation_required"] = False
        state["status"] = "completed"
        logger.info(f"NODE verify_recovery: Pod {service} verified HEALTHY.")
    else:
        state["recovery_confirmed"] = False
        state["status"] = "verifying_failed"
        logger.warning(f"NODE verify_recovery: Pod {service} verification FAILED (Attempt {state['attempts']}/{state['max_attempts']}).")

    return state


async def retry_or_escalate(state: RunbookState) -> RunbookState:
    """Node/Decision: Evaluate whether to retry remediation or escalate to Jira."""
    if state.get("recovery_confirmed"):
        state["status"] = "completed"
        return state

    attempts = state.get("attempts", 1)
    max_attempts = state.get("max_attempts", 2)

    if attempts < max_attempts:
        state["status"] = "retrying"
        logger.info(f"NODE retry_or_escalate: Retrying remediation ({attempts + 1}/{max_attempts})...")
        return state

    # Max attempts exhausted -> Escalate to Jira
    state["escalation_required"] = True
    state["status"] = "escalating"

    spec = state.get("runbook_spec", {})
    service = state.get("service", "unknown")
    escalation_spec = spec.get("escalation", {})

    server = escalation_spec.get("server", "jira")
    tool_name = escalation_spec.get("name", "create_ticket")

    raw_args = escalation_spec.get("arguments", {})
    args = {
        "title": raw_args.get("title", f"P1 Incident: {service} Recovery Failed").format(service=service),
        "description": raw_args.get("description", f"Automated runbook {state.get('runbook_id')} failed after {attempts} attempts.").format(service=service)
    }

    logger.info(f"NODE retry_or_escalate: Max retries ({attempts}/{max_attempts}) reached! Escalating to Jira...")
    jira_res = await mcp_client.call_tool(server, tool_name, args)
    state["jira_ticket"] = jira_res
    state["status"] = "escalated"
    return state


# ------------------------------------------------------------------
# Graph Construction & Fallback Pipeline Runner
# ------------------------------------------------------------------

if HAS_LANGGRAPH:
    graph = StateGraph(RunbookState)

    graph.add_node("classify_alert", classify_alert)
    graph.add_node("load_runbook", load_runbook)
    graph.add_node("execute_remediation", execute_remediation)
    graph.add_node("verify_recovery", verify_recovery)
    graph.add_node("retry_or_escalate", retry_or_escalate)

    graph.set_entry_point("classify_alert")

    graph.add_edge("classify_alert", "load_runbook")
    graph.add_edge("load_runbook", "execute_remediation")
    graph.add_edge("execute_remediation", "verify_recovery")
    graph.add_edge("verify_recovery", "retry_or_escalate")

    graph.add_conditional_edges(
        "retry_or_escalate",
        lambda s: "execute_remediation" if s.get("status") == "retrying" else END,
        {"execute_remediation": "execute_remediation", END: END}
    )

    app_runbook = graph.compile()


async def run_runbook_agent(event_type: str, service: str, runbook_id: Optional[str] = None, incident_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper entrypoint to invoke the Runbook Agent pipeline asynchronously."""
    initial_state: RunbookState = {
        "event_type": event_type,
        "service": service,
        "runbook_id": runbook_id,
        "incident_details": incident_details or {},
        "runbook_spec": None,
        "actions_executed": [],
        "verification_result": None,
        "attempts": 0,
        "max_attempts": 2,
        "recovery_confirmed": False,
        "escalation_required": False,
        "jira_ticket": None,
        "status": "starting"
    }

    if HAS_LANGGRAPH:
        return await app_runbook.ainvoke(initial_state)

    # Self-contained StateGraph fallback pipeline when langgraph package is not present
    state = initial_state
    state = await classify_alert(state)
    state = await load_runbook(state)

    while True:
        state = await execute_remediation(state)
        state = await verify_recovery(state)
        state = await retry_or_escalate(state)

        if state.get("status") != "retrying":
            break

    return state


if __name__ == "__main__":
    async def _test():
        res = await run_runbook_agent(
            event_type="CrashLoopBackOff",
            service="payment-service",
            runbook_id="RB-001",
            incident_details={"logs": ["OutOfMemoryError"]}
        )
        print("Runbook Agent Result:", json.dumps(res, indent=2))

    asyncio.run(_test())
