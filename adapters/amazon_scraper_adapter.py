import re
import httpx
import unicodedata
from bs4 import BeautifulSoup
from adapters.base import RawProduct, StoreAdapter

BASE_URL = "https://www.amazon.com.mx/s?k={query}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9",
}


class AmazonScraperAdapter(StoreAdapter):

    @property
    def source_name(self) -> str:
        return "amazonscraperadapter"

    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def fetch_raw_products(self, query: str) -> list[RawProduct]:
        url = BASE_URL.format(query=query.replace(" ", "+"))
        response = self._http_client.get(url, headers=HEADERS)
        response.raise_for_status()
        return self._parse_products(response.text)

    def _parse_products(self, html: str) -> list[RawProduct]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.puis-card-container")
        return [
            self._parse_card(card)
            for card in cards
            if self._is_valid_card(card)
        ]

    def _is_valid_card(self, card) -> bool:
        return (
            card.select_one("h2 span") is not None
            and card.select_one("span.a-offscreen") is not None
        )

    def _parse_card(self, card) -> RawProduct:
        title = self._extract_title(card)
        cash_price = self._extract_cash_price(card)
        installment_price, msi_months = self._extract_installments(card)
        delivery_days = self._extract_delivery_days(card)
        url = self._extract_url(card)

        return RawProduct(
            source_id=url,
            fields={
                "title": title,
                "cash_price": cash_price,
                "installment_price": installment_price,
                "months_without_interest": msi_months is not None,
                "msi_months": msi_months,
                "in_stock": True,
                "delivery_days": delivery_days,
                "url": url,
            },
        )

    def _extract_title(self, card) -> str:
        tag = card.select_one("h2 span")
        return tag.text.strip() if tag else "Not specified"

    def _extract_cash_price(self, card) -> str:
        tag = card.select_one("span.a-price:not(.a-text-price) span.a-offscreen")
        if tag is None:
            tag = card.select_one("span.a-offscreen")
        return tag.text.strip().replace("$", "").replace(",", "") if tag else "0"

    def _extract_installments(self, card) -> tuple[str | None, int | None]:
        installment_tag = card.select_one("span.a-price.a-text-price span.a-offscreen")
        months_tag = card.select_one("span.a-size-base.a-color-secondary")

        if not installment_tag or not months_tag:
            return None, None

        months_text = months_tag.text.strip().lower()
        normalized_text = unicodedata.normalize("NFKD", months_text).encode("ascii", "ignore").decode("ascii")
        normalized_text = " ".join(normalized_text.split())

        if "sin interes" not in normalized_text:
            return None, None

        match = re.search(r"(\d+)\s*meses", normalized_text)
        if not match:
            return None, None

        installment_price = installment_tag.text.strip().replace("$", "").replace(",", "")
        return installment_price, int(match.group(1))

    def _extract_delivery_days(self, card) -> int | None:
        delivery_tag = card.select_one("div.udm-primary-delivery-message")
        if not delivery_tag:
            return None

        delivery_text = delivery_tag.text.strip().lower()
        normalized_text = unicodedata.normalize("NFKD", delivery_text).encode("ascii", "ignore").decode("ascii")

        if "hoy" in normalized_text:
            return 0
        if "manana" in normalized_text:
            return 1

        match = re.search(r"(\d+)\s*(?:dias|dia)", normalized_text)
        if match:
            return int(match.group(1))
        return None

    def _extract_url(self, card) -> str:
        tag = card.select_one("a.a-link-normal")
        if not tag:
            return ""
        href = tag.get("href", "")
        return f"https://www.amazon.com.mx{href}" if href.startswith("/") else href