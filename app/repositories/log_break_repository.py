from typing import List, Optional, Type
from sqlalchemy.orm import Session, joinedload
from app.models import LogBreak, Delivery
from app.repositories.abstract_repository import AbstractRepository


class LogBreakRepository(AbstractRepository[LogBreak, int]):
    def __init__(self, db: Session):
        super().__init__(db, LogBreak)
        self.with_load(
            joinedload(LogBreak.location),
            joinedload(LogBreak.delivery)
        )

    def get_for_driver(self, driver_id: int, skip: int = 0, limit: int = 100) -> list[Type[LogBreak]]:
        return self.db.query(self.model)\
            .join(Delivery, self.model.delivery_id == Delivery.id)\
            .filter(Delivery.driver_id == driver_id)\
            .offset(skip)\
            .limit(limit)\
            .all()