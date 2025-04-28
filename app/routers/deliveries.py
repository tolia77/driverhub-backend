from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import Delivery, User, Driver
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryUpdate,
    DeliveryShow,
    DeliveryStatus
)

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.post("/",
             response_model=DeliveryShow,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("dispatcher"))])
def create_delivery(
    delivery_data: DeliveryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new delivery (Dispatcher only)
    """
    # Validate driver exists if specified
    if delivery_data.driver_id:
        driver = db.query(Driver).filter(Driver.id == delivery_data.driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )

    new_delivery = Delivery(**delivery_data.model_dump())
    db.add(new_delivery)
    db.commit()
    db.refresh(new_delivery)
    return new_delivery


@router.get("/",
            response_model=List[DeliveryShow],
            dependencies=[Depends(require_role("dispatcher"))])
def list_deliveries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all deliveries (Dispatcher only)
    """
    return db.query(Delivery).offset(skip).limit(limit).all()


@router.get("/{delivery_id}",
            response_model=DeliveryShow,
            dependencies=[Depends(require_role("dispatcher"))])
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific delivery (Dispatcher only)
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


@router.put("/{delivery_id}",
            response_model=DeliveryShow,
            dependencies=[Depends(require_role("dispatcher"))])
def update_delivery(
    delivery_id: int,
    delivery_data: DeliveryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update delivery details (Dispatcher only)
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    # Validate driver exists if specified
    if delivery_data.driver_id:
        driver = db.query(Driver).filter(Driver.id == delivery_data.driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )

    for field, value in delivery_data.model_dump(exclude_unset=True).items():
        setattr(delivery, field, value)

    db.commit()
    db.refresh(delivery)
    return delivery


@router.patch("/{delivery_id}/status",
              response_model=DeliveryShow)
def update_delivery_status(
    delivery_id: int,
    new_status: DeliveryStatus = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["type"] != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can update delivery status"
        )

    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    if delivery.driver_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update status for your assigned deliveries"
        )

    delivery.status = new_status
    db.commit()
    db.refresh(delivery)
    return delivery


@router.delete("/{delivery_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("admin"))])
def delete_delivery(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a delivery (Admin only)
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    db.delete(delivery)
    db.commit()