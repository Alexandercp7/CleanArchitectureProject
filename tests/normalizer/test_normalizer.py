from unittest.mock import MagicMock
from adapters.base import RawProduct
from domain.product.product import Product
from normalizer.engine import Normalizer
from normalizer.mapping_loader import MappingLoader

MAPPING = {
    "title": "title",
    "cash_price": "cash_price",
    "installment_price": "installment_price",
    "months_without_interest": "months_without_interest",
    "msi_months": "msi_months",
    "in_stock": "in_stock",
    "delivery_days": "delivery_days",
    "url": "url",
}


def make_normalizer(mapping: dict) -> Normalizer:
    mock_loader = MagicMock(spec=MappingLoader)
    mock_loader.load.return_value = mapping
    return Normalizer(mapping_loader=mock_loader)


def test_maps_title_correctly():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop Dell", "cash_price": "18,999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.title == "Laptop Dell"


def test_converts_cash_price_string_to_float():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "18,999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.cash_price == 18999.0


def test_defaults_in_stock_to_true_when_field_missing():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.in_stock is True


def test_maps_in_stock_to_false_when_field_exists_and_false():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "in_stock": False},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.in_stock is False


def test_defaults_months_without_interest_to_false_when_field_missing():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.months_without_interest is False


def test_returns_none_when_installment_price_is_invalid():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "installment_price": "invalid"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.installment_price is None


def test_maps_installment_price_when_available():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "installment_price": "123"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.installment_price == 123.0


def test_maps_months_without_interest_to_true_when_field_exists():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "months_without_interest": True},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.months_without_interest is True


def test_maps_msi_months_when_available():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "msi_months": "12"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.msi_months == 12


def test_maps_delivery_days_when_available():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="1",
        fields={"title": "Laptop", "cash_price": "999", "delivery_days": "3"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.delivery_days == 3


def test_maps_url_from_source_id():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="https://articulo.mercadolibre.com.mx/MLM-12345",
        fields={"title": "Laptop", "cash_price": "999"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.url == "https://articulo.mercadolibre.com.mx/MLM-12345"


def test_maps_url_from_mapped_field_when_available():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(
        source_id="https://fallback.example/item",
        fields={"title": "Laptop", "cash_price": "999", "url": "https://mapped.example/item"},
    )
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.url == "https://mapped.example/item"