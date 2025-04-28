from datetime import datetime, UTC
from sqlalchemy import ForeignKey, Text, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey('deliveries.id'), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)

    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="reviews")
