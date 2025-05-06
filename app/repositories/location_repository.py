from sqlalchemy.orm import Session

from app.models import Location
from app.repositories.abstract_repository import AbstractRepository


class LocationRepository(AbstractRepository[Location, int]):
    def __init__(self, db: Session):
        super().__init__(db, Location)
