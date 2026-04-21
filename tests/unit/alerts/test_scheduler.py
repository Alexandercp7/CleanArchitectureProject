from datetime import datetime, timezone

import pytest

from alerts.evaluation import EvaluationResult
from alerts.scheduler import AlertScheduler
from domain.alert import Alert, AlertCondition


class FakeRepo:
    async def get_active(self):
        return [
            Alert(
                id="a1",
                user_id="u1",
                user_email="u@example.com",
                query="laptop",
                condition=AlertCondition.IN_STOCK,
                threshold=None,
                weights={"price": 1.0},
                interval_minutes=15,
                active=True,
                created_at=datetime.now(tz=timezone.utc),
            )
        ]

    async def record_evaluation(self, alert_id: str, condition_met: bool, error: str | None = None):
        self.last = (alert_id, condition_met, error)


class FakeOrchestrator:
    async def search_and_rank(self, request):
        return []


class FakeTracker:
    def evaluate(self, alert, products):
        return EvaluationResult(alert_id=alert.id, condition_met=False)


class FakeNotifier:
    async def notify(self, alert, products):
        return None


@pytest.mark.asyncio
async def test_tick_persists_evaluation() -> None:
    repo = FakeRepo()
    scheduler = AlertScheduler(FakeOrchestrator(), repo, FakeTracker(), FakeNotifier())

    await scheduler._tick()

    assert repo.last[0] == "a1"


def test_start_requires_running_event_loop() -> None:
    scheduler = AlertScheduler(FakeOrchestrator(), FakeRepo(), FakeTracker(), FakeNotifier())
    with pytest.raises(RuntimeError):
        scheduler.start()
