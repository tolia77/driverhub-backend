from typing import Optional, Type

from sqlalchemy.orm import Session, joinedload

from app.models import Review
from app.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review, int]):
    def __init__(self, db: Session):
        super().__init__(db, Review)
        self.with_load(joinedload(Review.delivery))

    def get_by_delivery(self, delivery_id: int) -> Optional[Review]:
        return self.get_by_field("delivery_id", delivery_id)

    def exists_for_delivery(self, delivery_id: int) -> bool:
        return self.db.query(
            self.db.query(self.model)
            .filter_by(delivery_id=delivery_id)
            .exists()
        ).scalar()

    def get_by_client(self, client_id: int, skip: int = 0, limit: int = 100) -> list[Type[Review]]:
        return (
            self.db.query(Review)
            .join(Review.delivery)
            .filter_by(client_id=client_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
