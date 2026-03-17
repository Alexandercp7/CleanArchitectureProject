import httpx
from unittest.mock import MagicMock
from adapters.mercadolibre_scraper_adapter import MercadoLibreScraperAdapter

HTML_FIXTURE = """
<div class="poly-card__content">
  <h3 class="poly-component__title-wrapper">
    <a class="poly-component__title">Laptop Dell XPS</a>
  </h3>
  <div class="poly-component__price">
    <s><span class="andes-money-amount__fraction">25,000</span></s>
    <span class="andes-money-amount__fraction">18,999</span>
  </div>
  <div class="poly-component__shipping">Free shipping</div>
</div>
"""

HTML_NO_RESULTS = "<html><body><p>No results found</p></body></html>"


def make_adapter(html: str) -> MercadoLibreScraperAdapter:
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = MagicMock(
        status_code=200,
        text=html,
        raise_for_status=lambda: None,
    )
    return MercadoLibreScraperAdapter(http_client=mock_client)


def test_returns_product_with_correct_title():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["title"] == "Laptop Dell XPS"


def test_returns_current_price_not_crossed_out():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["price"] == "18,999"


def test_returns_free_shipping_when_available():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["shipping"] == "Free shipping"


def test_returns_empty_list_when_no_products_found():
    adapter = make_adapter(HTML_NO_RESULTS)
    results = adapter.fetch_raw_products("laptop")
    assert results == []