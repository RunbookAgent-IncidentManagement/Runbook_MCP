"""
AWS Lambda Trigger — RCA Agent Integration
Wires Amazon CloudWatch Alarms (via SNS) to the LangGraph RCA Agent.

Architecture:
CloudWatch Alarm → SNS Topic (`escalation-topic`) → Lambda (this file) → RCA Agent (`/analyze`) → Runbook Agent (`/execute`)

Environment Variables (deployment):
- RCA_AGENT_URL: http://rca-agent-service:8000/analyze
- RUNBOOK_AGENT_URL: http://runbook-agent-service:8001/execute
- SNS_TOPIC_ARN: arn:aws:sns:us-east-1:ACCOUNT:escalation-topic
- SNS_ALERT_TOPIC_ARN: arn:aws:sns:us-east-1:ACCOUNT:escalation-topic
"""
import os
import json
import logging
import requests

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Service endpoints (Docker Compose / Kubernetes service names)
RCA_AGENT_URL = os.getenv("RCA_AGENT_URL", "http://rca-agent-service:8000/analyze")
RUNBOOK_AGENT_URL = os.getenv("RUNBOOK_AGENT_URL", "http://runbook-agent-service:8001/execute")

# SNS Topic for escalation / audit
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:escalation-topic")


def lambda_handler(event: dict, context) -> dict:
    """
    Receives CloudWatch Alarm payload (via SNS) and triggers RCA Agent pipeline.

    Expected SNS Message Structure (CloudWatch Alarm):
    {
      "Message": "{...CloudWatch Alarm JSON...}",
      "TopicArn": "arn:aws:sns:..."
    }
    """
    logger.info(f"Lambda triggered by SNS event. TopicArn: {event.get('TopicArn')}")

    # Parse SNS envelope (CloudWatch Alarm format)
    sns_message = event.get("Message", "{}")
    try:
        alarm_payload = json.loads(sns_message) if isinstance(sns_message, str) else sns_message
    except json.JSONDecodeError:
        alarm_payload = sns_message

    # Extract alert details from CloudWatch Alarm payload
    alert_id = alarm_payload.get("AlarmName", "unknown-alarm")
    affected_service = alarm_payload.get("Trigger", {}).get("Dimensions", [{}])[0].get("value", "unknown-service")
    alarm_state = alarm_payload.get("NewStateValue", "ALARM")

    # Build RCA Agent input state
    rca_input = {
        "alert_id": alert_id,
        "alert_name": alarm_payload.get("AlarmName", "CloudWatch Alarm"),
        "affected_service": affected_service,
        "logs": [],
        "metrics": alarm_payload.get("Trigger", {}).get("MetricName", {}),
        "k8s_events": [],
        "deployment_history": [],
        "incident_category": None,
        "severity": None,
        "root_cause": None,
        "confidence": 0.0,
        "recommended_runbook": None,
        "status": "analyzing",
        "human_escalated": False,
    }

    # Call RCA Agent
    try:
        logger.info(f"Calling RCA Agent at {RCA_AGENT_URL}")
        rca_resp = requests.post(
            RCA_AGENT_URL,
            json=rca_input,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        rca_resp.raise_for_status()
        rca_result = rca_resp.json()
        logger.info(f"RCA Agent result: {rca_result.get('status')}, category: {rca_result.get('incident_category')}, severity: {rca_result.get('severity')}, confidence: {rca_result.get('confidence')}")
    except requests.RequestException as exc:
        logger.error(f"RCA Agent call failed: {exc}")
        # Fallback: escalate immediately
        rca_result = {
            "incident_category": "SERVICE_DOWN",
            "severity": "P1",
            "recommended_runbook": "RB-001",
            "status": "escalated",
            "human_escalated": True,
            "confidence": 0.0,
            "root_cause": "RCA Agent unreachable; manual investigation required.",
        }

    # If a runbook is selected and confidence is sufficient, trigger Runbook Agent
    runbook_id = rca_result.get("recommended_runbook")
    confidence = rca_result.get("confidence", 0.0)
    escalated = rca_result.get("status") == "escalated" or rca_result.get("human_escalated", False)

    if runbook_id and confidence >= 0.7 and not escalated:
        try:
            logger.info(f"Triggering Runbook Agent for {runbook_id}")
            runbook_resp = requests.post(
                RUNBOOK_AGENT_URL,
                json={
                    "runbook_id": runbook_id,
                    "incident_details": rca_result,
                    "service": rca_result.get("affected_service"),
                },
                timeout=60,
                headers={"Content-Type": "application/json"},
            )
            runbook_resp.raise_for_status()
            runbook_result = runbook_resp.json()
            logger.info(f"Runbook Agent executed: {runbook_result.get('status')}, actions: {runbook_result.get('actions_executed', [])}")
        except requests.RequestException as exc:
            logger.error(f"Runbook Agent call failed: {exc}")
            # If runbook fails, escalate via SNS
            escalated = True

    # Final escalation / audit reporting
    if escalated or confidence < 0.7:
        try:
            # In production: publish to SNS topic using boto3
            # sns_client = boto3.client("sns", region_name="us-east-1")
            # sns_client.publish(
            #     TopicArn=SNS_TOPIC_ARN,
            #     Message=json.dumps({"event": "escalation", "alert_id": alert_id, "service": affected_service, "runbook": runbook_id, "confidence": confidence, "reason": "low_confidence_or_agent_failure"}),
            #     Subject=f"[P{rca_result.get('severity', '1')}] AuraCommerce Incident Escalation: {alert_id}"
            # )
            logger.info(f"Escalation triggered for alert {alert_id}. SNS topic: {SNS_TOPIC_ARN}")
        except Exception as exc:
            logger.error(f"SNS escalation failed: {exc}")

    # Audit trail: log structured event (would go to S3 / OpenSearch in production)
    audit_entry = {
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "lambda_trigger": "cloudwatch_alarm_sns",
        "alert_id": alert_id,
        "affected_service": affected_service,
        "alarm_state": alarm_state,
        "rca_result": rca_result,
        "escalated": escalated,
        "sns_topic_arn": SNS_TOPIC_ARN,
    }
    logger.info(f"AUDIT: {json.dumps(audit_entry)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "RCA Agent pipeline executed",
            "alert_id": alert_id,
            "service": affected_service,
            "rca_result": rca_result,
            "runbook_triggered": runbook_id if (runbook_id and confidence >= 0.7 and not escalated) else None,
            "escalated": escalated,
            "audit_timestamp": audit_entry["timestamp"],
        })
    }


