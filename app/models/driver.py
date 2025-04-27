from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import User


class Driver(User):
    __tablename__ = 'drivers'

    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey('vehicles.id'), nullable=True, unique=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="driver")

    __mapper_args__ = {
        'polymorphic_identity': 'driver',
    }
