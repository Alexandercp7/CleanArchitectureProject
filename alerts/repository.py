from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.alert import Alert, AlertCondition
from infrastructure.persistence.models.alert_model import AlertBase, AlertRow


@dataclass(frozen=True)
class AlertSpec:
    user_id: str
    user_email: str
    query: str
    condition: AlertCondition
    weights: dict[str, float]
    interval_minutes: int
    threshold: float | None = None


_Base = AlertBase


SessionFactory = Callable[[], AsyncSession]


class AlertRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def create(self, spec: AlertSpec) -> Alert:
        now = datetime.now(tz=timezone.utc)
        row = AlertRow(
            id=str(uuid4()),
            user_id=spec.user_id,
            user_email=spec.user_email,
            query=spec.query,
            condition=spec.condition.value,
            threshold=spec.threshold,
            weights_json=_to_weights_json(spec.weights),
            interval_minutes=spec.interval_minutes,
            active=True,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _to_alert(row)

    async def get_by_user(self, user_id: str) -> list[Alert]:
        statement = select(AlertRow).where(AlertRow.user_id == user_id).order_by(AlertRow.created_at.desc())
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).scalars().all()
        return [_to_alert(row) for row in rows]

    async def get_active(self) -> list[Alert]:
        statement = select(AlertRow).where(AlertRow.active.is_(True)).order_by(AlertRow.last_checked_at.asc().nullsfirst())
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).scalars().all()
        return [_to_alert(row) for row in rows]

    async def get_by_id(self, alert_id: str) -> Alert | None:
        statement = select(AlertRow).where(AlertRow.id == alert_id)
        async with self._session_factory() as session:
            row = (await session.execute(statement)).scalar_one_or_none()
        return None if row is None else _to_alert(row)

    async def deactivate(self, alert_id: str, requesting_user_id: str) -> bool:
        now = datetime.now(tz=timezone.utc)
        statement = (
            update(AlertRow)
            .where(and_(AlertRow.id == alert_id, AlertRow.user_id == requesting_user_id, AlertRow.active.is_(True)))
            .values(active=False, updated_at=now)
        )
        async with self._session_factory() as session:
            result = await session.execute(statement)
            await session.commit()
        return result.rowcount > 0

    async def record_evaluation(self, alert_id: str, condition_met: bool, error: str | None = None) -> None:
        now = datetime.now(tz=timezone.utc)
        values = {
            "last_checked_at": now,
            "updated_at": now,
            "last_error": error,
        }
        if condition_met:
            values["last_triggered_at"] = now

        statement = update(AlertRow).where(AlertRow.id == alert_id).values(**values)
        async with self._session_factory() as session:
            await session.execute(statement)
            await session.commit()


def _to_alert(row: AlertRow) -> Alert:
    return Alert(
        id=row.id,
        user_id=row.user_id,
        user_email=row.user_email,
        query=row.query,
        condition=AlertCondition(row.condition),
        threshold=row.threshold,
        weights=_from_weights_json(row.weights_json),
        interval_minutes=row.interval_minutes,
        active=row.active,
        created_at=_as_utc(row.created_at),
        last_checked_at=_as_utc_optional(row.last_checked_at),
        last_triggered_at=_as_utc_optional(row.last_triggered_at),
        last_error=row.last_error,
        updated_at=_as_utc(row.updated_at),
    )


def _to_weights_json(weights: dict[str, float]) -> str:
    parts = [f"{key}:{weights[key]}" for key in sorted(weights)]
    return "|".join(parts)


def _from_weights_json(raw_value: str) -> dict[str, float]:
    if not raw_value:
        return {}
    weights: dict[str, float] = {}
    for part in raw_value.split("|"):
        key, value = part.split(":", maxsplit=1)
        weights[key] = float(value)
    return weights


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _as_utc_optional(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)
