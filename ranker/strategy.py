from abc import ABC, abstractmethod
from domain.product.product import Product


class RankStrategy(ABC):

    @abstractmethod
    def score_all(
        self, products: list[Product], weights: dict[str, float]
    ) -> list[Product]:
        ...