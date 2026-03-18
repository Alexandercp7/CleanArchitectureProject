from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    title: str
    price: float
    in_stock: bool
    delivery_days: int | None
    source: str