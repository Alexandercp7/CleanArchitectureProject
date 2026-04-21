from __future__ import annotations

from alerts.evaluation import EvaluationResult
from domain.alert import Alert, AlertCondition
from domain.product import Product


class AlertTracker:
    def evaluate(self, alert: Alert, products: list[Product]) -> EvaluationResult:
        try:
            return self._evaluate(alert=alert, products=products)
        except ValueError as error:
            return EvaluationResult(alert_id=alert.id, condition_met=False, error=str(error))

    def _evaluate(self, alert: Alert, products: list[Product]) -> EvaluationResult:
        if alert.condition == AlertCondition.IN_STOCK:
            has_stocked_product = any(product.in_stock for product in products)
            return EvaluationResult(alert_id=alert.id, condition_met=has_stocked_product)
        if alert.condition == AlertCondition.PRICE_BELOW:
            threshold = self._assert_threshold(alert.threshold)
            has_price_match = any(product.cash_price <= threshold for product in products)
            return EvaluationResult(alert_id=alert.id, condition_met=has_price_match)
        raise ValueError(f"Unsupported condition: {alert.condition}")

    def _assert_threshold(self, threshold: float | None) -> float:
        if threshold is None:
            raise ValueError("PRICE_BELOW alert requires a threshold")
        return threshold
