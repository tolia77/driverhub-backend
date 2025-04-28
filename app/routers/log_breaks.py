from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.models import LogBreak, Delivery, User
from app.schemas.log_break import (
    LogBreakCreate,
    LogBreakUpdate,
    LogBreakOut
)

router = APIRouter(prefix="/log_breaks", tags=["log_breaks"])


@router.post("/",
             response_model=LogBreakOut,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("driver"))])
def create_log_break(
        log_break_data: LogBreakCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(
        Delivery.id == log_break_data.delivery_id,
        Delivery.driver_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found or not assigned to you"
        )

    if log_break_data.start_time >= log_break_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    new_log_break = LogBreak(**log_break_data.model_dump())
    db.add(new_log_break)
    db.commit()
    db.refresh(new_log_break)
    return new_log_break


@router.get("/", response_model=List[LogBreakOut])
def list_log_breaks(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    return db.query(LogBreak).offset(skip).limit(limit).all()


@router.get("/{log_break_id}", response_model=LogBreakOut)
def get_log_break(
        log_break_id: int,
        db: Session = Depends(get_db)
):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log break not found"
        )
    return log_break


@router.put("/{log_break_id}",
            response_model=LogBreakOut,
            dependencies=[Depends(require_role("driver"))])
def update_log_break(
        log_break_id: int,
        log_break_data: LogBreakUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log break not found"
        )
    delivery = db.query(Delivery).filter(
        Delivery.id == log_break.delivery_id,
        Delivery.driver_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own log breaks"
        )

    if (log_break_data.start_time or log_break_data.end_time) and \
            (log_break_data.start_time >= log_break_data.end_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    for field, value in log_break_data.model_dump(exclude_unset=True).items():
        setattr(log_break, field, value)

    db.commit()
    db.refresh(log_break)
    return log_break


@router.delete("/{log_break_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("driver"))])
def delete_log_break(
        log_break_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    log_break = db.query(LogBreak).filter(LogBreak.id == log_break_id).first()
    if not log_break:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log break not found"
        )

    delivery = db.query(Delivery).filter(
        Delivery.id == log_break.delivery_id,
        Delivery.driver_id == current_user["id"]
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own log breaks"
        )

    db.delete(log_break)
    db.commit()
