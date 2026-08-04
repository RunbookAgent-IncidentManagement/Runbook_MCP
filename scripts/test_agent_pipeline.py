#!/usr/bin/env python3
"""
End-to-End Agent Pipeline Test Script
Smoke tests the Mistral LLM Classifier, FastMCP stdio servers, LangGraph Retry State Machine,
Jira Escalation, and FORCE_UNHEALTHY simulation.
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

    # Enable K8S_DRY_RUN for offline test environment
    os.environ["K8S_DRY_RUN"] = "true"
    os.environ["ENABLE_RULE_FALLBACK"] = "true"
    # Use short polling for tests (3s × 1 poll = 3s instead of 30s)
    os.environ["VERIFY_TIMEOUT_SECONDS"] = "3"
    print(f"Environment: K8S_DRY_RUN=true, ENABLE_RULE_FALLBACK=true, VERIFY_TIMEOUT_SECONDS=3")

    passed = 0
    failed = 0

    # Step 1: Catalog Check
    runbooks = catalog.list_runbooks()
    print(f"\n[TEST 1] Runbook Catalog Loaded: {len(runbooks)} Runbooks ({', '.join(runbooks.keys())})")
    assert len(runbooks) == 6, f"Expected 6 runbooks, got {len(runbooks)}"
    passed += 1

    # Step 2: Mistral LLM Classifier Test — CrashLoopBackOff must map to RB-001
    print("\n[TEST 2] Testing Mistral LLM Classifier (CrashLoopBackOff → RB-001)...")
    classification = await classifier.classify(
        service="payment-service",
        event_type="CrashLoopBackOff",
        logs=["java.lang.OutOfMemoryError", "Connection refused"],
        k8s_events=["Liveness probe failed"]
    )
    print("   Output:", json.dumps(classification, indent=2))
    assert classification.get("runbook_id") == "RB-001", \
        f"Expected RB-001 for CrashLoopBackOff, got {classification.get('runbook_id')}"
    print("   ✅ Classification Test PASSED!")
    passed += 1

    # Step 3: FastMCP Tool Session Call Test
    print("\n[TEST 3] Testing FastMCP Tool Client (Kubernetes get_pod_status)...")
    pod_status = await mcp_client.call_tool("kubernetes", "get_pod_status", {"pod_name": "payment-service"})
    print("   Output:", json.dumps(pod_status, indent=2))
    assert pod_status.get("healthy") is True, f"Expected healthy=True in dry-run, got {pod_status.get('healthy')}"
    print("   ✅ FastMCP Kubernetes Tool PASSED!")
    passed += 1

    print("\n[TEST 4] Testing FastMCP Tool Client (Jira create_ticket)...")
    jira_res = await mcp_client.call_tool("jira", "create_ticket", {
        "title": "Smoke Test Ticket",
        "description": "Automated pipeline smoke test."
    })
    print("   Output:", json.dumps(jira_res, indent=2))
    assert jira_res.get("ticket_key") is not None, "Expected ticket_key in Jira response"
    print("   ✅ FastMCP Jira Tool PASSED!")
    passed += 1

    # Step 5: LangGraph Runbook Execution Flow Test (healthy scenario)
    print("\n[TEST 5] Executing LangGraph State Machine (healthy dry-run)...")
    os.environ.pop("FORCE_UNHEALTHY", None)  # Ensure healthy mode
    res = await run_runbook_agent(
        event_type="CrashLoopBackOff",
        service="payment-service",
        runbook_id=None,
        incident_details={
            "logs": ["OutOfMemoryError: Metaspace"],
            "k8s_events": ["Liveness probe failed"]
        }
    )

    print(f"\n  * Final Status:       {res.get('status')}")
    print(f"  * Runbook Selected:   {res.get('runbook_id')}")
    print(f"  * Total Attempts:     {res.get('attempts')}/{res.get('max_attempts')}")
    print(f"  * Recovery Confirmed: {res.get('recovery_confirmed')}")
    print(f"  * Escalation Req:     {res.get('escalation_required')}")

    assert res.get("status") == "completed", f"Expected completed, got {res.get('status')}"
    assert res.get("recovery_confirmed") is True, f"Expected recovery_confirmed=True, got {res.get('recovery_confirmed')}"
    assert res.get("escalation_required") is False, f"Expected escalation_required=False"
    print("   ✅ Healthy Workflow Test PASSED!")
    passed += 1

    # Step 6: Escalation Flow Test (FORCE_UNHEALTHY)
    print("\n[TEST 6] Executing LangGraph State Machine (FORCE_UNHEALTHY → escalation)...")
    os.environ["FORCE_UNHEALTHY"] = "true"
    esc_res = await run_runbook_agent(
        event_type="CrashLoopBackOff",
        service="payment-service",
        runbook_id="RB-001",
        incident_details={
            "logs": ["CrashLoopBackOff detected"],
            "k8s_events": ["Back-off restarting failed container"]
        }
    )

    print(f"\n  * Final Status:       {esc_res.get('status')}")
    print(f"  * Runbook Selected:   {esc_res.get('runbook_id')}")
    print(f"  * Total Attempts:     {esc_res.get('attempts')}/{esc_res.get('max_attempts')}")
    print(f"  * Recovery Confirmed: {esc_res.get('recovery_confirmed')}")
    print(f"  * Escalation Req:     {esc_res.get('escalation_required')}")
    if esc_res.get("jira_ticket"):
        ticket = esc_res.get("jira_ticket")
        print(f"  * Jira Ticket:        {ticket.get('ticket_key')} ({ticket.get('mode')})")

    assert esc_res.get("status") == "escalated", f"Expected escalated, got {esc_res.get('status')}"
    assert esc_res.get("escalation_required") is True, f"Expected escalation_required=True"
    assert esc_res.get("recovery_confirmed") is False, f"Expected recovery_confirmed=False"
    assert esc_res.get("jira_ticket") is not None, "Expected jira_ticket to be created"
    assert esc_res.get("jira_ticket", {}).get("ticket_key") is not None, "Expected ticket_key in jira_ticket"
    print("   ✅ Escalation Flow Test PASSED!")
    passed += 1

    # Cleanup
    os.environ.pop("FORCE_UNHEALTHY", None)

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {passed + failed} tests")
    print("=" * 70)
    if failed == 0:
        print("✅ ALL SMOKE TESTS PASSED SUCCESSFULLY!")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
