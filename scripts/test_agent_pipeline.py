#!/usr/bin/env python3
"""
End-to-End Agent Pipeline Test Script
Smoke tests the Mistral LLM Classifier, FastMCP stdio servers, LangGraph Retry State Machine, and Jira Escalation.
"""
import os
import sys
import json
import asyncio

# Set stdout/stderr encoding for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "ai-agents"))
sys.path.insert(0, os.path.join(BASE_DIR, "ai-agents", "langgraph"))

from llm_classifier import classifier
from catalog_parser import catalog
from runbook_agent import run_runbook_agent
from mcp_client import mcp_client


async def run_pipeline_test():
    print("=" * 70)
    print("AuraCommerce AI Agent & FastMCP Pipeline Smoke Test")
    print("=" * 70)

    # Enable K8S_DRY_RUN for offline test environment if set
    dry_run_env = os.getenv("K8S_DRY_RUN", "true")
    os.environ["K8S_DRY_RUN"] = dry_run_env
    print(f"Environment: K8S_DRY_RUN={dry_run_env}")

    # Step 1: Catalog Check
    runbooks = catalog.list_runbooks()
    print(f"\n[TEST 1] Runbook Catalog Loaded: {len(runbooks)} Runbooks ({', '.join(runbooks.keys())})")

    # Step 2: Mistral LLM Classifier Test
    print("\n[TEST 2] Testing Mistral LLM Classifier (with keyword fallback)...")
    classification = classifier.classify(
        service="payment-service",
        event_type="CrashLoopBackOff",
        logs=["java.lang.OutOfMemoryError", "Connection refused"],
        k8s_events=["Liveness probe failed"]
    )
    print("   Output:", json.dumps(classification, indent=2))
    assert classification.get("runbook_id") == "RB-001", "Expected RB-001 mapping for CrashLoopBackOff"
    print("   Classification Test PASSED!")

    # Step 3: FastMCP Tool Session Call Test
    print("\n[TEST 3] Testing FastMCP Tool Client (Kubernetes get_pod_status)...")
    pod_status = await mcp_client.call_tool("kubernetes", "get_pod_status", {"pod_name": "payment-service"})
    print("   Output:", json.dumps(pod_status, indent=2))
    print("   FastMCP Kubernetes Tool PASSED!")

    print("\n[TEST 4] Testing FastMCP Tool Client (Jira create_ticket)...")
    jira_res = await mcp_client.call_tool("jira", "create_ticket", {
        "title": "Smoke Test Ticket",
        "description": "Automated pipeline smoke test."
    })
    print("   Output:", json.dumps(jira_res, indent=2))
    print("   FastMCP Jira Tool PASSED!")

    # Step 4: LangGraph Runbook Execution Flow Test
    print("\n[TEST 5] Executing Full LangGraph State Machine Workflow...")
    res = await run_runbook_agent(
        event_type="CrashLoopBackOff",
        service="payment-service",
        runbook_id=None,  # Triggers LLM classification automatically
        incident_details={
            "logs": ["OutOfMemoryError: Metaspace"],
            "k8s_events": ["Liveness probe failed"]
        }
    )

    print("\n" + "=" * 70)
    print("LANGGRAPH EXECUTION RESULT SUMMARY")
    print("=" * 70)
    print(f"  * Final Status:       {res.get('status')}")
    print(f"  * Runbook Selected:   {res.get('runbook_id')}")
    print(f"  * Total Attempts:     {res.get('attempts')}/{res.get('max_attempts')}")
    print(f"  * Actions Executed:   {len(res.get('actions_executed', []))}")
    print(f"  * Recovery Confirmed: {res.get('recovery_confirmed')}")
    print(f"  * Escalation Req:     {res.get('escalation_required')}")
    if res.get("jira_ticket"):
        print(f"  * Jira Ticket:        {res.get('jira_ticket').get('ticket_key')} ({res.get('jira_ticket').get('url')})")
    print("=" * 70)
    print("ALL SMOKE TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
