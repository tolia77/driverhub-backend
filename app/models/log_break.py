from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class LogBreak(Base):
    __tablename__ = 'log_breaks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_id: Mapped[int] = mapped_column(ForeignKey('deliveries.id'), nullable=False)

    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="breaks")
