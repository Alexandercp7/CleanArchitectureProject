import httpx
from unittest.mock import MagicMock
from adapters.mercadolibre_scraper_adapter import MercadoLibreScraperAdapter

HTML_FIXTURE = """
<div class="poly-card__content">
  <h3 class="poly-component__title-wrapper">
    <a class="poly-component__title" href="https://articulo.mercadolibre.com.mx/MLM-12345-laptop-dell-xps">Laptop Dell XPS</a>
  </h3>
  <div class="poly-component__price">
    <s><span class="andes-money-amount__fraction">25,000</span></s>
        <div class="poly-price__current">
            <span class="andes-money-amount__fraction">18,999</span>
        </div>
  </div>
  <span class="poly-price__installments">
    <span class="andes-money-amount__fraction">1,583</span>
    12x sin interés
  </span>
  <div class="poly-component__shipping">Llega en 3 días</div>
</div>
"""

HTML_THREE_PRICES_FIXTURE = """
<div class="poly-card__content">
    <h3 class="poly-component__title-wrapper">
        <a class="poly-component__title" href="https://articulo.mercadolibre.com.mx/MLM-99999-item">Producto X</a>
    </h3>
    <div class="poly-component__price">
        <s><span class="andes-money-amount__fraction">8,832</span></s>
        <div class="poly-price__current">
            <span class="andes-money-amount__fraction">4,515</span>
        </div>
    </div>
    <span class="poly-price__installments">
        3 meses de <span class="andes-money-amount__fraction">1,505</span>
    </span>
    <div class="poly-component__shipping">Llega en 2 días</div>
</div>
"""

HTML_WITH_INSTALLMENTS_BUT_NO_MSI = """
<div class="poly-card__content">
    <h3 class="poly-component__title-wrapper">
        <a class="poly-component__title" href="https://articulo.mercadolibre.com.mx/MLM-11111-item">Producto sin MSI</a>
    </h3>
    <div class="poly-component__price">
        <div class="poly-price__current">
            <span class="andes-money-amount__fraction">3,937</span>
        </div>
    </div>
    <span class="poly-price__installments">
        3 meses de <span class="andes-money-amount__fraction">1,312</span>
    </span>
    <div class="poly-component__shipping">Llega mañana</div>
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
    assert results[0].fields["cash_price"] == "18,999"


def test_returns_free_shipping_when_available():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["shipping"] == "Llega en 3 días"


def test_returns_product_link_as_source_id():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].source_id == "https://articulo.mercadolibre.com.mx/MLM-12345-laptop-dell-xps"


def test_returns_installment_fields_when_available():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["installment_price"] == "1,583"
    assert results[0].fields["months_without_interest"] is True
    assert results[0].fields["msi_months"] == 12


def test_returns_delivery_days_when_detected_in_shipping_text():
    adapter = make_adapter(HTML_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["delivery_days"] == 3


def test_returns_empty_list_when_no_products_found():
    adapter = make_adapter(HTML_NO_RESULTS)
    results = adapter.fetch_raw_products("laptop")
    assert results == []


def test_returns_cash_price_not_installment_price():
    adapter = make_adapter(HTML_THREE_PRICES_FIXTURE)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["cash_price"] == "4,515"


def test_does_not_set_installment_price_when_not_msi():
    adapter = make_adapter(HTML_WITH_INSTALLMENTS_BUT_NO_MSI)
    results = adapter.fetch_raw_products("laptop")
    assert results[0].fields["months_without_interest"] is False
    assert results[0].fields["installment_price"] is None
    assert results[0].fields["msi_months"] is None
