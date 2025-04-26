from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.models import User


class Client(User):
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    phone_number: Mapped[str] = mapped_column(nullable=False)
    # You don't need to define `type` again because it's already set in the User class
    # type: UserType = UserType.client  # Optional, as polymorphism works

    __mapper_args__ = {
        'polymorphic_identity': 'client',
    }
