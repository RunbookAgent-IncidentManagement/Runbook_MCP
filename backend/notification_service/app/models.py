import uuid
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from backend.shared.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, server_default="pending")
    event_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
