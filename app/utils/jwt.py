from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError

from app.settings import settings

SECRET_KEY = settings.jwt.jwt_secret
EXPIRES_IN_MINUTES = settings.jwt.jwt_expires_in_minutes
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = EXPIRES_IN_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
