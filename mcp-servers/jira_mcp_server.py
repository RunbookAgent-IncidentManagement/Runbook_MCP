#!/usr/bin/env python3
"""
Local Jira MCP Server (Free Mode)
Runs as a background sub-process managed by LangGraph Python script.
Uses environment variables for Atlassian URL and API token (free tier / self-hosted).
"""
import os
import requests

JIRA_URL = os.getenv("JIRA_URL", "https://your-domain.atlassian.net")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")


def create_ticket(title: str, description: str, project_key: str = "INC") -> dict:
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": title,
            "description": description,
            "issuetype": {"name": "Bug"},
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JIRA_TOKEN}" if JIRA_TOKEN else "Basic dummy",
    }
    try:
        resp = requests.post(f"{JIRA_URL}/rest/api/3/issue", json=payload, headers=headers, timeout=15)
        return {"status": resp.status_code, "ticket_key": resp.json().get("key"), "url": resp.json().get("self")}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "free_mode_note": "Using environment variables; no real Jira call made if variables missing."}


if __name__ == "__main__":
    print("Jira MCP Server (Free Mode) — Ready. JIRA_URL:", JIRA_URL)
