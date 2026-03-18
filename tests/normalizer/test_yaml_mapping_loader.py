from normalizer.yaml_mapping_loader import YamlMappingLoader


def test_loads_mapping_file_for_source(tmp_path):
    mappings_dir = tmp_path / "mappings"
    mappings_dir.mkdir()
    (mappings_dir / "mercadolibrescraperadapter.yaml").write_text(
        "title: title\ncash_price: cash_price\ninstallment_price: installment_price\nmonths_without_interest: months_without_interest\nmsi_months: msi_months\nin_stock: in_stock\ndelivery_days: delivery_days\n",
        encoding="utf-8",
    )

    loader = YamlMappingLoader(mappings_dir=mappings_dir)

    mapping = loader.load("mercadolibrescraperadapter")

    assert mapping["title"] == "title"
    assert mapping["cash_price"] == "cash_price"
