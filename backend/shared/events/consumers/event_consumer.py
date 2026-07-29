#!/usr/bin/env python3
"""
Concrete Event-Driven Wiring: SQS Consumer + EventBridge Integration
Connects business events (order.confirmed, payment.processed, incident.detected)
to the Runbook Agent pipeline via notification-service event endpoint.
"""
import json
import time
import requests

# Service endpoints (Docker Compose / Kubernetes internal network)
NOTIFICATION_SERVICE = "http://notification-service:8000"
ORDER_SERVICE = "http://order-service:8000"
PAYMENT_SERVICE = "http://payment-service:8000"
RUNBOOK_RUNNER = "http://runbook-runner:8000"

EVENT_TYPES = [
    "order.created",
    "order.confirmed",
    "payment.processed",
    "payment.failed",
    "incident.detected",
    "queue.backlog",
    "database.connectivity.failed",
    "deployment.failure",
]


def publish_event(event_type: str, payload: dict, source_service: str = "event-publisher"):
    """Publish event to notification service event consumer (SQS/EventBridge stub)."""
    event = {
        "event_type": event_type,
        "payload": payload,
        "source_service": source_service,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        resp = requests.post(
            f"{NOTIFICATION_SERVICE}/notifications/consume-event",
            json=event,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        result = resp.json()
        print(f"[EVENT_PUBLISHED] {event_type} -> notification-service -> {result.get('action')}")
        return result
    except Exception as exc:
        print(f"[EVENT_PUBLISH_ERROR] {event_type}: {exc}")
        return {"action": "failed", "error": str(exc)}


def simulate_order_flow():
    print("=== CONCRETE EVENT FLOW: Order -> Payment -> Inventory (stub) -> Notification ===")
    publish_event("order.created", {"order_id": "ORD-001", "user_id": "demo-user", "items": [{"product_id": "p1", "qty": 1}]}, "order-service")
    time.sleep(0.5)
    publish_event("order.confirmed", {"order_id": "ORD-001", "status": "confirmed", "total": 389.0}, "order-service")
    time.sleep(0.5)
    publish_event("payment.processed", {"order_id": "ORD-001", "amount": 389.0, "status": "success"}, "payment-service")
    time.sleep(0.5)
    # Incident event: deployment failure simulation for AI agent
    publish_event("incident.detected", {
        "service": "payment-service",
        "alert_name": "payment-service-health-failed",
        "runbook_id": "RB-001",
        "metrics": {"cpu_percent": 92.5, "memory_percent": 88.1},
        "k8s_events": ["Liveness probe failed", "Back-off restarting failed container"],
    }, "cloudwatch-alarm")


if __name__ == "__main__":
    print("Concrete event-driven wiring demonstration:")
    print(f"  Notification Service: {NOTIFICATION_SERVICE}")
    print(f"  Runbook Runner: {RUNBOOK_RUNNER}")
    print()
    simulate_order_flow()
    print()
    print("Event flow completed. Check notification-service logs for 'agent_pipeline_triggered' entries.")
