from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.base_service import BaseService


class ReviewService(BaseService[ReviewCreate, int, Review, ReviewRepository]):
    def __init__(self, db: Session):
        repository = ReviewRepository(db)
        super().__init__(repository, Review)

    def create(self, data: ReviewCreate) -> Review:
        existing_review = self.repository.get_by_delivery_id(data.delivery_id)
        if existing_review is not None:
            raise ValueError("A review for this delivery already exists.")
        return super().create(data)

    def update(self, review_id: int, data: ReviewUpdate) -> Optional[Review]:
        existing_review = self.get(review_id)
        if not existing_review:
            return None

        if data.delivery_id is not None and data.delivery_id != existing_review.delivery_id:
            conflicting_review = self.repository.get_by_delivery_id(data.delivery_id)
            if conflicting_review is not None:
                raise ValueError("Another review already exists for this delivery.")

        return super().update(review_id, data)

    def get_client_reviews(self, client_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
        return self.repository.get_client_reviews(client_id, skip, limit)
