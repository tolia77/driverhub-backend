from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import LogBreak, Delivery, Location
from app.schemas.log_break import LogBreakCreate, LogBreakUpdate, LogBreakOut

router = APIRouter(prefix="/log_breaks", tags=["log_breaks"])


@router.post("/", response_model=LogBreakOut,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("driver"))])
def create_log_break(
        log_break_data: LogBreakCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.id == log_break_data.delivery_id).first()
    if not delivery or not (delivery.driver_id == current_user["id"] or current_user["type"] == "admin"):
        raise HTTPException(status_code=404, detail="Delivery not found or not assigned to you")

    if log_break_data.start_time >= log_break_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    location = Location(**log_break_data.location.model_dump())
    db.add(location)
    db.flush()

    new_log_break = LogBreak(
        **log_break_data.model_dump(exclude={"location"}),
        location_id=location.id
    )
    db.add(new_log_break)
    db.commit()
    db.refresh(new_log_break)
    return new_log_break


@router.get("/", response_model=List[LogBreakOut])
def list_log_breaks(
        delivery_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    query = db.query(LogBreak)
    if delivery_id is not None:
        query = query.filter(LogBreak.delivery_id == delivery_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{log_break_id}", response_model=LogBreakOut)
def get_log_break(log_break_id: int, db: Session = Depends(get_db)):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(status_code=404, detail="Log break not found")
    return log_break


@router.patch("/{log_break_id}", response_model=LogBreakOut,
              dependencies=[Depends(require_role("driver"))])
def update_log_break(
        log_break_id: int,
        log_break_data: LogBreakUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(status_code=404, detail="Log break not found")

    delivery = db.query(Delivery).filter(Delivery.id == log_break.delivery_id).first()
    if not delivery or not (delivery.driver_id == current_user["id"] or current_user["type"] == "admin"):
        raise HTTPException(status_code=403, detail="You can only update your own log breaks")

    if (log_break_data.start_time and log_break_data.end_time) and \
            log_break_data.start_time >= log_break_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    update_data = log_break_data.model_dump(exclude_unset=True, exclude={"location"})

    for field, value in update_data.items():
        setattr(log_break, field, value)

    if log_break_data.location:
        new_location = Location(**log_break_data.location.model_dump())
        db.add(new_location)
        db.flush()
        log_break.location_id = new_location.id

    db.commit()
    db.refresh(log_break)
    return log_break


@router.delete("/{log_break_id}", status_code=204,
               dependencies=[Depends(require_role("driver"))])
def delete_log_break(
        log_break_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(status_code=404, detail="Log break not found")

    delivery = db.query(Delivery).filter(Delivery.id == log_break.delivery_id).first()
    if not delivery or not (delivery.driver_id == current_user["id"] or current_user["type"] == "admin"):
        raise HTTPException(status_code=403, detail="You can only delete your own log breaks")

    db.delete(log_break)
    db.commit()


@router.get("/driver/me", response_model=List[LogBreakOut],
            dependencies=[Depends(require_role("driver"))])
def get_my_log_breaks(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return db.query(LogBreak) \
        .join(Delivery, LogBreak.delivery_id == Delivery.id) \
        .filter(Delivery.driver_id == current_user["id"]) \
        .offset(skip) \
        .limit(limit) \
        .all()
