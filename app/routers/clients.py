from typing import List

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_role
from app.models import Client, User
from app.schemas.client import ClientOut, ClientUpdate
from app.utils.security import hash_password

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/",
            response_model=List[ClientOut],
            dependencies=[Depends(require_role("dispatcher"))])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()


@router.get("/{client_id}",
            response_model=ClientOut,
            dependencies=[Depends(require_role("dispatcher"))])
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientOut, dependencies=[Depends(require_role("admin"))])
def update_client(
        client_id: int,
        client_update: ClientUpdate,
        db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client_update.email is not None:
        existing_user = db.query(User).filter(
            User.email == client_update.email,
            User.id != client_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        client.email = client_update.email

    if client_update.first_name is not None:
        client.first_name = client_update.first_name
    if client_update.last_name is not None:
        client.last_name = client_update.last_name
    if client_update.phone_number is not None:
        client.phone_number = client_update.phone_number
    if client_update.password is not None:
        client.password_hash = hash_password(client_update.password)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("admin"))])
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
