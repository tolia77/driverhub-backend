from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.user import UserRead


class MessageBase(BaseModel):
    text: str
    sender_id: int
    receiver_id: Optional[int] = None


class MessageCreate(MessageBase):
    pass


class MessageShow(MessageBase):
    id: int
    created_at: datetime
    sender: Optional[UserRead] = None  # Basic user info
    receiver: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
