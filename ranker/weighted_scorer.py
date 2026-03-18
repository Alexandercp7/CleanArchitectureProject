from domain.product import Product
from ranker.strategy import RankStrategy


class WeightedScorer(RankStrategy):

    def score_all(
        self, products: list[Product], weights: dict[str, float]
    ) -> list[Product]:
        max_price = max((p.cash_price for p in products), default=1.0)
        max_days = max(
            (p.delivery_days for p in products if p.delivery_days is not None),
            default=1,
        )
        return sorted(
            products,
            key=lambda p: self._compute_score(p, weights, max_price, max_days),
            reverse=True,
        )

    def _compute_score(
        self,
        product: Product,
        weights: dict[str, float],
        max_price: float,
        max_days: int,
    ) -> float:
        return (
            weights.get("price", 0.0) * self._normalize_price(product.cash_price, max_price)
            + weights.get("months_without_interest", 0.0)
            * self._normalize_months_without_interest(product.months_without_interest)
            + weights.get("in_stock", 0.0) * self._normalize_in_stock(product.in_stock)
            + weights.get("delivery_days", 0.0) * self._normalize_delivery_days(product.delivery_days, max_days)
        )

    def _normalize_price(self, price: float, max_price: float) -> float:
        return 1.0 - (price / max_price)

    def _normalize_months_without_interest(self, months_without_interest: bool) -> float:
        return 1.0 if months_without_interest else 0.0

    def _normalize_in_stock(self, in_stock: bool) -> float:
        return 1.0 if in_stock else 0.0

    def _normalize_delivery_days(self, delivery_days: int | None, max_days: int) -> float:
        if delivery_days is None:
            return -1.0
        return 1.0 - (delivery_days / max_days)
