from datetime import date

from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db import Base


class Vehicle(Base):
    __tablename__ = 'vehicles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    license_plate: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    maintenance_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    driver: Mapped["Driver"] = relationship("Driver", back_populates="vehicle", uselist=False)
