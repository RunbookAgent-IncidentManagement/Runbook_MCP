#!/usr/bin/env python3
"""
Jira MCP Server — FastMCP stdio protocol implementation.
Exposes Atlassian Jira issue creation and status queries over stdio transport.
Supports REST API integration with graceful mock fallback if token is unset.
"""
import os
import json
import sys
import urllib.request
import urllib.error

try:
    from fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:
            from mcp.server import FastMCP
        except ImportError as err:
            print(f"[WARN] Real FastMCP package not loaded ({err}). Using fallback shim.", file=sys.stderr)
            class FastMCP:
                def __init__(self, name):
                    self.name = name
                    self.tools = {}

                def tool(self, func=None):
                    def decorator(f):
                        self.tools[f.__name__] = f
                        return f
                    return decorator(func) if func else decorator

                def run(self, transport="stdio"):
                    print(f"[{self.name}] Running over {transport} (shim)", file=sys.stderr)

mcp = FastMCP("jira-mcp-server")

JIRA_URL = os.getenv("JIRA_URL", "https://your-domain.atlassian.net")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "devops@example.com")
DEFAULT_PROJECT = os.getenv("JIRA_PROJECT_KEY", "INC")


import base64

@mcp.tool()
def create_ticket(title: str, description: str, project_key: str = DEFAULT_PROJECT, issue_type: str = "Bug") -> str:
    """Create an incident or bug ticket in Jira."""
    # Real mode triggers when JIRA_TOKEN is provided and non-empty
    if not JIRA_TOKEN or JIRA_TOKEN == "atlassian_api_token_here":
        # Mock mode when real credentials are not configured
        mock_key = f"{project_key}-101"
        return json.dumps({
            "status": 201,
            "ticket_key": mock_key,
            "url": f"{JIRA_URL}/browse/{mock_key}",
            "title": title,
            "mode": "mock",
            "message": "Jira ticket created successfully in mock mode."
        })

    # Atlassian API v3 requires ADF (Atlassian Document Format) for description
    adf_description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description
                    }
                ]
            }
        ]
    }

    payload = json.dumps({
        "fields": {
            "project": {"key": project_key},
            "summary": title,
            "description": adf_description,
            "issuetype": {"name": issue_type},
        }
    }).encode("utf-8")
    
    # Atlassian Cloud REST API v3 requires Basic Auth with base64(email:token)
    auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_b64}"
    }

    try:
        req = urllib.request.Request(f"{JIRA_URL.rstrip('/')}/rest/api/3/issue", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return json.dumps({
                "status": resp.status,
                "ticket_key": data.get("key"),
                "url": f"{JIRA_URL.rstrip('/')}/browse/{data.get('key')}",
                "mode": "live"
            })
    except urllib.error.HTTPError as err:
        return json.dumps({"status": err.code, "error": err.read().decode("utf-8"), "mode": "live_error"})
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc), "mode": "fallback_error"})


@mcp.tool()
def get_ticket_status(ticket_key: str) -> str:
    """Retrieve current status of a specified Jira issue key."""
    if not JIRA_TOKEN or JIRA_TOKEN == "atlassian_api_token_here":
        return json.dumps({
            "ticket_key": ticket_key,
            "status": "In Progress",
            "assignee": "On-Call SRE",
            "mode": "mock"
        })

    auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    headers = {"Authorization": f"Basic {auth_b64}"}
    try:
        req = urllib.request.Request(f"{JIRA_URL.rstrip('/')}/rest/api/3/issue/{ticket_key}", headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            fields = data.get("fields", {})
            return json.dumps({
                "ticket_key": ticket_key,
                "status": fields.get("status", {}).get("name", "Unknown"),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned")
            })
    except Exception as exc:
        return json.dumps({"ticket_key": ticket_key, "error": str(exc)})


if __name__ == "__main__":
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        port = int(os.getenv("PORT", 8002))
        os.environ["FASTMCP_HOST"] = "0.0.0.0"
        os.environ["FASTMCP_PORT"] = str(port)
        print(f"🚀 Starting FastMCP Jira Web/SSE Server on http://0.0.0.0:{port}")
        try:
            mcp.settings.host = "0.0.0.0"
            mcp.settings.port = port
        except Exception:
            pass
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
