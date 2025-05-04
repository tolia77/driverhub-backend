from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from app.schemas.location import LocationCreate, LocationOut


class LogBreakBase(BaseModel):
    start_time: datetime
    end_time: datetime
    cost: float
    delivery_id: int


class LogBreakCreate(LogBreakBase):
    location: LocationCreate


class LogBreakUpdate(BaseModel):
    location: Optional[LocationCreate] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: Optional[float] = None
    delivery_id: Optional[int] = None


class LogBreakOut(LogBreakBase):
    id: int
    location: LocationOut
    model_config = ConfigDict(from_attributes=True)
