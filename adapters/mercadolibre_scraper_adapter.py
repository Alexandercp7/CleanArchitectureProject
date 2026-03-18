import httpx
import re
import unicodedata
from bs4 import BeautifulSoup
from adapters.base import RawProduct, StoreAdapter

BASE_URL = "https://listado.mercadolibre.com.mx/{query}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


class MercadoLibreScraperAdapter(StoreAdapter):

    @property
    def source_name(self) -> str:
        return "mercadolibrescraperadapter"

    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def fetch_raw_products(self, query: str) -> list[RawProduct]:
        url = BASE_URL.format(query=query.replace(" ", "-"))
        response = self._http_client.get(url, headers=HEADERS)
        response.raise_for_status()
        return self._parse_products(response.text)

    def _parse_products(self, html: str) -> list[RawProduct]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.poly-card__content")
        return [
            self._parse_card(card)
            for card in cards
            if self._is_valid_card(card)
        ]

    def _is_valid_card(self, card) -> bool:
        return (
            card.select_one("a.poly-component__title") is not None
            and card.select_one("span.andes-money-amount__fraction") is not None
        )

    def _parse_card(self, card) -> RawProduct:
        title_tag = card.select_one("a.poly-component__title")
        title = title_tag.text.strip()
        link = title_tag.get("href", "").strip()
        cash_price = self._extract_current_price(card)
        installment_price, months_without_interest, msi_months = self._extract_installment_info(card)
        shipping = self._extract_shipping(card)
        delivery_days = self._extract_delivery_days(shipping)

        return RawProduct(
            source_id=link,
            fields={
                "title": title,
                "cash_price": cash_price,
                "installment_price": installment_price,
                "months_without_interest": months_without_interest,
                "msi_months": msi_months,
                "shipping": shipping,
                "delivery_days": delivery_days,
            },
        )

    def _extract_current_price(self, card) -> str:
        current_price = card.select_one("div.poly-price__current span.andes-money-amount__fraction")
        if current_price is None:
            raise ValueError("Current price not found in poly-price__current")
        return current_price.text.strip()

    def _extract_installment_info(self, card) -> tuple[str | None, bool, int | None]:
        installments = card.select_one("span.poly-price__installments")
        if installments is None:
            return None, False, None

        text = installments.text.strip().lower()
        normalized_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        normalized_text = " ".join(normalized_text.split())

        months_without_interest = bool(
            re.search(r"\b\d+\s*(?:mes(?:es)?|x)\b.*\bsin interes(?:es)?\b", normalized_text)
            or re.search(r"\bsin interes(?:es)?\b.*\b\d+\s*(?:mes(?:es)?|x)\b", normalized_text)
        )

        if not months_without_interest:
            return None, False, None

        months_match = re.search(r"\b(\d+)\s*(?:mes(?:es)?|x)\b", normalized_text)
        msi_months = int(months_match.group(1)) if months_match else None

        installment_fraction = installments.select_one("span.andes-money-amount__fraction")
        installment_price = installment_fraction.text.strip() if installment_fraction else None
        return installment_price, True, msi_months

    def _extract_shipping(self, card) -> str:
        shipping_tag = card.select_one("div.poly-component__shipping")
        return shipping_tag.text.strip() if shipping_tag else "Not specified"

    def _extract_delivery_days(self, shipping_text: str) -> int | None:
        text = shipping_text.strip().lower()
        if text == "not specified":
            return None
        if "hoy" in text:
            return 0
        if "mañana" in text or "manana" in text:
            return 1

        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))
        return None