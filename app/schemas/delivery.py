from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DeliveryStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In-Transit"
    DELIVERED = "Delivered"
    FAILED = "Failed"


class DeliveryBase(BaseModel):
    driver_id: Optional[int] = None
    client_id: Optional[int] = None
    pickup_location: str
    dropoff_location: str
    package_details: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    delivery_notes: Optional[str] = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryUpdate(BaseModel):
    driver_id: Optional[int] = None
    client_id: Optional[int] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    package_details: Optional[str] = None
    status: Optional[DeliveryStatus] = None
    delivery_notes: Optional[str] = None


class DeliveryOut(DeliveryBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
