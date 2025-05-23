from typing import Optional

from sqlalchemy.orm import Session
from app.schemas.location import LocationCreate
from app.models import Location
from app.repositories.location_repository import LocationRepository
from app.services.base_service import BaseService


class LocationService(BaseService[LocationCreate, LocationCreate, int, Location, LocationRepository]):
    def __init__(self, db: Session):
        repository = LocationRepository(db)
        super().__init__(repository, Location)

    def create(self, location_data: LocationCreate) -> Location:
        location = super().create(location_data)
        location.address = location.get_address()
        self.repository.update(location.id, {"address": location.address})
        return location

    def update(self, id: int, location_data: LocationCreate) -> Optional[Location]:
        updated_location = super().update(id, location_data)

        if updated_location:
            updated_location.address = updated_location.get_address()
            self.repository.update(id, {"address": updated_location.address})

        return updated_location
