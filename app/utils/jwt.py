from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError

from app.settings import settings

SECRET_KEY = settings.JWT_SECRET
EXPIRES_IN_MINUTES = settings.JWT_EXPIRES_IN_MINUTES
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
