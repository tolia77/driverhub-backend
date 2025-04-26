from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.models import User


class Dispatcher(User):
    __tablename__ = 'dispatchers'

    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dispatcher',
    }
