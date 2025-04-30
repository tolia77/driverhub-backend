import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.db import Base


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(datetime.UTC),
        nullable=False
    )
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])
