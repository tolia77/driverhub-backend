from typing import Optional, Type
from sqlalchemy.orm import Session
from app.models import LogBreak, Delivery
from app.repositories.log_break_repository import LogBreakRepository
from app.schemas.log_break import LogBreakCreate, LogBreakUpdate
from app.services.base_service import BaseService
from app.services.location_service import LocationService


class LogBreakService(BaseService[LogBreakCreate, int, LogBreak, LogBreakRepository]):
    def __init__(self, db: Session):
        repository = LogBreakRepository(db)
        self._location_service = LocationService(db)
        super().__init__(repository, LogBreak)

    def create(
            self,
            log_break_data: LogBreakCreate,
            driver_id: Optional[int] = None
    ) -> LogBreak:
        if log_break_data.start_time >= log_break_data.end_time:
            raise ValueError("End time must be after start time")

        if driver_id:
            delivery = self.repository.db.query(Delivery) \
                .filter(Delivery.id == log_break_data.delivery_id) \
                .first()
            if not delivery or delivery.driver_id != driver_id:
                raise ValueError("Delivery not found or not assigned to you")
        location = self._location_service.create(log_break_data.location)
        break_dict = log_break_data.model_dump(exclude={'location'})
        break_dict['location_id'] = location.id

        log_break = LogBreak(**break_dict)

        return self.repository.create(log_break)

    def update(
            self,
            break_id: int,
            break_data: LogBreakUpdate,
            driver_id: Optional[int] = None
    ) -> Optional[LogBreak]:
        log_break = self.get(break_id)
        if not log_break:
            return None

        if driver_id:
            delivery = self.repository.db.query(Delivery) \
                .filter(Delivery.id == log_break.delivery_id) \
                .first()
            if not delivery or delivery.driver_id != driver_id:
                raise ValueError("You can only update your own log breaks")

        if (break_data.start_time and break_data.end_time) and \
                break_data.start_time >= break_data.end_time:
            raise ValueError("End time must be after start time")

        update_data = break_data.model_dump(exclude_unset=True, exclude={'location'})

        if break_data.location:
            location = self._location_service.update(
                log_break.location_id,
                break_data.location
            )
            if not location:
                return None

        return self.repository.update(break_id, update_data)

    def get_driver_log_breaks(
            self,
            driver_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> list[Type[LogBreak]]:
        return self.repository.get_for_driver(driver_id, skip, limit)
