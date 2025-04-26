from pydantic import BaseModel


class DispatcherCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
