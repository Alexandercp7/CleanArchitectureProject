import httpx
import pytest
from unittest.mock import MagicMock

from adapters.amazon_scraper_adapter import AmazonScraperAdapter

HTML_FIXTURE = """
<div class="puis-card-container">
  <h2><span>Laptop Amazon Test</span></h2>
  <a class="a-link-normal" href="/dp/B0TEST123">Ver producto</a>

  <span class="a-price a-price-whole">
    <span class="a-offscreen">$15,999</span>
  </span>

  <span class="a-price a-text-price">
    <span class="a-offscreen">$1,333</span>
  </span>
  <span class="a-size-base a-color-secondary">12 meses sin intereses</span>

  <div class="udm-primary-delivery-message">Llega en 2 días</div>
</div>
"""

HTML_NO_MSI = """
<div class="puis-card-container">
  <h2><span>Laptop Amazon Sin MSI</span></h2>
  <a class="a-link-normal" href="/dp/B0NOMSI99">Ver producto</a>

  <span class="a-price a-price-whole">
    <span class="a-offscreen">$9,999</span>
  </span>

  <span class="a-price a-text-price">
    <span class="a-offscreen">$833</span>
  </span>
  <span class="a-size-base a-color-secondary">12 meses de $833</span>

  <div class="udm-primary-delivery-message">Llega mañana</div>
</div>
"""


def make_adapter(html: str) -> AmazonScraperAdapter:
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = MagicMock(
        status_code=200,
        text=html,
        raise_for_status=lambda: None,
    )
    return AmazonScraperAdapter(http_client=mock_client)


@pytest.mark.asyncio
async def test_returns_cash_price_from_non_text_price_node():
    adapter = make_adapter(HTML_FIXTURE)
    results = await adapter.fetch_raw_products("laptop")

    assert results[0].fields["cash_price"] == "15999"


@pytest.mark.asyncio
async def test_sets_msi_fields_only_when_text_indicates_sin_intereses():
    adapter = make_adapter(HTML_FIXTURE)
    results = await adapter.fetch_raw_products("laptop")

    assert results[0].fields["months_without_interest"] is True
    assert results[0].fields["msi_months"] == 12
    assert results[0].fields["installment_price"] == "1333"


@pytest.mark.asyncio
async def test_does_not_set_msi_fields_when_no_sin_intereses_text():
    adapter = make_adapter(HTML_NO_MSI)
    results = await adapter.fetch_raw_products("laptop")

    assert results[0].fields["months_without_interest"] is False
    assert results[0].fields["msi_months"] is None
    assert results[0].fields["installment_price"] is None
    assert results[0].fields["delivery_days"] == 1
