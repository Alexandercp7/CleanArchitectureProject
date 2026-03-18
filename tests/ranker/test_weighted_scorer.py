from domain.product import Product
from ranker.weighted_scorer import WeightedScorer


def make_product(**overrides) -> Product:
    defaults = dict(
        title="Laptop",
        price=1000.0,
        in_stock=True,
        delivery_days=5,
        source="mercadolibre",
    )
    return Product(**{**defaults, **overrides})


def test_cheaper_product_ranks_first_on_price_weight():
    scorer = WeightedScorer()
    cheap = make_product(price=500.0)
    expensive = make_product(price=9000.0)
    weights = {"price": 1.0, "availability": 0.0, "delivery": 0.0}

    ranked = scorer.score_all([expensive, cheap], weights)

    assert ranked[0].price == 500.0


def test_in_stock_product_ranks_first_on_availability_weight():
    scorer = WeightedScorer()
    available = make_product(in_stock=True)
    unavailable = make_product(in_stock=False)
    weights = {"price": 0.0, "availability": 1.0, "delivery": 0.0}

    ranked = scorer.score_all([unavailable, available], weights)

    assert ranked[0].in_stock is True


def test_faster_delivery_ranks_first_on_delivery_weight():
    scorer = WeightedScorer()
    fast = make_product(delivery_days=1)
    slow = make_product(delivery_days=20)
    weights = {"price": 0.0, "availability": 0.0, "delivery": 1.0}

    ranked = scorer.score_all([slow, fast], weights)

    assert ranked[0].delivery_days == 1


def test_returns_empty_list_when_no_products():
    scorer = WeightedScorer()
    ranked = scorer.score_all([], {"price": 1.0})

    assert ranked == []


def test_missing_delivery_days_ranks_last_on_delivery_weight():
    scorer = WeightedScorer()
    with_days = make_product(delivery_days=5)
    without_days = make_product(delivery_days=None)
    weights = {"price": 0.0, "availability": 0.0, "delivery": 1.0}

    ranked = scorer.score_all([without_days, with_days], weights)

    assert ranked[0].delivery_days == 5     