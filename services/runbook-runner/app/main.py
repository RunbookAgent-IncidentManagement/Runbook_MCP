#!/usr/bin/env python3
"""
Runbook Runner Service — Free, Local, AWS Lambda-Free Replacement
Runs as a lightweight HTTP service (Flask/FastAPI) on the VM/Server
alongside the E-Commerce App (K3s) and the Alerting Agent.

Architecture (New, Free):
  K3s Cluster (AWS EC2)  →  Alerting Agent (CloudWatch webhook)  →  HTTP POST  →  This Service
  This Service  →  Hugging Face LLM (free inference API)  →  Local MCP Servers  →  kubectl / Jira REST
"""
import os
import json
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Runbook Runner Service (Free)", version="1.0.0")

# Local Kubernetes service names (same as Docker Compose / K8s)
RCA_AGENT_URL = os.getenv("RCA_AGENT_URL", "http://rca-agent-service:8000/analyze")
RUNBOOK_AGENT_URL = os.getenv("RUNBOOK_AGENT_URL", "http://runbook-agent-service:8001/execute")

# Hugging Face (free tier) endpoint reference
HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")  # Free tier uses optional token; set for higher rate limits


class AlertPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    service: Optional[str] = None
    alert_name: Optional[str] = None


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "runbook-runner", "mode": "free-local"}


@app.post("/execute", tags=["runbook"])
def execute_runbook(payload: AlertPayload):
    """
    Receives alerts directly (no Lambda, no SNS cost) and executes the agent pipeline.
    This replaces lambda_rca_trigger.py for the free architecture.
    """
    import requests
    logger.info(f"FREE_RUNNER: Received {payload.event_type} for service={payload.service}")

    # Step 1: Build RCA input from payload (free, no AWS Lambda needed)
    rca_input = {
        "alert_id": payload.payload.get("alert_id", "free-alert-001"),
        "alert_name": payload.alert_name or payload.event_type,
        "affected_service": payload.service or payload.payload.get("service", "unknown"),
        "logs": payload.payload.get("logs", []),
        "metrics": payload.payload.get("metrics", {}),
        "k8s_events": payload.payload.get("k8s_events", []),
        "deployment_history": payload.payload.get("deployment_history", []),
        "incident_category": payload.payload.get("incident_category"),
        "severity": payload.payload.get("severity"),
        "root_cause": None,
        "confidence": 0.0,
        "recommended_runbook": payload.payload.get("recommended_runbook"),
        "status": "analyzing",
        "human_escalated": False,
    }

    # Step 2: Call local RCA Agent (free, runs inside same VM/K3s)
    try:
        rca_resp = requests.post(RCA_AGENT_URL, json=rca_input, timeout=30, headers={"Content-Type": "application/json"})
        rca_result = rca_resp.json()
        logger.info(f"FREE_RUNNER: RCA result status={rca_result.get('status')}, category={rca_result.get('incident_category')}, confidence={rca_result.get('confidence')}, runbook={rca_result.get('recommended_runbook')}")
    except Exception as exc:
        logger.error(f"FREE_RUNNER: RCA call failed: {exc}")
        rca_result = {
            "incident_category": "SERVICE_DOWN",
            "severity": "P1",
            "recommended_runbook": "RB-001",
            "status": "escalated",
            "human_escalated": True,
            "confidence": 0.0,
            "root_cause": "RCA unreachable in free mode.",
        }

    # Step 3: If runbook selected, trigger Runbook Agent (free, local Kubernetes)
    runbook_result = None
    runbook_id = rca_result.get("recommended_runbook")
    confidence = rca_result.get("confidence", 0.0)
    escalated = rca_result.get("status") == "escalated" or rca_result.get("human_escalated", False)

    if runbook_id and confidence >= 0.7 and not escalated:
        try:
            rb_resp = requests.post(
                RUNBOOK_AGENT_URL,
                json={
                    "runbook_id": runbook_id,
                    "incident_details": rca_result,
                    "service": rca_result.get("affected_service"),
                },
                timeout=60,
                headers={"Content-Type": "application/json"},
            )
            runbook_result = rb_resp.json()
            logger.info(f"FREE_RUNNER: Runbook executed status={runbook_result.get('status')}, actions={runbook_result.get('actions_executed')}, verification={runbook_result.get('verification_result')}")
        except Exception as exc:
            logger.error(f"FREE_RUNNER: Runbook call failed: {exc}")
            escalated = True

    # Step 4: Free-mode audit (logs only — no SNS cost, no Lambda cost)
    audit = {
        "mode": "free-local",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "event_type": payload.event_type,
        "service": payload.service,
        "rca_result": rca_result,
        "runbook_triggered": runbook_id if (runbook_id and confidence >= 0.7 and not escalated) else None,
        "runbook_result": runbook_result,
        "escalated": escalated,
        "huggingface_api_url": HUGGINGFACE_API_URL,
    }
    logger.info(f"FREE_RUNNER_AUDIT: {json.dumps(audit)}")

    return {
        "statusCode": 200,
        "body": {
            "message": "Free local agent pipeline executed (no Lambda/SNS cost)",
            "event_type": payload.event_type,
            "service": payload.service,
            "rca_result": rca_result,
            "runbook_result": runbook_result,
            "escalated": escalated,
            "mode": "free-local",
            "huggingface_endpoint": HUGGINGFACE_API_URL,
        }
    }
