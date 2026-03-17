import httpx
from bs4 import BeautifulSoup
from adapters.base import RawProduct, StoreAdapter

BASE_URL = "https://listado.mercadolibre.com.mx/{query}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


class MercadoLibreScraperAdapter(StoreAdapter):

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
        title = card.select_one("a.poly-component__title").text.strip()
        price = self._extract_current_price(card)
        shipping = self._extract_shipping(card)

        return RawProduct(
            source_id=title.lower().replace(" ", "-"),
            fields={
                "title": title,
                "price": price,
                "shipping": shipping,
            },
        )

    def _extract_current_price(self, card) -> str:
        fractions = card.select("span.andes-money-amount__fraction")
        return fractions[1].text.strip() if len(fractions) > 1 else fractions[0].text.strip()

    def _extract_shipping(self, card) -> str:
        shipping_tag = card.select_one("div.poly-component__shipping")
        return shipping_tag.text.strip() if shipping_tag else "Not specified"