from typing import Optional, Type

from sqlalchemy.orm import Session

from app.models import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.base_service import BaseService


class ReviewService(BaseService[ReviewCreate, ReviewUpdate, int, Review, ReviewRepository]):
    def __init__(self, db: Session):
        repository = ReviewRepository(db)
        super().__init__(repository, Review)

    def create(self, review_data: ReviewCreate) -> Review:
        if self.repository.exists_for_delivery(review_data.delivery_id):
            raise ValueError("Review for this delivery already exists")

        return super().create(review_data)

    def update(self, review_id: int, review_data: ReviewUpdate) -> Optional[Review]:
        review = self.repository.get(review_id)
        if not review:
            return None

        return super().update(review_id, review_data)

    def get_by_delivery(self, delivery_id: int) -> Optional[Review]:
        return self.repository.get_by_delivery(delivery_id)

    def get_by_client(self, client_id: int, skip: int = 0, limit: int = 100) -> list[Type[Review]]:
        return self.repository.get_by_client(client_id, skip, limit)

