from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)

class CartItemResponse(CartItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    added_at: datetime
    product_name: Optional[str] = None
    product_price: Optional[Decimal] = None

class CartResponse(BaseModel):
    user_id: str
    items: List[CartItemResponse]
    total_items: int
    estimated_total: Decimal
