from __future__ import annotations

from dataclasses import dataclass

import httpx

from domain.alert import Alert
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
        message = self._build_email_message(alert=alert, products=products)
        if self._http_client is None:
            return
        await self._http_client.post(
            "/notify",
            json={
                "recipient": message.recipient,
                "subject": message.subject,
                "body": message.body,
            },
        )

    def _build_email_message(self, alert: Alert, products: list[Product]) -> EmailMessage:
        product_count = len(products)
        subject = f"Alert triggered for {alert.query}"
        body = f"Found {product_count} matching products for your alert '{alert.id}'."
        return EmailMessage(recipient=alert.user_email, subject=subject, body=body)
