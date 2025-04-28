from datetime import datetime
from pydantic import BaseModel, Field, conint, ConfigDict
from typing import Optional


class ReviewBase(BaseModel):
    delivery_id: int
    text: Optional[str] = None
    rating: conint(ge=1, le=5) = Field(..., description="Rating from 1 to 5")


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    text: Optional[str] = None
    rating: Optional[conint(ge=1, le=5)] = Field(None, description="Rating from 1 to 5")


class ReviewRead(ReviewBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
