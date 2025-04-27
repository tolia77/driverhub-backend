from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.vehicle import VehicleRead


class DriverBase(BaseModel):
    license_number: str


class DriverCreate(UserCreate, DriverBase):
    vehicle_id: Optional[int] = None


class DriverRead(UserRead, DriverBase):
    vehicle_id: Optional[int] = None
    vehicle: Optional[VehicleRead] = None

    model_config = ConfigDict(from_attributes=True)


class DriverUpdate(UserUpdate):
    license_number: Optional[str] = None
    vehicle_id: Optional[int] = None