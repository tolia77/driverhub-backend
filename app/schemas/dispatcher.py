from pydantic import BaseModel, ConfigDict
from typing import Optional


class DispatcherCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class DispatcherRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class DispatcherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
