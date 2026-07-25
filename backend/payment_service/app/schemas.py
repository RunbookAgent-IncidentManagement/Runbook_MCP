from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class PaymentCreate(BaseModel):
    order_id: UUID
    amount: Decimal = Field(gt=0)

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    amount: Decimal
    status: str
    transaction_ref: Optional[str]
    created_at: datetime
