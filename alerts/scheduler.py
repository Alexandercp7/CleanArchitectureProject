from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from datetime import datetime, timedelta, timezone

from alerts.evaluation import EvaluationResult
from alerts.notifier import Notifier
from alerts.repository import AlertRepository
from alerts.tracker import AlertTracker
from application.search.search_service import SearchRequest, SearchService


class AlertScheduler:
    def __init__(
        self,
        orchestrator: SearchService,
        repo: AlertRepository,
        tracker: AlertTracker,
        notifier: Notifier,
    ) -> None:
        self._orchestrator = orchestrator
        self._repo = repo
        self._tracker = tracker
        self._notifier = notifier
        self._logger = logging.getLogger(__name__)
        self._task: asyncio.Task[None] | None = None
        self._is_running = False

    def start(self) -> None:
        asyncio.get_running_loop()
        if self._task is not None and not self._task.done():
            return
        self._is_running = True
        self._task = asyncio.create_task(self._run(), name="alert-scheduler")

    def stop(self) -> Awaitable[None]:
        if self._task is None:
            return self._completed()
        self._is_running = False
        self._task.cancel()
        return self._wait_for_stop()

    async def _run(self) -> None:
        while self._is_running:
            await self._tick()
            await asyncio.sleep(30)

    async def _tick(self) -> None:
        active_alerts = await self._repo.get_active()
        due_alerts = [alert for alert in active_alerts if self._is_due_for_evaluation(alert)]
        evaluations = await asyncio.gather(
            *(self._evaluate_alert(alert) for alert in due_alerts),
            return_exceptions=True,
        )
        await self._persist_evaluations(evaluations)

    def _is_due_for_evaluation(self, alert) -> bool:
        if alert.last_checked_at is None:
            return True

        next_check_at = alert.last_checked_at + timedelta(minutes=alert.interval_minutes)
        return datetime.now(tz=timezone.utc) >= next_check_at

    async def _evaluate_alert(self, alert) -> EvaluationResult:
        search_request = SearchRequest(query=alert.query, weights=alert.weights)
        products = await self._orchestrator.search_and_rank(search_request)
        result = self._tracker.evaluate(alert=alert, products=products)
        if result.condition_met and not result.has_error():
            await self._notifier.notify(alert=alert, products=products)
        return result

    async def _persist_evaluations(self, evaluations: list[EvaluationResult | Exception]) -> None:
        for item in evaluations:
            if isinstance(item, Exception):
                self._logger.error("Alert evaluation failed", exc_info=item)
                continue
            await self._repo.record_evaluation(
                alert_id=item.alert_id,
                condition_met=item.condition_met,
                error=item.error,
            )

    async def _wait_for_stop(self) -> None:
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _completed(self) -> None:
        return None
