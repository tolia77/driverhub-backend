from sqlalchemy.orm import Session

from app.models import Location
from app.repositories.base_repository import BaseRepository


class LocationRepository(BaseRepository[Location, int]):
    def __init__(self, db: Session):
        super().__init__(db, Location)
