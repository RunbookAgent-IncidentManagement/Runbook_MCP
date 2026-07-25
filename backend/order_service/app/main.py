import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from decimal import Decimal

from backend.shared.database import get_db
from backend.shared.events import EventType, BaseEvent
from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderResponse, OrderStatusUpdate, OrderItemResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version="1.0.0", docs_url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "order-service"}

@app.post("/orders", response_model=OrderResponse, status_code=201, tags=["orders"])
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    total = sum(item.quantity * item.unit_price for item in order_data.items)
    db_order = Order(
        user_id=order_data.user_id,
        total_amount=total,
        shipping_address=order_data.shipping_address,
        status="pending"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    for item in order_data.items:
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(db_item)
    db.commit()
    # Publish event (simulated via log; in production publish to SQS/EventBridge)
    logger.info(f"ORDER_CREATED: order_id={db_order.id}, user={order_data.user_id}, total={total}")
    # Simulated event payload
    event_payload = {
        "order_id": str(db_order.id),
        "user_id": order_data.user_id,
        "total_amount": float(total),
        "items": [{"product_id": str(i.product_id), "quantity": i.quantity, "unit_price": float(i.unit_price)} for i in order_data.items]
    }
    logger.info(f"EVENT_PUBLISHED: type={EventType.ORDER_CREATED.value}, payload={event_payload}")
    return OrderResponse(
        id=db_order.id,
        user_id=db_order.user_id,
        status=db_order.status,
        total_amount=db_order.total_amount,
        shipping_address=db_order.shipping_address,
        created_at=db_order.created_at,
        items=[]
    )

@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["orders"])
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        items=[OrderItemResponse(id=i.id, order_id=i.order_id, product_id=i.product_id, quantity=int(i.quantity), unit_price=i.unit_price) for i in items],
        created_at=order.created_at
    )

@app.get("/orders/user/{user_id}", response_model=List[OrderResponse], tags=["orders"])
def get_user_orders(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    result = []
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        result.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            items=[OrderItemResponse(id=i.id, order_id=i.order_id, product_id=i.product_id, quantity=int(i.quantity), unit_price=i.unit_price) for i in items],
            created_at=order.created_at
        ))
    return result

@app.patch("/orders/{order_id}/status", response_model=OrderResponse, tags=["orders"])
def update_status(order_id: uuid.UUID, update: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = update.status
    db.commit()
    db.refresh(order)
    logger.info(f"ORDER_STATUS_UPDATED: order_id={order.id}, status={update.status}")
    return get_order(order_id, db=db)
