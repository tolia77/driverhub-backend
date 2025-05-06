from typing import Optional, List

from sqlalchemy.orm import Session

from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.models import Vehicle
from app.repositories.vehicle_repository import VehicleRepository

from app.services.abstract_service import AbstractService


class VehicleService(AbstractService[VehicleCreate, int, Vehicle, VehicleRepository]):
    def __init__(self, db: Session):
        repository = VehicleRepository(db)
        super().__init__(repository)

    async def create_vehicle(self, vehicle_data: VehicleCreate) -> Vehicle:
        if await self._license_plate_exists(vehicle_data.license_plate):
            raise ValueError("License plate is already used")

        return await self.create(vehicle_data)

    async def update_vehicle(
            self,
            vehicle_id: int,
            vehicle_data: VehicleUpdate
    ) -> Optional[Vehicle]:
        if not await self.exists(vehicle_id):
            return None

        if vehicle_data.license_plate:
            existing = await self._get_by_license_plate(vehicle_data.license_plate)
            if existing and existing.id != vehicle_id:
                raise ValueError("License plate is already used")

        return await self.update(vehicle_id, vehicle_data)

    async def _license_plate_exists(self, license_plate: str) -> bool:
        return self.repository.get_by_license_plate(license_plate) is not None

    async def _get_by_license_plate(self, license_plate: str) -> Optional[Vehicle]:
        return self.repository.get_by_license_plate(license_plate)

    async def get_unassigned_vehicles(self) -> List[Vehicle]:
        return await self.filter(driver=None)
