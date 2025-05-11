from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import User


class Client(User):
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    phone_number: Mapped[str] = mapped_column(nullable=False)
    deliveries: Mapped[list["Delivery"]] = relationship("Delivery", back_populates="client")
    #TODO: add reviews relationship (not sure)
    __mapper_args__ = {
        'polymorphic_identity': 'client',
    }
