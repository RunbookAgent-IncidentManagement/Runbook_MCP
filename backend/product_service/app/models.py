from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.shared.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    sku = Column(String(100), nullable=False, unique=True, index=True)
    image_url = Column(String(500), nullable=True)
    stock_quantity = Column(Integer, nullable=False, server_default="0")
    status = Column(String(20), nullable=False, server_default="available")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
