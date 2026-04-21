from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.persistence.base import Base


AlertBase = Base


class AlertRow(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_active_last_checked", "active", "last_checked_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    user_email: Mapped[str] = mapped_column(String(320))
    query: Mapped[str] = mapped_column(String(255))
    condition: Mapped[str] = mapped_column(String(32))
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    weights_json: Mapped[str] = mapped_column(Text)
    interval_minutes: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
