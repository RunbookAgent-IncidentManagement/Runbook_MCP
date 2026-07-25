import os
import logging
import random
import time
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from decimal import Decimal

from backend.shared.database import get_db
from backend.shared.events import EventType, BaseEvent
from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service", version="1.0.0", docs_url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "payment-service"}

@app.post("/payments/process", response_model=PaymentResponse, status_code=201, tags=["payments"])
def process_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    # Simulate payment processing with delay and random outcome
    time.sleep(0.5)
    # 95% success rate for demo
    is_success = random.random() > 0.05
    status = "completed" if is_success else "failed"
    transaction_ref = f"txn_{uuid.uuid4().hex[:16]}"
    if not is_success:
        transaction_ref = None
    db_payment = Payment(
        order_id=data.order_id,
        amount=data.amount,
        status=status,
        transaction_ref=transaction_ref
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    event_type = EventType.PAYMENT_PROCESSED if is_success else EventType.PAYMENT_FAILED
    event_payload = {
        "payment_id": str(db_payment.id),
        "order_id": str(data.order_id),
        "amount": float(data.amount),
        "status": status,
        "transaction_ref": transaction_ref
    }
    logger.info(f"EVENT_PUBLISHED: type={event_type.value}, payload={event_payload}")
    logger.info(f"PAYMENT_PROCESSED: payment_id={db_payment.id}, status={status}, order={data.order_id}")
    return PaymentResponse(
        id=db_payment.id,
        order_id=db_payment.order_id,
        amount=db_payment.amount,
        status=db_payment.status,
        transaction_ref=db_payment.transaction_ref,
        created_at=db_payment.created_at
    )

@app.get("/payments/{payment_id}", response_model=PaymentResponse, tags=["payments"])
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@app.get("/payments/order/{order_id}", response_model=Optional[PaymentResponse], tags=["payments"])
def get_payment_by_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        return None
    return payment
