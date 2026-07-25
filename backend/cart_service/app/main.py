import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid

from backend.shared.database import get_db
from backend.shared.events import EventType, BaseEvent
from app.models import CartItem
from app.schemas import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cart Service", version="1.0.0", docs_url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "cart-service"}

@app.get("/cart/{user_id}", response_model=CartResponse, tags=["cart"])
def view_cart(user_id: str, db: Session = Depends(get_db)):
    items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    # In production, join with product service; here we simulate
    total_items = sum(i.quantity for i in items)
    estimated_total = sum(i.quantity * 25.99 for i in items)  # simulated price
    results = []
    for item in items:
        results.append(CartItemResponse(
            id=item.id,
            user_id=item.user_id,
            product_id=item.product_id,
            quantity=item.quantity,
            added_at=item.added_at,
            product_name="Demo Product",
            product_price=Decimal("25.99")
        ))
    return CartResponse(user_id=user_id, items=results, total_items=total_items, estimated_total=estimated_total)

@app.post("/cart/{user_id}/items", response_model=CartItemResponse, status_code=201, tags=["cart"])
def add_item(user_id: str, item: CartItemCreate, db: Session = Depends(get_db)):
    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == item.product_id
    ).first()
    if existing:
        existing.quantity += item.quantity
        db.commit()
        db.refresh(existing)
        return existing
    db_item = CartItem(user_id=user_id, **item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(f"Cart item added: user={user_id}, product={item.product_id}")
    return db_item

@app.put("/cart/{user_id}/items/{item_id}", response_model=CartItemResponse, tags=["cart"])
def update_quantity(user_id: str, item_id: uuid.UUID, update: CartItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db_item.quantity = update.quantity
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/cart/{user_id}/items/{item_id}", status_code=204, tags=["cart"])
def remove_item(user_id: str, item_id: uuid.UUID, db: Session = Depends(get_db)):
    db_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(db_item)
    db.commit()
    return None

@app.delete("/cart/{user_id}", status_code=204, tags=["cart"])
def clear_cart(user_id: str, db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    return None
