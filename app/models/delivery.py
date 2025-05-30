from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db import Base


class DeliveryStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In-Transit"
    DELIVERED = "Delivered"
    FAILED = "Failed"


class Delivery(Base):
    __tablename__ = 'deliveries'

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey('drivers.id'), nullable=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey('clients.id'), nullable=True)

    pickup_location_id: Mapped[int] = mapped_column(ForeignKey('locations.id'), nullable=False)
    dropoff_location_id: Mapped[int] = mapped_column(ForeignKey('locations.id'), nullable=False)

    package_details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus),
        default=DeliveryStatus.PENDING,
        nullable=False
    )
    delivery_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

    driver: Mapped["Driver"] = relationship("Driver", back_populates="deliveries")
    client: Mapped["Client"] = relationship("Client", back_populates="deliveries")

    pickup_location: Mapped["Location"] = relationship("Location", foreign_keys=[pickup_location_id])
    dropoff_location: Mapped["Location"] = relationship("Location", foreign_keys=[dropoff_location_id])

    breaks: Mapped[list["LogBreak"]] = relationship("LogBreak", back_populates="delivery", cascade="all, delete-orphan")
    review: Mapped["Review"] = relationship("Review", back_populates="delivery", uselist=False, cascade="all, delete-orphan")
