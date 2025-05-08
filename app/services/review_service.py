from typing import Optional, List
from sqlalchemy.orm import Session

from app.schemas.review import ReviewCreate, ReviewUpdate
from app.models import Review
from app.repositories.review_repository import ReviewRepository
from app.services.base_service import BaseService


class ReviewService(BaseService[ReviewCreate, int, Review, ReviewRepository]):
    def __init__(self, db: Session):
        repository = ReviewRepository(db)
        super().__init__(repository, Review)

    def create(self, data: ReviewCreate, client_id: Optional[int] = None) -> Review:
        if self.repository.get_by_delivery_id(data.delivery_id):
            raise ValueError("Review already exists for this delivery")

        review = super().create(data)

        if client_id and review.delivery.client_id != client_id:
            self.repository.delete(review.id)
            raise PermissionError("You can only create reviews for your deliveries")

        return review

    def update(self, id: int, data: ReviewUpdate, client_id: Optional[int] = None) -> Optional[Review]:
        review = self.get(id)
        if not review:
            return None

        if client_id and review.delivery.client_id != client_id:
            raise PermissionError("You can only update your own reviews")

        return super().update(id, data)

    def delete(self, id: int, client_id: Optional[int] = None) -> bool:
        review = self.get(id)
        if not review:
            return False

        if client_id and review.delivery.client_id != client_id:
            raise PermissionError("You can only delete your own reviews")

        return super().delete(id)

    def get_client_reviews(self, client_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
        return self.repository.get_client_reviews(client_id, skip, limit)