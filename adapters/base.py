from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawProduct:
    source_id: str
    fields: dict[str, Any]


class StoreAdapter(ABC):

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_raw_products(self, query: str) -> list[RawProduct]:
        ...