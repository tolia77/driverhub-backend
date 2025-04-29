from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, dispatchers, drivers, vehicles, clients, deliveries, log_breaks, websocket

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(dispatchers.router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(clients.router)
app.include_router(deliveries.router)
app.include_router(log_breaks.router)
app.include_router(websocket.router)
