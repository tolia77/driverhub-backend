from typing import List
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_role
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    return VehicleService(db)


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=VehicleRead,
             dependencies=[Depends(require_role("dispatcher"))])
async def create_vehicle(
        vehicle: VehicleCreate,
        service: VehicleService = Depends(get_vehicle_service)
):
    try:
        new_vehicle = await service.create_vehicle(vehicle)
        return new_vehicle
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/unassigned",
            response_model=List[VehicleRead],
            dependencies=[Depends(require_role("dispatcher"))])
async def get_unassigned_vehicles(
        service: VehicleService = Depends(get_vehicle_service)
):
    vehicles = await service.get_unassigned_vehicles()
    return vehicles


@router.get("/",
            response_model=List[VehicleRead],
            dependencies=[Depends(require_role("dispatcher"))])
async def list_vehicles(
        service: VehicleService = Depends(get_vehicle_service)
):
    vehicles = await service.get_all()
    return vehicles


@router.get("/{vehicle_id}",
            response_model=VehicleRead,
            dependencies=[Depends(require_role("dispatcher"))])
async def get_vehicle(
        vehicle_id: int,
        service: VehicleService = Depends(get_vehicle_service)
):
    vehicle = await service.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.patch("/{vehicle_id}",
              response_model=VehicleRead,
              dependencies=[Depends(require_role("dispatcher"))])
async def update_vehicle(
        vehicle_id: int,
        vehicle_update: VehicleUpdate,
        service: VehicleService = Depends(get_vehicle_service)
):
    try:
        updated_vehicle = await service.update_vehicle(vehicle_id, vehicle_update)
        if not updated_vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return updated_vehicle
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{vehicle_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("dispatcher"))])
async def delete_vehicle(
        vehicle_id: int,
        service: VehicleService = Depends(get_vehicle_service)
):
    vehicle = await service.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle.driver:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete vehicle assigned to a driver. Unassign driver first."
        )

    await service.delete(vehicle_id)
