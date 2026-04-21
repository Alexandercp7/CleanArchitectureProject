from datetime import datetime, timezone

import pytest

from alerts.repository import AlertRepository, AlertSpec
from domain.alert import AlertCondition


@pytest.mark.asyncio
async def test_create_and_fetch_alert(session_factory) -> None:
    repo = AlertRepository(session_factory)

    created = await repo.create(
        AlertSpec(
            user_id="u1",
            user_email="user@example.com",
            query="laptop",
            condition=AlertCondition.IN_STOCK,
            weights={"price": 1.0},
            interval_minutes=15,
        )
    )

    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.user_id == "u1"


@pytest.mark.asyncio
async def test_deactivate_alert(session_factory) -> None:
    repo = AlertRepository(session_factory)

    created = await repo.create(
        AlertSpec(
            user_id="u1",
            user_email="user@example.com",
            query="laptop",
            condition=AlertCondition.IN_STOCK,
            weights={"price": 1.0},
            interval_minutes=15,
        )
    )

    did_deactivate = await repo.deactivate(created.id, "u1")

    assert did_deactivate is True


@pytest.mark.asyncio
async def test_record_evaluation_updates_alert(session_factory) -> None:
    repo = AlertRepository(session_factory)

    created = await repo.create(
        AlertSpec(
            user_id="u1",
            user_email="user@example.com",
            query="laptop",
            condition=AlertCondition.PRICE_BELOW,
            weights={"price": 1.0},
            interval_minutes=15,
            threshold=1000.0,
        )
    )

    await repo.record_evaluation(created.id, condition_met=True, error=None)
    updated = await repo.get_by_id(created.id)

    assert updated is not None
    assert updated.last_checked_at is not None
    assert updated.last_triggered_at is not None
