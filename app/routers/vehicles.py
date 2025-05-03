from typing import List

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.dependencies import require_role
from app.models import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=VehicleRead,
             dependencies=[Depends(require_role("dispatcher"))])
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    # Перевірка унікальності номерного знаку
    db_vehicle = db.query(Vehicle).filter(Vehicle.license_plate == vehicle.license_plate).first()
    if db_vehicle:
        raise HTTPException(status_code=400, detail="Vehicle with this license plate already exists")

    new_vehicle = Vehicle(
        model=vehicle.model,
        license_plate=vehicle.license_plate,
        capacity=vehicle.capacity,
        mileage=vehicle.mileage,
        maintenance_due_date=vehicle.maintenance_due_date
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle


@router.get("/unassigned", response_model=List[VehicleRead],
            dependencies=[Depends(require_role("dispatcher"))])
def get_unassigned_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).filter(Vehicle.driver == None).all()


@router.get("/", response_model=List[VehicleRead],
            dependencies=[Depends(require_role("dispatcher"))])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).options(joinedload(Vehicle.driver)).all()


@router.get("/{vehicle_id}", response_model=VehicleRead,
            dependencies=[Depends(require_role("dispatcher"))])
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).options(joinedload(Vehicle.driver)).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleRead,
              dependencies=[Depends(require_role("dispatcher"))])
def update_vehicle(vehicle_id: int, vehicle_update: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle_update.model is not None:
        vehicle.model = vehicle_update.model
    if vehicle_update.license_plate is not None:
        # Перевірка унікальності нового номерного знаку
        if vehicle_update.license_plate != vehicle.license_plate:
            existing_vehicle = db.query(Vehicle).filter(
                Vehicle.license_plate == vehicle_update.license_plate,
                Vehicle.id != vehicle_id
            ).first()
            if existing_vehicle:
                raise HTTPException(status_code=400, detail="License plate already in use")
        vehicle.license_plate = vehicle_update.license_plate
    if vehicle_update.capacity is not None:
        vehicle.capacity = vehicle_update.capacity
    if vehicle_update.mileage is not None:
        vehicle.mileage = vehicle_update.mileage
    if vehicle_update.maintenance_due_date is not None:
        vehicle.maintenance_due_date = vehicle_update.maintenance_due_date

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("dispatcher"))])
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.driver:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete vehicle assigned to a driver. Unassign driver first."
        )

    db.delete(vehicle)
    db.commit()
