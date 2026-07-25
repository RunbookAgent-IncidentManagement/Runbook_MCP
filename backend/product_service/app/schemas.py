from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    sku: str = Field(..., max_length=100)
    image_url: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    status: str = Field(default="available", pattern="^(available|out_of_stock|discontinued)$")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(available|out_of_stock|discontinued)$")

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

class ProductSearchResponse(BaseModel):
    results: list[ProductResponse]
    total: int
    page: int
    limit: int
