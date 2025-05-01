from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import Review, Delivery, User
from app.schemas.review import ReviewBase, ReviewCreate, ReviewUpdate, ReviewRead

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=ReviewRead,
             dependencies=[Depends(require_role("client"))])
def create_review(
        review: ReviewCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    # Check if the delivery exists and belongs to the current client
    delivery = db.query(Delivery).filter(
        Delivery.id == review.delivery_id,
        Delivery.client_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found or not assigned to you"
        )

    # Check if review already exists for this delivery
    existing_review = db.query(Review).filter(
        Review.delivery_id == review.delivery_id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this delivery"
        )

    new_review = Review(
        delivery_id=review.delivery_id,
        text=review.text,
        rating=review.rating
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


@router.get("/",
            response_model=List[ReviewRead],
            dependencies=[Depends(require_role("dispatcher"))])
def list_reviews(
        delivery_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    query = db.query(Review)

    if delivery_id is not None:
        query = query.filter(Review.delivery_id == delivery_id)

    return query.offset(skip).limit(limit).all()


@router.get("/{review_id}",
            response_model=ReviewRead,
            dependencies=[Depends(require_role("dispatcher"))])
def get_review(
        review_id: int,
        db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review


@router.patch("/{review_id}",
              response_model=ReviewRead,
              dependencies=[Depends(require_role("client"))])
def update_review(
        review_id: int,
        review_update: ReviewUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Verify the review belongs to the current client through delivery
    delivery = db.query(Delivery).filter(
        Delivery.id == review.delivery_id,
        Delivery.client_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own reviews"
        )

    if review_update.text is not None:
        review.text = review_update.text
    if review_update.rating is not None:
        review.rating = review_update.rating

    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("client"))])
def delete_review(
        review_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Verify the review belongs to the current client through delivery
    delivery = db.query(Delivery).filter(
        Delivery.id == review.delivery_id,
        Delivery.client_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )

    db.delete(review)
    db.commit()


@router.get("/client/me",
            response_model=List[ReviewRead],
            dependencies=[Depends(require_role("client"))])
def get_my_reviews(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return db.query(Review) \
        .join(Delivery, Review.delivery_id == Delivery.id) \
        .filter(Delivery.client_id == current_user["id"]) \
        .offset(skip) \
        .limit(limit) \
        .all()