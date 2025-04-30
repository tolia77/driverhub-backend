from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from app.dependencies import get_current_user, get_current_user_from_ws
from collections import defaultdict
import json  # Add this import

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_dispatchers: Dict[int, WebSocket] = {}
        self.active_drivers: Dict[int, WebSocket] = {}
        self.driver_dispatcher_map: Dict[int, List[int]] = defaultdict(list)  # driver_id -> dispatcher_ids

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
        driver_ws = self.active_drivers.get(driver_id)
        if driver_ws:
            await driver_ws.send_json(message)

    async def send_to_all_dispatchers(self, message: dict):
        for ws in self.active_dispatchers.values():
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
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
                await manager.send_to_driver(
                    target_driver_id,
                    {
                        "text": text,
                        "sender": user["id"],
                        "type": "message"
                    }
                )

            elif user["type"] == "driver":
                await manager.send_to_all_dispatchers(
                    {
                        "text": text,
                        "sender": user["id"],
                        "type": "message"
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(user)