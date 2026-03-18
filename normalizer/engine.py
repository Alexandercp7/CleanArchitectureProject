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
            cash_price=self._extract_cash_price(fields, field_map),
            installment_price=self._extract_installment_price(fields, field_map),
            months_without_interest=self._extract_months_without_interest(fields, field_map),
            msi_months=self._extract_msi_months(fields, field_map),
            in_stock=self._extract_in_stock(fields, field_map),
            delivery_days=self._extract_delivery_days(fields, field_map),
            url=self._extract_url(fields, field_map, raw.source_id),
        )

    def _extract_title(self, fields: dict, field_map: dict) -> str:
        return fields.get(field_map["title"], NOT_SPECIFIED)

    def _extract_cash_price(self, fields: dict, field_map: dict) -> float:
        raw_price = fields.get(field_map["cash_price"], "0")
        return float(str(raw_price).replace(",", ""))

    def _extract_installment_price(self, fields: dict, field_map: dict) -> float | None:
        key = field_map.get("installment_price")
        if not key or key not in fields:
            return None
        raw_price = fields.get(key)
        if raw_price in (None, ""):
            return None
        try:
            return float(str(raw_price).replace(",", ""))
        except (ValueError, TypeError):
            return None

    def _extract_months_without_interest(self, fields: dict, field_map: dict) -> bool:
        key = field_map.get("months_without_interest")
        if not key or key not in fields:
            return False

        value = fields[key]
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "yes", "si", "sí"}

    def _extract_in_stock(self, fields: dict, field_map: dict) -> bool:
        key = field_map.get("in_stock")
        if not key or key not in fields:
            return True
        return bool(fields[key])

    def _extract_msi_months(self, fields: dict, field_map: dict) -> int | None:
        key = field_map.get("msi_months")
        if not key or key not in fields:
            return None
        try:
            return int(fields[key])
        except (ValueError, TypeError):
            return None

    def _extract_delivery_days(self, fields: dict, field_map: dict) -> int | None:
        key = field_map.get("delivery_days")
        if not key or key not in fields:
            return None
        try:
            return int(fields[key])
        except (ValueError, TypeError):
            return None

    def _extract_url(self, fields: dict, field_map: dict, source_id: str) -> str:
        key = field_map.get("url")
        if key and key in fields:
            value = str(fields[key]).strip()
            if value:
                return value
        return source_id
