#!/usr/bin/env python3
"""
Runbook Runner FastAPI Service
Async HTTP service providing alert ingestion, LLM classification, LangGraph state machine orchestration, and MCP tool execution.
"""
import os
import sys
import json
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add ai-agents to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "ai-agents"))
sys.path.insert(0, os.path.join(BASE_DIR, "ai-agents", "langgraph"))

from catalog_parser import catalog
from runbook_agent import run_runbook_agent

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Runbook Runner Service",
    description="FastAPI Service for Automated Incident Management via LangGraph & MCP",
    version="3.0.0"
)


class AlertPayload(BaseModel):
    event_type: str
    service: str
    runbook_id: Optional[str] = None
    alert_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@app.get("/health", tags=["health"])
async def health_check():
    """Service health status and active configurations."""
    return {
        "status": "healthy",
        "service": "runbook-runner",
        "mode": "langgraph-mcp-fastapi",
        "dry_run": os.getenv("K8S_DRY_RUN", "false").lower() in ("true", "1", "yes"),
        "catalog_size": len(catalog.list_runbooks())
    }


from mcp_client import mcp_client


class MCPToolCall(BaseModel):
    server: str = "kubernetes"
    tool_name: str = "get_pod_status"
    arguments: Optional[Dict[str, Any]] = {"pod_name": "payment-service"}


@app.get("/runbooks", tags=["catalog"])
async def list_runbooks():
    """List all available runbooks from the catalog."""
    return {
        "count": len(catalog.list_runbooks()),
        "runbooks": catalog.list_runbooks()
    }


@app.get("/mcp/tools", tags=["mcp-testing"])
async def list_mcp_tools():
    """List all registered FastMCP tools across Kubernetes & Jira MCP servers."""
    return {
        "mcp_servers": {
            "kubernetes": [
                {"name": "get_pod_logs", "description": "Retrieve stdout/stderr logs from a pod", "args": ["pod_name", "namespace"]},
                {"name": "rollout_restart", "description": "Trigger rolling restart of a deployment", "args": ["deployment", "namespace"]},
                {"name": "rollout_undo", "description": "Roll back deployment to previous revision", "args": ["deployment", "namespace"]},
                {"name": "scale_deployment", "description": "Scale deployment to target replicas", "args": ["deployment", "replicas", "namespace"]},
                {"name": "get_pod_status", "description": "Check pod status and readiness probes", "args": ["pod_name", "namespace"]}
            ],
            "jira": [
                {"name": "create_ticket", "description": "Create an incident ticket in Jira", "args": ["summary", "description", "issue_type", "priority"]},
                {"name": "get_ticket_status", "description": "Retrieve Jira ticket status by key", "args": ["ticket_key"]}
            ]
        }
    }


@app.post("/mcp/tools/call", tags=["mcp-testing"])
async def call_mcp_tool(request: MCPToolCall):
    """Interactively execute any FastMCP tool on Kubernetes or Jira servers over stdio."""
    try:
        res = await mcp_client.call_tool(
            server=request.server,
            tool_name=request.tool_name,
            arguments=request.arguments or {}
        )
        return {
            "status": "success",
            "server": request.server,
            "tool_name": request.tool_name,
            "result": res
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MCP Tool Execution Error: {exc}")


@app.post("/execute", tags=["execution"])
async def execute_runbook(alert: AlertPayload):
    """
    Ingest alert payload, perform LLM classification (if runbook_id is not specified),
    execute LangGraph state machine, perform MCP tool actions, verify recovery, and return execution report.
    """
    logger.info(f"RUNNER_SERVICE: Processing alert event '{alert.event_type}' for service '{alert.service}'")

    incident_details = alert.payload or {}
    if alert.alert_name:
        incident_details["alert_name"] = alert.alert_name

    try:
        result = await run_runbook_agent(
            event_type=alert.event_type,
            service=alert.service,
            runbook_id=alert.runbook_id,
            incident_details=incident_details
        )

        return {
            "statusCode": 200,
            "status": result.get("status"),
            "event_type": alert.event_type,
            "service": alert.service,
            "runbook_id": result.get("runbook_id"),
            "actions_executed": result.get("actions_executed", []),
            "verification_result": result.get("verification_result"),
            "attempts": result.get("attempts"),
            "recovery_confirmed": result.get("recovery_confirmed"),
            "escalation_required": result.get("escalation_required"),
            "jira_ticket": result.get("jira_ticket"),
            "result_summary": result
        }
    except Exception as exc:
        logger.error(f"RUNNER_SERVICE_ERROR: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
