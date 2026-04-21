from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias

RawFieldValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True)
class RawProduct:
    source_id: str
    fields: dict[str, RawFieldValue]


class StoreAdapter(ABC):

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_raw_products(self, query: str) -> list[RawProduct]:
        ...