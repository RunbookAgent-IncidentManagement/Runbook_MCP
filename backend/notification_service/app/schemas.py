from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: str
    channel: str = Field(pattern="^(email|sms)$")
    subject: Optional[str] = None
    message: str
    event_reference: Optional[str] = None

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    channel: str
    subject: Optional[str]
    message: Optional[str]
    status: str
    event_reference: Optional[str]
    created_at: datetime
