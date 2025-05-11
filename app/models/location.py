from datetime import datetime
from typing import List

import requests
from sqlalchemy import Float, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db import Base
from app.settings import settings


class Location(Base):
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    pickup_deliveries: Mapped[List["Delivery"]] = relationship(
        "Delivery",
        back_populates="pickup_location",
        foreign_keys="Delivery.pickup_location_id"
    )
    dropoff_deliveries: Mapped[List["Delivery"]] = relationship(
        "Delivery",
        back_populates="dropoff_location",
        foreign_keys="Delivery.dropoff_location_id"
    )
    breaks: Mapped[List["LogBreak"]] = relationship(
        "LogBreak",
        back_populates="location"
    )

    def get_address(self) -> str:
        if settings.app.environment == "test":
            return "Test Address"
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "format": "json"
        }
        headers = {"User-Agent": "drivetrack/1.0"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return "Unknown location"

        data = response.json()
        addr = data.get("address", {})

        road = addr.get("road") or addr.get("street") or ""
        house_number = addr.get("house_number") or ""
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        district = addr.get("district") or ""
        state = addr.get("state") or ""
        country = addr.get("country") or ""

        parts = [road, house_number, city, district, state, country]
        return ", ".join(part for part in parts if part)
