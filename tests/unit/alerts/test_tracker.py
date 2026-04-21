from datetime import datetime, timezone

from alerts.tracker import AlertTracker
from domain.alert import Alert, AlertCondition
from domain.product import Product


def _build_alert(condition: AlertCondition, threshold: float | None = None) -> Alert:
    return Alert(
        id="a1",
        user_id="u1",
        user_email="user@example.com",
        query="laptop",
        condition=condition,
        threshold=threshold,
        weights={"price": 1.0},
        interval_minutes=30,
        active=True,
        created_at=datetime.now(tz=timezone.utc),
    )


def _build_product(in_stock: bool, cash_price: float) -> Product:
    return Product(
        title="Laptop",
        cash_price=cash_price,
        installment_price=None,
        months_without_interest=False,
        msi_months=None,
        in_stock=in_stock,
        delivery_days=None,
        url="https://example.com/p",
    )


def test_in_stock_condition_matches() -> None:
    tracker = AlertTracker()
    alert = _build_alert(AlertCondition.IN_STOCK)

    result = tracker.evaluate(alert, [_build_product(True, 1000.0)])

    assert result.condition_met is True


def test_price_below_condition_matches() -> None:
    tracker = AlertTracker()
    alert = _build_alert(AlertCondition.PRICE_BELOW, threshold=1500.0)

    result = tracker.evaluate(alert, [_build_product(False, 1200.0)])

    assert result.condition_met is True


def test_price_below_without_threshold_returns_error() -> None:
    tracker = AlertTracker()
    alert = _build_alert(AlertCondition.PRICE_BELOW, threshold=None)

    result = tracker.evaluate(alert, [_build_product(False, 1200.0)])

    assert result.has_error() is True
