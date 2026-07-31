#!/usr/bin/env python3
"""
Incident Simulation: Payment Service CrashLoopBackOff (Direct Runbook Execution)
Sends an incident alert event payload to the Runbook Runner Service to trigger RB-001 (Restart Deployment).
"""
import requests
import time

RUNBOOK_RUNNER_URL = "http://localhost:8000/execute"


def simulate_payment_crash():
    print("[INCIDENT] Triggering CrashLoopBackOff alert payload for payment-service...")
    payload = {
        "event_type": "CrashLoopBackOff",
        "service": "payment-service",
        "payload": {
            "service": "payment-service",
            "alert_name": "payment-service-health-failed",
            "alert_id": f"incident-payment-{int(time.time())}",
            "metrics": {"cpu_percent": 94.2, "memory_percent": 89.0},
            "k8s_events": ["Liveness probe failed: HTTP 500", "Back-off restarting failed container"],
            "logs": ["java.lang.OutOfMemoryError: Metaspace", "Connection reset by peer"]
        }
    }

    try:
        resp = requests.post(RUNBOOK_RUNNER_URL, json=payload, timeout=10)
        print(f"[INCIDENT] Alert sent. Runbook Runner response (HTTP {resp.status_code}):")
        print(resp.json())
    except Exception as exc:
        print(f"[INCIDENT] Could not reach Runbook Runner at {RUNBOOK_RUNNER_URL}: {exc}")


if __name__ == "__main__":
    simulate_payment_crash()
