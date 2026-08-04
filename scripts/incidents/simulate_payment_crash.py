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
        resp = requests.post(RUNBOOK_RUNNER_URL, json=payload, timeout=15)
        print(f"[INCIDENT] Alert sent. Runbook Runner response (HTTP {resp.status_code}):")
        res_data = resp.json()
        print(json.dumps(res_data, indent=2))

        # If asynchronous processing (HTTP 202), poll status endpoint until completion
        if resp.status_code == 202 or res_data.get("statusCode") == 202:
            incident_id = res_data.get("incident_id")
            status_url = f"http://localhost:8000/execute/{incident_id}/status"
            print(f"\n[INCIDENT] Polling execution status at {status_url}...")

            for _ in range(60):
                time.sleep(2)
                st_resp = requests.get(status_url, timeout=10)
                if st_resp.status_code == 200:
                    st_data = st_resp.json()
                    st = st_data.get("status")
                    print(f"   --> Current Status: {st} (Attempts: {st_data.get('attempts', 0)})")
                    if st in ("completed", "escalated", "error"):
                        print("\n[INCIDENT] Final Workflow Result:")
                        print(json.dumps(st_data, indent=2))
                        break
    except Exception as exc:
        print(f"[INCIDENT] Could not reach Runbook Runner at {RUNBOOK_RUNNER_URL}: {exc}")


if __name__ == "__main__":
    simulate_payment_crash()
