from abc import ABC, abstractmethod
from domain.product import Product


class AbstractCache(ABC):

    @abstractmethod
    def get(self, key: str) -> list[Product] | None:
        ...

    @abstractmethod
    def set(self, key: str, value: list[Product], ttl_seconds: int) -> None:
        ...