from adapters.base import RawProduct
from domain.product import Product
from normalizer.mapping_loader import MappingLoader

NOT_SPECIFIED = "Not specified"


class Normalizer:

    def __init__(self, mapping_loader: MappingLoader) -> None:
        self._mapping_loader = mapping_loader

    def normalize_to_product(self, raw: RawProduct, source_name: str) -> Product:
        field_map = self._mapping_loader.load(source_name)
        fields = raw.fields
        return Product(
            title=self._extract_title(fields, field_map),
            price=self._extract_price(fields, field_map),
            in_stock=self._extract_in_stock(fields, field_map),
            delivery_days=self._extract_delivery_days(fields, field_map),
            source=source_name,
        )

    def _extract_title(self, fields: dict, field_map: dict) -> str:
        return fields.get(field_map["title"], NOT_SPECIFIED)

    def _extract_price(self, fields: dict, field_map: dict) -> float:
        raw_price = fields.get(field_map["price"], "0")
        return float(str(raw_price).replace(",", ""))

    def _extract_in_stock(self, fields: dict, field_map: dict) -> bool:
        key = field_map.get("in_stock")
        if not key or key not in fields:
            return True
        return bool(fields[key])

    def _extract_delivery_days(self, fields: dict, field_map: dict) -> int | None:
        key = field_map.get("delivery_days")
        if not key or key not in fields:
            return None
        try:
            return int(fields[key])
        except (ValueError, TypeError):
            return None