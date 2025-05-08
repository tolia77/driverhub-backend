from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.models import Review
from app.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review, int]):
    def __init__(self, db: Session):
        super().__init__(db, Review)
        self.with_load(joinedload(Review.delivery))

    def get_by_delivery_id(self, delivery_id: int) -> Optional[Review]:
        return self.get_by_field("delivery_id", delivery_id)

    def get_client_reviews(self, client_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
        query = self.db.query(self.model)
        query = self._apply_load_options(query)
        query = query.join(self.model.delivery).filter(self.model.delivery.has(client_id=client_id))
        return query.offset(skip).limit(limit).all()
