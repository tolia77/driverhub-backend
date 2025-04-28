from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LogBreakBase(BaseModel):
    location: str
    start_time: datetime
    end_time: datetime
    cost: float
    delivery_id: int


class LogBreakCreate(LogBreakBase):
    pass


class LogBreakUpdate(BaseModel):
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: Optional[float] = None
    delivery_id: Optional[int] = None


class LogBreakOut(LogBreakBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
