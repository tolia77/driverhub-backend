from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db import get_db
from app.dependencies import require_role
from app.models import Driver, User, Vehicle
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate
from app.utils.security import hash_password

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=DriverRead,
             dependencies=[Depends(require_role("dispatcher"))])
def create_driver(driver: DriverCreate, db: Session = Depends(get_db)):
    # Перевірка наявності email
    db_user = db.query(User).filter(User.email == driver.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Перевірка наявності vehicle_id (якщо вказаний)
    if driver.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == driver.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle.driver:  # Перевірка чи транспорт вже прив'язаний до іншого водія
            raise HTTPException(status_code=400, detail="Vehicle already assigned to another driver")

    hashed_password = hash_password(driver.password)

    new_driver = Driver(
        email=driver.email,
        password_hash=hashed_password,
        first_name=driver.first_name,
        last_name=driver.last_name,
        license_number=driver.license_number,
        vehicle_id=driver.vehicle_id
    )

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver


@router.get("/", response_model=List[DriverRead],
            dependencies=[Depends(require_role("dispatcher"))])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).options(joinedload(Driver.vehicle)).all()


@router.get("/{driver_id}", response_model=DriverRead,
            dependencies=[Depends(require_role("dispatcher"))])
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).options(joinedload(Driver.vehicle)).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.patch("/{driver_id}", response_model=DriverRead,
            dependencies=[Depends(require_role("dispatcher"))])
def update_driver(driver_id: int, driver_update: DriverUpdate, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    if driver_update.first_name is not None:
        driver.first_name = driver_update.first_name
    if driver_update.last_name is not None:
        driver.last_name = driver_update.last_name
    if driver_update.license_number is not None:
        driver.license_number = driver_update.license_number

    if driver_update.vehicle_id is not None:
        if driver_update.vehicle_id != driver.vehicle_id:
            vehicle = db.query(Vehicle).filter(Vehicle.id == driver_update.vehicle_id).first()
            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle not found")
            if vehicle.driver and vehicle.driver.id != driver_id:
                raise HTTPException(status_code=400, detail="Vehicle already assigned to another driver")
            driver.vehicle_id = driver_update.vehicle_id

    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("dispatcher"))])
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    db.delete(driver)
    db.commit()
