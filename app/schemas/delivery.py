from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.client import ClientOut
from app.schemas.driver import DriverRead
from app.schemas.location import LocationCreate, LocationOut
from app.schemas.review import ReviewRead


class DeliveryStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In-Transit"
    DELIVERED = "Delivered"
    FAILED = "Failed"


class DeliveryBase(BaseModel):
    driver_id: Optional[int] = None
    client_id: Optional[int] = None
    package_details: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    delivery_notes: Optional[str] = None


class DeliveryCreate(DeliveryBase):
    pickup_location: LocationCreate
    dropoff_location: LocationCreate


class DeliveryUpdate(BaseModel):
    driver_id: Optional[int] = None
    client_id: Optional[int] = None
    pickup_location: Optional[LocationCreate] = None
    dropoff_location: Optional[LocationCreate] = None
    package_details: Optional[str] = None
    status: Optional[DeliveryStatus] = None
    delivery_notes: Optional[str] = None


class DeliveryShow(DeliveryBase):
    id: int
    pickup_location: LocationOut
    dropoff_location: LocationOut
    review: Optional[ReviewRead] = None
    created_at: datetime
    driver: Optional[DriverRead] = None
    client: Optional[ClientOut] = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryStatusUpdate(BaseModel):
    new_status: DeliveryStatus
