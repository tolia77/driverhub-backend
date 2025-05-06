from typing import Optional
from sqlalchemy.orm import Session
from app.models import Location
from app.schemas.location import LocationCreate, LocationOut
from app.repositories.location_repository import LocationRepository


class LocationService:
    def __init__(self, db: Session):
        self.repository = LocationRepository(db)

    def create(self, location_data: LocationCreate) -> Location:
        location = Location(**location_data.model_dump())
        location.address = location.get_address()
        return self.repository.create(location)

    def update(self, location_id: int, location_data: LocationCreate) -> Optional[Location]:
        location = self.repository.get(location_id)
        if not location:
            return None

        for field, value in location_data.model_dump().items():
            setattr(location, field, value)

        location.address = location.get_address()
        self.repository.db.commit()
        self.repository.db.refresh(location)
        return location

    def get(self, location_id: int) -> Optional[LocationOut]:
        location = self.repository.get(location_id)
        return LocationOut.model_validate(location) if location else None
