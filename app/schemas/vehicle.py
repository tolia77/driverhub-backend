from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class VehicleBase(BaseModel):
    model: str
    license_plate: str
    capacity: int
    mileage: int
    maintenance_due_date: Optional[date] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleRead(VehicleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class VehicleUpdate(BaseModel):
    model: Optional[str] = None
    license_plate: Optional[str] = None
    capacity: Optional[int] = None
    mileage: Optional[int] = None
    maintenance_due_date: Optional[date] = None
