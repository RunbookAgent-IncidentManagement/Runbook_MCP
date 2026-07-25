from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(gt=0)

class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID

class OrderCreate(BaseModel):
    user_id: str
    shipping_address: Optional[str] = None
    items: List[OrderItemBase]

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    status: str
    total_amount: Decimal
    shipping_address: Optional[str]
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]

class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|confirmed|shipped|delivered|cancelled)$")
