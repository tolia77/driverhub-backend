from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import Delivery
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewRead
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.post("/",
             response_model=ReviewRead,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("client"))])
def create_review(
        review_data: ReviewCreate,
        service: ReviewService = Depends(get_review_service),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter_by(id=review_data.delivery_id).first()
    if not delivery or delivery.client_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Delivery not found or not assigned to you")
    try:
        new_review = service.create(review_data)
        return new_review
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/",
            response_model=List[ReviewRead],
            dependencies=[Depends(require_role("dispatcher"))])
def list_reviews(
        delivery_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        service: ReviewService = Depends(get_review_service)
):
    if delivery_id:
        review = service.get_by_delivery(delivery_id)
        return [review] if review else []
    return service.get_all(skip=skip, limit=limit)


@router.get("/{review_id}",
            response_model=ReviewRead,
            dependencies=[Depends(require_role("dispatcher"))])
def get_review(
        review_id: int,
        service: ReviewService = Depends(get_review_service)
):
    review = service.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.patch("/{review_id}",
              response_model=ReviewRead,
              dependencies=[Depends(require_role("client"))])
def update_review(
        review_id: int,
        review_data: ReviewUpdate,
        service: ReviewService = Depends(get_review_service)
):
    try:
        updated_review = service.update(review_id, review_data)
        if not updated_review:
            raise HTTPException(status_code=404, detail="Review not found")
        return updated_review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{review_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("client"))])
def delete_review(
        review_id: int,
        service: ReviewService = Depends(get_review_service)
):
    review = service.get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if not service.delete(review_id):
        raise HTTPException(status_code=404, detail="Review not found")


@router.get("/client/me",
            response_model=List[ReviewRead],
            dependencies=[Depends(require_role("client"))])
def get_my_reviews(
        skip: int = 0,
        limit: int = 100,
        service: ReviewService = Depends(get_review_service),
        current_user: dict = Depends(get_current_user)
):
    return service.get_by_client(client_id=current_user["id"], skip=skip, limit=limit)
