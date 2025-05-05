from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class LocationBase(BaseModel):
    latitude: float
    longitude: float


class LocationCreate(LocationBase):
    pass


class LocationOut(LocationBase):
    id: int
    created_at: datetime
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
