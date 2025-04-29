from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordBearer

from app.utils.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": payload["id"], "email": payload["sub"], "type": payload["type"]}


def require_role(required_role: str):
    def wrapper(user=Depends(get_current_user)):
        if user["type"] != "admin" and user["type"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user

    return wrapper


async def get_current_user_from_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Token missing")

    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Invalid token")

    return {"id": payload["id"], "email": payload["sub"], "type": payload["type"]}
