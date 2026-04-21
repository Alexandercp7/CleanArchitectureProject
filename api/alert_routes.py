from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from alerts.repository import AlertRepository, AlertSpec
from api.dependencies import get_current_user
from domain.alert import AlertCondition
from domain.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@dataclass(frozen=True)
class AlertRouteDependencies:
    repo: AlertRepository


def get_alert_dependencies() -> AlertRouteDependencies:
    raise RuntimeError("Dependency provider must be overridden by main.create_app")


class CreateAlertBody(BaseModel):
    query: str = Field(min_length=1)
    condition: AlertCondition
    interval_minutes: int = Field(gt=0)
    weights: dict[str, float] = Field(default_factory=lambda: {"price": 1.0})
    threshold: float | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: CreateAlertBody,
    user: User = Depends(get_current_user),
    deps: AlertRouteDependencies = Depends(get_alert_dependencies),
) -> dict[str, str]:
    spec = AlertSpec(
        user_id=user.id,
        user_email=user.email,
        query=body.query,
        condition=body.condition,
        weights=body.weights,
        interval_minutes=body.interval_minutes,
        threshold=body.threshold,
    )
    alert = await deps.repo.create(spec)
    return {"id": alert.id}


@router.get("")
async def list_alerts(
    user: User = Depends(get_current_user),
    deps: AlertRouteDependencies = Depends(get_alert_dependencies),
) -> list[dict[str, str | bool | None]]:
    alerts = await deps.repo.get_by_user(user.id)
    return [
        {
            "id": alert.id,
            "query": alert.query,
            "condition": alert.condition.value,
            "active": alert.active,
            "last_error": alert.last_error,
        }
        for alert in alerts
    ]


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    deps: AlertRouteDependencies = Depends(get_alert_dependencies),
) -> None:
    did_deactivate = await deps.repo.deactivate(alert_id=alert_id, requesting_user_id=user.id)
    if not did_deactivate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
