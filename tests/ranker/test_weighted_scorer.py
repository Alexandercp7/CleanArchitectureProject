from domain.product.product import Product
from ranker.weighted_scorer import WeightedScorer


def make_product(**overrides) -> Product:
    defaults = dict(
        title="Laptop",
        cash_price=1000.0,
        installment_price=None,
        months_without_interest=False,
        msi_months=None,
        in_stock=True,
        delivery_days=None,
        url="https://example.com/product",
    )
    return Product(**{**defaults, **overrides})


def test_cheaper_product_ranks_first_on_price_weight():
    scorer = WeightedScorer()
    cheap = make_product(cash_price=500.0)
    expensive = make_product(cash_price=9000.0)
    weights = {"price": 1.0, "months_without_interest": 0.0, "in_stock": 0.0}

    ranked = scorer.score_all([expensive, cheap], weights)

    assert ranked[0].cash_price == 500.0


def test_in_stock_product_ranks_first_on_in_stock_weight():
    scorer = WeightedScorer()
    available = make_product(in_stock=True)
    unavailable = make_product(in_stock=False)
    weights = {"price": 0.0, "months_without_interest": 0.0, "in_stock": 1.0}

    ranked = scorer.score_all([unavailable, available], weights)

    assert ranked[0].in_stock is True


def test_months_without_interest_ranks_first_on_its_weight():
    scorer = WeightedScorer()
    with_months = make_product(months_without_interest=True)
    without_months = make_product(months_without_interest=False)
    weights = {"price": 0.0, "months_without_interest": 1.0, "in_stock": 0.0}

    ranked = scorer.score_all([without_months, with_months], weights)

    assert ranked[0].months_without_interest is True


def test_returns_empty_list_when_no_products():
    scorer = WeightedScorer()
    ranked = scorer.score_all([], {"price": 1.0})

    assert ranked == []


def test_faster_delivery_ranks_first_on_delivery_days_weight():
    scorer = WeightedScorer()
    fast = make_product(delivery_days=1)
    slow = make_product(delivery_days=5)
    weights = {
        "price": 0.0,
        "months_without_interest": 0.0,
        "in_stock": 0.0,
        "delivery_days": 1.0,
    }

    ranked = scorer.score_all([slow, fast], weights)

    assert ranked[0].delivery_days == 1