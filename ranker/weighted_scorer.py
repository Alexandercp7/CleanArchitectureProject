from domain.product import Product
from ranker.strategy import RankStrategy


class WeightedScorer(RankStrategy):

    def score_all(
        self, products: list[Product], weights: dict[str, float]
    ) -> list[Product]:
        max_price = max((p.price for p in products), default=1.0)
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
            weights.get("price", 0.0) * self._normalize_price(product.price, max_price)
            + weights.get("availability", 0.0) * self._normalize_availability(product.in_stock)
            + weights.get("delivery", 0.0) * self._normalize_delivery(product.delivery_days, max_days)
        )

    def _normalize_price(self, price: float, max_price: float) -> float:
        return 1.0 - (price / max_price)

    def _normalize_availability(self, in_stock: bool) -> float:
        return 1.0 if in_stock else 0.0

    def _normalize_delivery(self, days: int | None, max_days: int) -> float:
        if days is None:
            return -1.0
        return 1.0 - (days / max_days)