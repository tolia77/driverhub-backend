from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.models import User


class Driver(User):
    __tablename__ = 'drivers'

    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    license_number: Mapped[str] = mapped_column(nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'driver',
    }