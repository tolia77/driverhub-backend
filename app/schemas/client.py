from pydantic import BaseModel, ConfigDict


class ClientSignup(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    model_config = ConfigDict(from_attributes=True)
