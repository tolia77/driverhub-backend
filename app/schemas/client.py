from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime

from app.schemas.user import UserBase


class ClientBase(UserBase):
    phone_number: str


class ClientSignup(ClientBase):
    password: str


class ClientUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    password: str | None = None


class ClientOut(ClientBase):
    id: int
    created_at: datetime
    type: str

    model_config = ConfigDict(from_attributes=True)
