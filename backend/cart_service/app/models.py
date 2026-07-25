import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Numeric
from sqlalchemy.dialects.postgresql import UUID
from backend.shared.database import Base

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, server_default="1")
    added_at = Column(DateTime, server_default=func.now())
