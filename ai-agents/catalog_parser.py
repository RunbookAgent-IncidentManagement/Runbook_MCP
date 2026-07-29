#!/usr/bin/env python3
"""
Catalog Parser Module
Parses Markdown documentation (`runbook_catalog.md`) and declarative YAML specifications (`runbook_actions.yaml`).
"""
import os
import json
from typing import Dict, Any, Optional

YAML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "runbooks", "runbook_actions.yaml"))
MARKDOWN_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "langgraph", "runbook_catalog.md"))


class RunbookCatalog:
    """Provides structured access to Runbook definitions and tool action mappings."""

    def __init__(self, yaml_path: str = YAML_PATH):
        self.yaml_path = yaml_path
        self._catalog: Dict[str, Any] = {}
        self.load_catalog()

    def load_catalog(self):
        try:
            import yaml
            if os.path.exists(self.yaml_path):
                with open(self.yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self._catalog = data.get("runbooks", {})
                    return
        except ImportError:
            pass

        # Fallback catalog if pyyaml is not installed
        self._catalog = self._get_fallback_catalog()

    def get_runbook(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        return self._catalog.get(runbook_id.upper())

    def list_runbooks(self) -> Dict[str, Any]:
        return self._catalog

    def _get_fallback_catalog(self) -> Dict[str, Any]:
        return {
            "RB-001": {
                "id": "RB-001",
                "name": "Restart Deployment",
                "category": "POD_FAILURE",
                "severity": "P1",
                "description": "Triggers rolling restart of unhealthy microservice deployment pods.",
                "tool_call": {"server": "kubernetes", "name": "rollout_restart", "arguments": {"deployment": "{service}"}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "{service}"}}, "expected_healthy": True},
                "max_attempts": 2,
                "fallback_runbook": "RB-002",
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "P1 Incident Unresolved: {service} Pod CrashLoop (RB-001 Failed)", "description": "Automated restart of deployment {service} failed after 2 attempts. Escalating for manual investigation."}}
            },
            "RB-002": {
                "id": "RB-002",
                "name": "Rollback Deployment",
                "category": "DEPLOYMENT_FAILURE",
                "severity": "P2",
                "description": "Rolls back deployment to previous stable revision.",
                "tool_call": {"server": "kubernetes", "name": "rollout_undo", "arguments": {"deployment": "{service}"}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "{service}"}}, "expected_healthy": True},
                "max_attempts": 2,
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "P2 Incident Unresolved: {service} Rollback Failed (RB-002)", "description": "Rollback of deployment {service} failed to restore service health."}}
            },
            "RB-003": {
                "id": "RB-003",
                "name": "Scale Service",
                "category": "HIGH_CPU",
                "severity": "P3",
                "description": "Scales deployment to 6 replicas to handle CPU/memory saturation.",
                "tool_call": {"server": "kubernetes", "name": "scale_deployment", "arguments": {"deployment": "{service}", "replicas": 6}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "{service}"}}, "expected_healthy": True},
                "max_attempts": 2,
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "P3 Alert: {service} Scale Out Unsuccessful", "description": "Scaling service {service} to 6 replicas failed to resolve resource contention."}}
            },
            "RB-004": {
                "id": "RB-004",
                "name": "Restart Consumer",
                "category": "QUEUE_BACKLOG",
                "severity": "P2",
                "description": "Restarts consumer deployment to resume message processing.",
                "tool_call": {"server": "kubernetes", "name": "rollout_restart", "arguments": {"deployment": "{service}"}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "{service}"}}, "expected_healthy": True},
                "max_attempts": 2,
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "P2 Consumer Stall: {service} Restart Unsuccessful", "description": "Consumer service {service} restart did not clear backlog."}}
            },
            "RB-005": {
                "id": "RB-005",
                "name": "Database Connectivity Recovery",
                "category": "DATABASE_CONNECTIVITY",
                "severity": "P1",
                "description": "Restarts database connection pool and postgres deployment.",
                "tool_call": {"server": "kubernetes", "name": "rollout_restart", "arguments": {"deployment": "postgres"}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "postgres"}}, "expected_healthy": True},
                "max_attempts": 2,
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "CRITICAL P1: Database Recovery Failed for {service}", "description": "Database pod restart failed to restore connectivity."}}
            },
            "RB-006": {
                "id": "RB-006",
                "name": "Queue Backlog Recovery",
                "category": "QUEUE_BACKLOG",
                "severity": "P2",
                "description": "Scales consumer workers to 4 replicas.",
                "tool_call": {"server": "kubernetes", "name": "scale_deployment", "arguments": {"deployment": "{service}", "replicas": 4}},
                "verification": {"tool_call": {"server": "kubernetes", "name": "get_pod_status", "arguments": {"pod_name": "{service}"}}, "expected_healthy": True},
                "max_attempts": 2,
                "escalation": {"server": "jira", "name": "create_ticket", "arguments": {"title": "P2 Queue Backlog: {service} Scale-Up Unresolved", "description": "Queue backlog recovery scaling failed for {service}."}}
            }
        }


# Global catalog singleton instance
catalog = RunbookCatalog()
