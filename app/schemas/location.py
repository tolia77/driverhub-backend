from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class LocationBase(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationOut(LocationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
