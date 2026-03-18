from unittest.mock import MagicMock
from adapters.base import RawProduct
from domain.product import Product
from normalizer.engine import Normalizer
from normalizer.mapping_loader import MappingLoader

MAPPING = {
    "title": "title",
    "price": "price",
    "in_stock": "in_stock",
    "delivery_days": "delivery_days",
}


def make_normalizer(mapping: dict) -> Normalizer:
    mock_loader = MagicMock(spec=MappingLoader)
    mock_loader.load.return_value = mapping
    return Normalizer(mapping_loader=mock_loader)


def test_maps_title_correctly():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop Dell", "price": "18,999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.title == "Laptop Dell"


def test_converts_price_string_to_float():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "price": "18,999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.price == 18999.0


def test_defaults_in_stock_to_true_when_field_missing():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "price": "999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.in_stock is True


def test_defaults_delivery_days_to_none_when_field_missing():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "price": "999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.delivery_days is None


def test_sets_source_name_on_product():
    normalizer = make_normalizer(MAPPING)
    raw = RawProduct(source_id="1", fields={"title": "Laptop", "price": "999"})
    product = normalizer.normalize_to_product(raw, "mercadolibre")
    assert product.source == "mercadolibre"