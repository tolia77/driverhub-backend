from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, require_role
from app.models import User, Client
from app.schemas.client import ClientSignup
from app.schemas.user import UserLogin
from app.utils.jwt import create_access_token
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


@router.post("/login")
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        {"id": user.id, "sub": user.email, "type": user.type}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "type": user.type,
        },
    }


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(client: ClientSignup, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == client.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    hashed_password = hash_password(client.password)

    new_user = Client(
        email=client.email,
        password_hash=hashed_password,
        first_name=client.first_name,
        last_name=client.last_name,
        phone_number=client.phone_number,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "email": new_user.email}


@router.get("/me")
def read_me(current_user=Depends(get_current_user)):
    return {"user": current_user}


@router.get("/admin", dependencies=[Depends(require_role("admin"))])
def admin_only():
    return {"message": "Welcome admin!"}
