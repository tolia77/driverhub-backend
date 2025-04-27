from typing import Optional
from pydantic import BaseModel
from app.schemas.user import UserCreate, UserRead, UserUpdate


class DriverBase(BaseModel):
    license_number: str


class DriverCreate(UserCreate, DriverBase):
    pass


class DriverRead(UserRead, DriverBase):
    pass


class DriverUpdate(UserUpdate):
    license_number: Optional[str] = None
