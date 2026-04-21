from __future__ import annotations

from dataclasses import dataclass

import httpx

from domain.alert import Alert, AlertCondition
from domain.product import Product


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    body: str


class Notifier:
    def __init__(self, http_client: httpx.AsyncClient | None) -> None:
        self._http_client = http_client

    async def notify(self, alert: Alert, products: list[Product]) -> None:
        matching_products = self._select_matching_products(alert=alert, products=products)
        message = self._build_email_message(alert=alert, matching_products=matching_products)
        if self._http_client is None:
            return
        await self._http_client.post(
            "/notify",
            json={
                "recipient": message.recipient,
                "subject": message.subject,
                "body": message.body,
                "alert_id": alert.id,
                "query": alert.query,
                "condition": alert.condition.value,
                "threshold": alert.threshold,
                "matching_products": [
                    {
                        "title": product.title,
                        "cash_price": product.cash_price,
                        "in_stock": product.in_stock,
                        "url": product.url,
                    }
                    for product in matching_products
                ],
            },
        )

    def _build_email_message(self, alert: Alert, matching_products: list[Product]) -> EmailMessage:
        product_count = len(matching_products)
        subject = f"Alert triggered for {alert.query}"
        body = f"Found {product_count} matching products for your alert '{alert.id}'."
        return EmailMessage(recipient=alert.user_email, subject=subject, body=body)

    def _select_matching_products(self, alert: Alert, products: list[Product]) -> list[Product]:
        if alert.condition == AlertCondition.IN_STOCK:
            return [product for product in products if product.in_stock]
        if alert.condition == AlertCondition.PRICE_BELOW and alert.threshold is not None:
            return [product for product in products if product.cash_price <= alert.threshold]
        return []
