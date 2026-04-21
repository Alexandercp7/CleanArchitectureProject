import pytest

from api.weights_validation import validate_weights_payload


def test_accepts_known_keys_with_values_in_range() -> None:
    weights = {
        "price": 0.6,
        "in_stock": 0.2,
        "months_without_interest": 0.2,
        "delivery_days": 0.0,
    }

    assert validate_weights_payload(weights) == weights


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_rejects_values_out_of_range(value: float) -> None:
    with pytest.raises(ValueError):
        validate_weights_payload({"price": value})


def test_rejects_unknown_weight_keys() -> None:
    with pytest.raises(ValueError):
        validate_weights_payload({"price": 0.5, "unexpected": 0.5})
