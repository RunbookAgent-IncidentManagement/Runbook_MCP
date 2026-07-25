import uuid
from sqlalchemy import Column, String, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from backend.shared.database import Base

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False, server_default="pending")
    transaction_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
