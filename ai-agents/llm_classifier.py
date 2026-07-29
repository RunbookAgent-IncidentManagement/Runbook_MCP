#!/usr/bin/env python3
"""
Hugging Face Mistral LLM Classifier Module
Classifies incident alert signals (logs, k8s events, metrics) into runbook IDs (RB-001 .. RB-006).
Uses HuggingFace Inference API with robust regex JSON parsing and keyword fallback.
"""
import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

HUGGINGFACE_API_URL = os.getenv(
    "HUGGINGFACE_API_URL",
    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
)
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

CLASSIFIER_PROMPT_TEMPLATE = """<s>[INST] You are an expert Site Reliability Engineer for AuraCommerce.
Classify the following incident alert into exact JSON output.

Available Runbooks in Catalog:
- RB-001: Pod CrashLoopBackOff or Liveness Probe failure (Action: Restart Deployment)
- RB-002: Deployment Revision failure or broken release (Action: Rollback Deployment)
- RB-003: High CPU or Memory Pressure saturation (Action: Scale Replicas to 6)
- RB-004: Consumer Stall or processing lag (Action: Restart Consumer)
- RB-005: Database Connection Refused or SQL failure (Action: Recover DB)
- RB-006: Queue Depth Backlog > 1000 messages (Action: Scale Consumer Workers)

Incident Alert Details:
- Affected Service: {service}
- Event Type / Category: {event_type}
- Log Snippets: {logs}
- Kubernetes Events: {k8s_events}
- Metrics: {metrics}

Output ONLY valid JSON matching this exact structure:
{{
  "runbook_id": "RB-001",
  "category": "POD_FAILURE",
  "severity": "P1",
  "confidence": 0.95,
  "reasoning": "Explanation here"
}} [/INST]"""


class HuggingFaceMistralClassifier:
    """Classifier utilizing Mistral-7B via Hugging Face API with deterministic fallbacks."""

    def __init__(self, api_url: str = HUGGINGFACE_API_URL, token: str = HUGGINGFACE_TOKEN):
        self.api_url = api_url
        self.token = token

    def classify(self, service: str, event_type: str, logs: list = None, k8s_events: list = None, metrics: dict = None) -> dict:
        logs = logs or []
        k8s_events = k8s_events or []
        metrics = metrics or {}

        # 1. Attempt LLM API Inference if token or URL is available
        prompt = CLASSIFIER_PROMPT_TEMPLATE.format(
            service=service,
            event_type=event_type,
            logs=", ".join(logs),
            k8s_events=", ".join(k8s_events),
            metrics=json.dumps(metrics)
        )

        headers = {"Content-Type": "application/json"}
        if self.token and not self.token.startswith("hf_demo"):
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            payload = json.dumps({
                "inputs": prompt,
                "parameters": {"max_new_tokens": 150, "temperature": 0.1, "return_full_text": False}
            }).encode("utf-8")

            req = urllib.request.Request(self.api_url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    raw_body = response.read().decode("utf-8")
                    data = json.loads(raw_body)
                    raw_text = ""
                    if isinstance(data, list) and len(data) > 0:
                        raw_text = data[0].get("generated_text", "")
                    elif isinstance(data, dict):
                        raw_text = data.get("generated_text", "")

                    parsed = self._extract_json(raw_text)
                    if parsed and "runbook_id" in parsed:
                        parsed["source"] = "mistral_llm"
                        return parsed
        except Exception as exc:
            logger.warning(f"LLM Inference API call skipped/failed: {exc}. Falling back to rule-based classification.")

        # 2. Deterministic Rule-Based Fallback Classifier
        return self._keyword_fallback(service, event_type, logs, k8s_events, metrics)

    def _extract_json(self, text: str) -> dict:
        """Extract first valid JSON object from LLM response text using regex."""
        try:
            match = re.search(r"\{.*?\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {}

    def _keyword_fallback(self, service: str, event_type: str, logs: list, k8s_events: list, metrics: dict) -> dict:
        combined_signals = (event_type + " " + " ".join(logs) + " " + " ".join(k8s_events)).lower()

        if "crashloop" in combined_signals or "liveness" in combined_signals or "pod_failure" in combined_signals:
            return {
                "runbook_id": "RB-001",
                "category": "POD_FAILURE",
                "severity": "P1",
                "confidence": 0.95,
                "reasoning": "Detected pod crash loop / probe failure.",
                "source": "rule_engine"
            }
        elif "deployment" in combined_signals or "undo" in combined_signals or "rollback" in combined_signals:
            return {
                "runbook_id": "RB-002",
                "category": "DEPLOYMENT_FAILURE",
                "severity": "P2",
                "confidence": 0.90,
                "reasoning": "Detected deployment revision error.",
                "source": "rule_engine"
            }
        elif "cpu" in combined_signals or "memory" in combined_signals or metrics.get("cpu_percent", 0) > 80:
            return {
                "runbook_id": "RB-003",
                "category": "HIGH_CPU",
                "severity": "P3",
                "confidence": 0.88,
                "reasoning": "High resource utilization threshold exceeded.",
                "source": "rule_engine"
            }
        elif "database" in combined_signals or "postgres" in combined_signals or "connection refused" in combined_signals:
            return {
                "runbook_id": "RB-005",
                "category": "DATABASE_CONNECTIVITY",
                "severity": "P1",
                "confidence": 0.92,
                "reasoning": "Database connection refused.",
                "source": "rule_engine"
            }
        elif "queue" in combined_signals or "backlog" in combined_signals or metrics.get("queue_depth", 0) > 500:
            return {
                "runbook_id": "RB-006",
                "category": "QUEUE_BACKLOG",
                "severity": "P2",
                "confidence": 0.91,
                "reasoning": "Consumer queue backlog exceeded.",
                "source": "rule_engine"
            }

        return {
            "runbook_id": "RB-001",
            "category": "SERVICE_DOWN",
            "severity": "P1",
            "confidence": 0.70,
            "reasoning": "Default runbook mapping for service incident.",
            "source": "rule_engine_default"
        }


classifier = HuggingFaceMistralClassifier()
