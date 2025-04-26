from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import UserRole
from app.utils.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": payload["sub"], "role": payload["role"]}

def require_role(required_role: str):
    def wrapper(user = Depends(get_current_user)):
        print(user["role"].split(".")[1])
        print(required_role)
        if  user["role"].split(".")[1] != "ADMIN" and user["role"].split(".")[1] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user
    return wrapper