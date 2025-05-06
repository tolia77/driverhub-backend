from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role, get_current_user
from app.schemas.log_break import LogBreakCreate, LogBreakUpdate, LogBreakOut
from app.services.log_break_service import LogBreakService

router = APIRouter(prefix="/log_breaks", tags=["log_breaks"])


def get_log_break_service(db: Session = Depends(get_db)) -> LogBreakService:
    return LogBreakService(db)


@router.post("/", response_model=LogBreakOut,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("driver"))])
def create_log_break(
        log_break_data: LogBreakCreate,
        service: LogBreakService = Depends(get_log_break_service),
        current_user: dict = Depends(get_current_user)
):
    try:
        new_log_break = service.create_log_break(log_break_data, current_user["id"])
        return new_log_break
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[LogBreakOut])
def list_log_breaks(
        delivery_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        service: LogBreakService = Depends(get_log_break_service)
):
    if delivery_id:
        return service.filter(delivery_id=delivery_id, skip=skip, limit=limit)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{log_break_id}", response_model=LogBreakOut)
def get_log_break(
        log_break_id: int,
        service: LogBreakService = Depends(get_log_break_service)
):
    log_break = service.get(log_break_id)
    if not log_break:
        raise HTTPException(status_code=404, detail="Log break not found")
    return log_break


@router.patch("/{log_break_id}", response_model=LogBreakOut,
              dependencies=[Depends(require_role("driver"))])
def update_log_break(
        log_break_id: int,
        log_break_data: LogBreakUpdate,
        service: LogBreakService = Depends(get_log_break_service),
        current_user: dict = Depends(get_current_user)
):
    try:
        updated_break = service.update_log_break(
            log_break_id,
            log_break_data,
            current_user["id"]
        )
        if not updated_break:
            raise HTTPException(status_code=404, detail="Log break not found")
        return updated_break
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{log_break_id}", status_code=204,
               dependencies=[Depends(require_role("driver"))])
def delete_log_break(
        log_break_id: int,
        service: LogBreakService = Depends(get_log_break_service)
):
    log_break = service.get(log_break_id)
    if not log_break:
        raise HTTPException(status_code=404, detail="Log break not found")

    try:
        if not service.delete(log_break_id):
            raise HTTPException(status_code=404, detail="Log break not found")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/driver/me", response_model=List[LogBreakOut],
            dependencies=[Depends(require_role("driver"))])
def get_my_log_breaks(
        skip: int = 0,
        limit: int = 100,
        service: LogBreakService = Depends(get_log_break_service),
        current_user: dict = Depends(get_current_user)
):
    return service.get_driver_log_breaks(current_user["id"], skip, limit)