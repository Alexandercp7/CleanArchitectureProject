from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    title: str
    cash_price: float
    installment_price: float | None
    months_without_interest: bool
    msi_months: int | None
    in_stock: bool
    delivery_days: int | None
    url: str