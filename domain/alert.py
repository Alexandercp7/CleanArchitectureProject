from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AlertCondition(str, Enum):
    PRICE_BELOW = "PRICE_BELOW"
    IN_STOCK = "IN_STOCK"


@dataclass
class Alert:
    id: str
    user_id: str
    user_email: str
    query: str
    condition: AlertCondition
    threshold: float | None
    weights: dict[str, float]
    interval_minutes: int
    active: bool
    created_at: datetime
    last_checked_at: datetime | None = None
    last_triggered_at: datetime | None = None
    last_error: str | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
