from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_current_user_from_ws
from app.db import get_db
from app.models.message import Message
from collections import defaultdict
import datetime

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_dispatchers: Dict[int, WebSocket] = {}
        self.active_drivers: Dict[int, WebSocket] = {}

    async def connect(self, user: dict, websocket: WebSocket):
        await websocket.accept()
        if user["type"] == "dispatcher":
            self.active_dispatchers[user["id"]] = websocket
        elif user["type"] == "driver":
            self.active_drivers[user["id"]] = websocket

    def disconnect(self, user: dict):
        if user["type"] == "dispatcher":
            self.active_dispatchers.pop(user["id"], None)
        elif user["type"] == "driver":
            self.active_drivers.pop(user["id"], None)

    async def send_to_driver(self, driver_id: int, message: dict):
        if driver_ws := self.active_drivers.get(driver_id):
            await driver_ws.send_json(message)

    async def send_to_all_dispatchers(self, message: dict):
        for ws in self.active_dispatchers.values():
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat(
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    user = await get_current_user_from_ws(websocket)
    await manager.connect(user, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("message")
            target_driver_id = data.get("driver_id")

            if user["type"] == "dispatcher":
                if not target_driver_id:
                    await websocket.send_json({"error": "driver_id is required"})
                    continue

                message = Message(
                    text=text,
                    sender_id=user["id"],
                    receiver_id=target_driver_id
                )
                db.add(message)
                db.commit()
                db.refresh(message)

                # Send to target driver
                await manager.send_to_driver(
                    target_driver_id,
                    {
                        "id": message.id,
                        "text": message.text,
                        "sender_id": message.sender_id,
                        "receiver_id": message.receiver_id,
                        "created_at": message.created_at.isoformat(),
                        "type": "message"
                    }
                )

            elif user["type"] == "driver":
                message = Message(
                    text=text,
                    sender_id=user["id"],
                    receiver_id=None
                )
                db.add(message)
                db.commit()
                db.refresh(message)

                await manager.send_to_all_dispatchers(
                    {
                        "id": message.id,
                        "text": message.text,
                        "sender_id": message.sender_id,
                        "receiver_id": message.receiver_id,
                        "created_at": message.created_at.isoformat(),
                        "type": "message"
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(user)
    finally:
        db.close()