import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.shared.database import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, server_default="pending")
    total_amount = Column(Numeric(12, 2), nullable=False)
    shipping_address = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quantity = Column(String(10), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
