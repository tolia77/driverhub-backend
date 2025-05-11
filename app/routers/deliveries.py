from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import Delivery, Driver, Location
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryUpdate,
    DeliveryShow,
    DeliveryStatusUpdate
)
from app.utils.email import send_message

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.post("/",
             response_model=DeliveryShow,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("dispatcher"))])
def create_delivery(
        delivery_data: DeliveryCreate,
        db: Session = Depends(get_db)
):
    if delivery_data.driver_id:
        driver = db.query(Driver).filter(Driver.id == delivery_data.driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found"
            )

    pickup_location = Location(**delivery_data.pickup_location.model_dump())
    pickup_location.address = pickup_location.get_address()
    db.add(pickup_location)

    dropoff_location = Location(**delivery_data.dropoff_location.model_dump())
    dropoff_location.address = dropoff_location.get_address()
    db.add(dropoff_location)

    db.commit()
    db.refresh(pickup_location)
    db.refresh(dropoff_location)

    new_delivery = Delivery(
        **delivery_data.model_dump(exclude={"pickup_location", "dropoff_location"}),
        pickup_location_id=pickup_location.id,
        dropoff_location_id=dropoff_location.id
    )

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
    return (db.query(Delivery)
            .options(joinedload(Delivery.review),
                     joinedload(Delivery.driver),
                     joinedload(Delivery.client),
                     joinedload(Delivery.pickup_location),
                     joinedload(Delivery.dropoff_location))
            .offset(skip).limit(limit).all())


@router.get("/{delivery_id}",
            response_model=DeliveryShow,
            dependencies=[Depends(require_role("dispatcher"))])
def get_delivery(
        delivery_id: int,
        db: Session = Depends(get_db)
):
    delivery = (db.query(Delivery)
                .filter(Delivery.id == delivery_id)
                .options(joinedload(Delivery.review),
                         joinedload(Delivery.driver),
                         joinedload(Delivery.client),
                         joinedload(Delivery.pickup_location),
                         joinedload(Delivery.dropoff_location)).first()
                )
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


@router.patch("/{delivery_id}",
              response_model=DeliveryShow,
              dependencies=[Depends(require_role("dispatcher"))])
def update_delivery(
        delivery_id: int,
        delivery_data: DeliveryUpdate,
        db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    if 'driver_id' in delivery_data.model_fields_set:
        if delivery_data.driver_id is not None:
            driver = db.query(Driver).filter(Driver.id == delivery_data.driver_id).first()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Driver not found"
                )
        delivery.driver_id = delivery_data.driver_id

    if 'client_id' in delivery_data.model_fields_set:
        delivery.client_id = delivery_data.client_id

    if delivery_data.pickup_location:
        pickup_location = Location(**delivery_data.pickup_location.model_dump())
        pickup_location.address = pickup_location.get_address()
        db.add(pickup_location)
        db.commit()
        db.refresh(pickup_location)
        delivery.pickup_location_id = pickup_location.id

    if delivery_data.dropoff_location:
        dropoff_location = Location(**delivery_data.dropoff_location.model_dump())
        dropoff_location.address = dropoff_location.get_address()
        db.add(dropoff_location)
        db.commit()
        db.refresh(dropoff_location)
        delivery.dropoff_location_id = dropoff_location.id

    for field, value in delivery_data.model_dump(exclude_unset=True).items():
        if field not in ['driver_id', 'client_id', 'pickup_location', 'dropoff_location']:
            setattr(delivery, field, value)

    db.commit()
    db.refresh(delivery)
    return delivery


@router.patch("/{delivery_id}/status",
              response_model=DeliveryShow,
              dependencies=[Depends(require_role("driver"))])
def update_delivery_status(
        delivery_id: int,
        new_status: DeliveryStatusUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).options(joinedload(Delivery.client)).first()
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

    delivery.status = new_status.new_status
    db.commit()
    db.refresh(delivery)
    send_message(
        delivery.client.first_name,
        delivery.client.last_name,
        delivery.client.email,
        "Delivery Status Update",
        f"Your delivery status has been updated to: {delivery.status.value}"
    )
    return delivery


@router.delete("/{delivery_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("admin"))])
def delete_delivery(
        delivery_id: int,
        db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    db.delete(delivery)
    db.commit()


@router.get("/driver/me",
            response_model=List[DeliveryShow],
            dependencies=[Depends(require_role("driver"))])
def get_my_deliveries(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return db.query(Delivery) \
        .options(joinedload(Delivery.driver),
                 joinedload(Delivery.client),
                 joinedload(Delivery.pickup_location),
                 joinedload(Delivery.dropoff_location)) \
        .filter(Delivery.driver_id == current_user["id"]) \
        .offset(skip) \
        .limit(limit) \
        .all()


@router.get("/client/me",
            response_model=List[DeliveryShow],
            dependencies=[Depends(require_role("client"))])
def get_my_deliveries(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return db.query(Delivery) \
        .options(joinedload(Delivery.review),
                 joinedload(Delivery.pickup_location),
                 joinedload(Delivery.dropoff_location)) \
        .filter(Delivery.client_id == current_user["id"]) \
        .offset(skip) \
        .limit(limit) \
        .all()
