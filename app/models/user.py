import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from app.db import Base


class User(Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(datetime.UTC), nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': 'type'
    }
