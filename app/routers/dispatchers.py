from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.dependencies import require_role
from app.models import Dispatcher, User
from app.schemas.dispatcher import DispatcherCreate, DispatcherRead, DispatcherUpdate
from app.utils.security import hash_password

router = APIRouter(prefix="/dispatchers", tags=["dispatchers"])


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=DispatcherRead,
             dependencies=[Depends(require_role("admin"))])
def create_dispatcher(dispatcher: DispatcherCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == dispatcher.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    hashed_password = hash_password(dispatcher.password)

    new_user = Dispatcher(
        email=dispatcher.email,
        password_hash=hashed_password,
        first_name=dispatcher.first_name,
        last_name=dispatcher.last_name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=List[DispatcherRead],
            dependencies=[Depends(require_role("admin"))])
def list_dispatchers(db: Session = Depends(get_db)):
    return db.query(Dispatcher).all()


@router.get("/{dispatcher_id}", response_model=DispatcherRead,
            dependencies=[Depends(require_role("admin"))])
def get_dispatcher(dispatcher_id: int, db: Session = Depends(get_db)):
    dispatcher = db.query(Dispatcher).filter(Dispatcher.id == dispatcher_id).first()
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")
    return dispatcher


@router.put("/{dispatcher_id}", response_model=DispatcherRead,
            dependencies=[Depends(require_role("admin"))])
def update_dispatcher(dispatcher_id: int, dispatcher_update: DispatcherUpdate, db: Session = Depends(get_db)):
    dispatcher = db.query(Dispatcher).filter(Dispatcher.id == dispatcher_id).first()
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")

    if dispatcher_update.first_name is not None:
        dispatcher.first_name = dispatcher_update.first_name
    if dispatcher_update.last_name is not None:
        dispatcher.last_name = dispatcher_update.last_name

    db.commit()
    db.refresh(dispatcher)
    return dispatcher


@router.delete("/{dispatcher_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("admin"))])
def delete_dispatcher(dispatcher_id: int, db: Session = Depends(get_db)):
    dispatcher = db.query(Dispatcher).filter(Dispatcher.id == dispatcher_id).first()
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")

    db.delete(dispatcher)
    db.commit()
