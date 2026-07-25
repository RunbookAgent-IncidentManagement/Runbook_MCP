import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from backend.shared.database import get_db
from backend.shared.events import EventType, BaseEvent
from app.models import Notification
from app.schemas import NotificationCreate, NotificationResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0", docs_url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/notifications/send", response_model=NotificationResponse, status_code=201, tags=["notifications"])
def send_notification(data: NotificationCreate, db: Session = Depends(get_db)):
    # Simulate sending notification (email/SMS via SNS or external provider)
    notification = Notification(
        user_id=data.user_id,
        channel=data.channel,
        subject=data.subject,
        message=data.message,
        status="sent",
        event_reference=data.event_reference
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    logger.info(f"NOTIFICATION_SENT: user={data.user_id}, channel={data.channel}, event_ref={data.event_reference}")
    event_payload = {
        "notification_id": str(notification.id),
        "user_id": data.user_id,
        "channel": data.channel,
        "status": "sent"
    }
    logger.info(f"EVENT_PUBLISHED: type={EventType.NOTIFICATION_SENT.value}, payload={event_payload}")
    return notification

@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse], tags=["notifications"])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return notifications

@app.post("/notifications/consume-event", tags=["notifications"])
def consume_business_event(event: dict):
    # In production, consume from SQS/EventBridge
    logger.info(f"EVENT_CONSUMED: {event.get('event_type')} - {event.get('payload')}")

    # Concrete event wiring: trigger AI Agent pipeline for incident events
    event_type = event.get("event_type", "")
    payload = event.get("payload", {})

    # Wire to RCA Agent for incident detection events
    if event_type in ("incident.detected", "cloudwatch.alarm.triggered", "k8s.event.failure"):
        service = payload.get("service", "unknown")
        alert_name = payload.get("alert_name", "unknown-alert")
        # Call RCA Agent endpoint (local Kubernetes service / Lambda trigger)
        import requests
        try:
            rca_payload = {
                "alert_id": payload.get("alert_id", str(uuid.uuid4())),
                "alert_name": alert_name,
                "affected_service": service,
                "logs": payload.get("logs", []),
                "metrics": payload.get("metrics", {}),
                "k8s_events": payload.get("k8s_events", []),
                "deployment_history": payload.get("deployment_history", []),
                "incident_category": None,
                "severity": None,
                "root_cause": None,
                "confidence": 0.0,
                "recommended_runbook": None,
                "status": "analyzing",
                "human_escalated": False,
            }
            # Local Kubernetes endpoint (Docker Compose / EKS)
            resp = requests.post(
                "http://rca-agent-service:8000/analyze",
                json=rca_payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            rca_result = resp.json()
            logger.info(f"RCA_AGENT_RESULT: status={rca_result.get('status')}, category={rca_result.get('incident_category')}, severity={rca_result.get('severity')}, confidence={rca_result.get('confidence')}, runbook={rca_result.get('recommended_runbook')}")
            # If runbook recommended and confidence sufficient, trigger Runbook Agent
            runbook_id = rca_result.get("recommended_runbook")
            confidence = rca_result.get("confidence", 0.0)
            if runbook_id and confidence >= 0.7 and rca_result.get("status") != "escalated":
                try:
                    rb_resp = requests.post(
                        "http://runbook-agent-service:8001/execute",
                        json={
                            "runbook_id": runbook_id,
                            "incident_details": rca_result,
                            "service": service,
                        },
                        timeout=60,
                        headers={"Content-Type": "application/json"},
                    )
                    rb_result = rb_resp.json()
                    logger.info(f"RUNBOOK_AGENT_RESULT: status={rb_result.get('status')}, actions={rb_result.get('actions_executed', [])}, verification={rb_result.get('verification_result')}, escalated={rb_result.get('escalation_required')}")
                except Exception as exc:
                    logger.error(f"RUNBOOK_AGENT_CALL_FAILED: {exc}")
        except Exception as exc:
            logger.error(f"RCA_AGENT_CALL_FAILED: {exc}")
        return {
            "action": "agent_pipeline_triggered",
            "event_type": event_type,
            "service": service,
            "alert_name": alert_name,
        }

    # Trigger notification based on standard business event types
    if event_type == "order.confirmed" and payload.get("user_id"):
        return {"action": "notification_triggered", "type": "order_confirmed"}
    return {"action": "acknowledged", "event_type": event_type}
