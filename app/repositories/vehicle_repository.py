from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models import Vehicle
from app.repositories.base_repository import BaseRepository


class VehicleRepository(BaseRepository[Vehicle, int]):
    def __init__(self, db: Session):
        super().__init__(db, Vehicle)
        self.with_load(joinedload(Vehicle.driver))

    def get_by_license_plate(self, license_plate: str) -> Optional[Vehicle]:
        return self.db.query(self.model).filter(self.model.license_plate == license_plate).first()