# ------------------------------------------------------------------
# SNS / EventBridge Connection Points (Reference / Stub)
# ------------------------------------------------------------------

SNS_TOPIC_CONFIG = {
    "TopicName": "escalation-topic",
    "DisplayName": "AuraCommerce Escalation",
    "TopicArn": SNS_TOPIC_ARN,
    "Subscriptions": [
        {
            "Protocol": "lambda",
            "Endpoint": "arn:aws:lambda:us-east-1:ACCOUNT:function:lambda_rca_trigger",
            "RawMessageDelivery": False,
        },
        {
            "Protocol": "email",
            "Endpoint": "sre-oncall@aura-commerce.local",
        },
        {
            "Protocol": "sms",
            "Endpoint": "+14155552671",
        }
    ],
}

EVENTBRIDGE_RULE_CONFIG = {
    "Name": "CloudWatchAlarmToRCA",
    "EventPattern": {
        "source": ["aws.cloudwatch"],
        "detail-type": ["CloudWatch Alarm State Change"],
        "detail": {
            "state": {
                "value": ["ALARM"]
            },
            "alarmName": [{
                "prefix": ""
            }]
        }
    },
    "Targets": [
        {
            "Arn": "arn:aws:lambda:us-east-1:ACCOUNT:function:lambda_rca_trigger",
            "Id": "RCA_Lambda_Target"
        }
    ]
}

# Local invocation stub for testing (without AWS Lambda runtime)
if __name__ == "__main__":
    # Simulated CloudWatch Alarm payload (as delivered via SNS)
    simulated_sns_event = {
        "TopicArn": SNS_TOPIC_ARN,
        "Message": json.dumps({
            "AlarmName": "payment-service-health-failed",
            "AlarmDescription": "Liveness probe failed",
            "NewStateValue": "ALARM",
            "Trigger": {
                "Dimensions": [
                    {"name": "ServiceName", "value": "payment-service"}
                ],
                "MetricName": "ContainerHealthCheckFailed"
            },
            "StateReason": "Threshold Crossed: 1 datapoint [92.5 (05/07/26 14:30:00)] was not between 1 and 0"
        }),
        "MessageId": "sim-msg-001",
        "Type": "Notification"
    }
    result = lambda_handler(simulated_sns_event, None)
    print("Lambda trigger result:")
    print(json.dumps(result, indent=2))
