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


from fastapi.responses import HTMLResponse


@app.get("/mcp-ui", response_class=HTMLResponse, tags=["mcp-testing"])
async def mcp_inspector_ui():
    """Interactive Web Inspector Console for testing FastMCP Kubernetes & Jira tools."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FastMCP Interactive Developer Inspector</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --panel-bg: #1e293b;
            --border-color: #334155;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        header {
            background-color: var(--panel-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 1.25rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        header h1 { font-size: 1.25rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 0.5rem; }
        header span { font-size: 0.85rem; background: rgba(99, 102, 241, 0.2); color: #818cf8; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; }
        main {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 1.5rem;
            padding: 1.5rem;
            flex: 1;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }
        .card {
            background-color: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }
        .card-title { font-size: 1rem; font-weight: 600; color: var(--text-main); border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 0.5rem; }
        label { font-size: 0.85rem; font-weight: 500; color: var(--text-muted); display: block; margin-bottom: 0.35rem; }
        select, input, textarea {
            width: 100%;
            background-color: #0f172a;
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 0.65rem 0.85rem;
            border-radius: 0.5rem;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
        }
        select:focus, input:focus, textarea:focus { outline: none; border-color: var(--primary); }
        .preset-btn-group { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .preset-btn {
            background-color: #334155;
            color: #e2e8f0;
            border: none;
            padding: 0.4rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .preset-btn:hover { background-color: var(--primary); color: #fff; }
        .btn-submit {
            background-color: var(--primary);
            color: #fff;
            border: none;
            padding: 0.75rem 1.25rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.95rem;
            transition: background-color 0.2s ease;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
        }
        .btn-submit:hover { background-color: var(--primary-hover); }
        .output-header { display: flex; justify-content: space-between; align-items: center; }
        .status-badge { font-size: 0.8rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 0.25rem; background-color: #334155; color: #94a3b8; }
        .status-badge.success { background-color: rgba(16, 185, 129, 0.2); color: #34d399; }
        .status-badge.error { background-color: rgba(239, 68, 68, 0.2); color: #f87171; }
        pre {
            background-color: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1.25rem;
            overflow-x: auto;
            color: #38bdf8;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            flex: 1;
            min-height: 350px;
        }
    </style>
</head>
<body>
    <header>
        <h1>⚡ FastMCP Developer Inspector Console</h1>
        <span>Stdio / FastMCP Direct Web Protocol</span>
    </header>
    <main>
        <div class="card">
            <div class="card-title">MCP Tool Controls</div>
            
            <div>
                <label for="server">Select MCP Server</label>
                <select id="server" onchange="onServerChange()">
                    <option value="kubernetes">Kubernetes MCP Server (mcp-servers/kubernetes_mcp_server.py)</option>
                    <option value="jira">Jira MCP Server (mcp-servers/jira_mcp_server.py)</option>
                </select>
            </div>

            <div>
                <label>Preset Tool Quick Action</label>
                <div class="preset-btn-group" id="preset-buttons">
                    <!-- Populated dynamically -->
                </div>
            </div>

            <div>
                <label for="tool_name">MCP Tool Name</label>
                <input type="text" id="tool_name" value="get_pod_status">
            </div>

            <div>
                <label for="arguments">JSON Tool Arguments</label>
                <textarea id="arguments" rows="6">{\n  "pod_name": "payment-service"\n}</textarea>
            </div>

            <button class="btn-submit" onclick="executeMCPTool()">
                🚀 Execute FastMCP Tool
            </button>
        </div>

        <div class="card">
            <div class="output-header">
                <div class="card-title" style="border:none; margin:0; padding:0;">Execution Response Output</div>
                <div class="status-badge" id="status-badge">Ready</div>
            </div>
            <pre id="output-json">// Result payload from FastMCP Stdio execution will appear here...</pre>
        </div>
    </main>

    <script>
        const PRESETS = {
            kubernetes: [
                { label: 'get_pod_status', name: 'get_pod_status', args: { pod_name: 'payment-service' } },
                { label: 'rollout_restart', name: 'rollout_restart', args: { deployment: 'payment-service' } },
                { label: 'rollout_undo', name: 'rollout_undo', args: { deployment: 'payment-service' } },
                { label: 'scale_deployment', name: 'scale_deployment', args: { deployment: 'payment-service', replicas: 3 } },
                { label: 'get_pod_logs', name: 'get_pod_logs', args: { pod_name: 'payment-service' } }
            ],
            jira: [
                { label: 'create_ticket', name: 'create_ticket', args: { title: 'P1 Incident: payment-service Down', description: 'Metaspace OOM error detected.' } },
                { label: 'get_ticket_status', name: 'get_ticket_status', args: { ticket_key: 'INC-101' } }
            ]
        };

        function onServerChange() {
            const server = document.getElementById('server').value;
            const container = document.getElementById('preset-buttons');
            container.innerHTML = '';
            
            PRESETS[server].forEach(preset => {
                const btn = document.createElement('button');
                btn.className = 'preset-btn';
                btn.innerText = preset.label;
                btn.onclick = () => {
                    document.getElementById('tool_name').value = preset.name;
                    document.getElementById('arguments').value = JSON.stringify(preset.args, null, 2);
                };
                container.appendChild(btn);
            });

            // Set initial preset
            if (PRESETS[server].length > 0) {
                document.getElementById('tool_name').value = PRESETS[server][0].name;
                document.getElementById('arguments').value = JSON.stringify(PRESETS[server][0].args, null, 2);
            }
        }

        async function executeMCPTool() {
            const server = document.getElementById('server').value;
            const tool_name = document.getElementById('tool_name').value.trim();
            const rawArgs = document.getElementById('arguments').value.trim();
            const outputPre = document.getElementById('output-json');
            const badge = document.getElementById('status-badge');

            let parsedArgs = {};
            try {
                parsedArgs = rawArgs ? JSON.parse(rawArgs) : {};
            } catch (err) {
                badge.innerText = 'JSON Error';
                badge.className = 'status-badge error';
                outputPre.innerText = 'Invalid JSON in Tool Arguments: ' + err.message;
                return;
            }

            badge.innerText = 'Executing...';
            badge.className = 'status-badge';
            outputPre.innerText = '// Sending JSON-RPC request to FastMCP Stdio process...';

            try {
                const resp = await fetch('/mcp/tools/call', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        server: server,
                        tool_name: tool_name,
                        arguments: parsedArgs
                    })
                });

                const data = await resp.json();
                if (resp.ok) {
                    badge.innerText = 'Success (200 OK)';
                    badge.className = 'status-badge success';
                } else {
                    badge.innerText = 'Error (' + resp.status + ')';
                    badge.className = 'status-badge error';
                }
                outputPre.innerText = JSON.stringify(data, null, 2);
            } catch (err) {
                badge.innerText = 'Network Error';
                badge.className = 'status-badge error';
                outputPre.innerText = 'Failed to execute tool: ' + err.message;
            }
        }

        // Initialize default presets on load
        onServerChange();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


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
