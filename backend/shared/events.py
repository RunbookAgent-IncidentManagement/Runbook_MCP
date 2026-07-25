from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class EventType(str, Enum):
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    NOTIFICATION_SENT = "notification.sent"
    CART_UPDATED = "cart.updated"
    PRODUCT_UPDATED = "product.updated"
    QUEUE_BACKLOG = "queue.backlog"

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class OrderCreatedEvent(BaseEvent):
    event_type: EventType = EventType.ORDER_CREATED
    payload: Dict[str, Any]

class PaymentProcessedEvent(BaseEvent):
    event_type: EventType = EventType.PAYMENT_PROCESSED
    payload: Dict[str, Any]

class QueueBacklogEvent(BaseEvent):
    event_type: EventType = EventType.QUEUE_BACKLOG
    payload: Dict[str, Any]
