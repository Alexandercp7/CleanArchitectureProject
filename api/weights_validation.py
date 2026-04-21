from domain.weights import ALLOWED_WEIGHT_KEYS


def validate_weights_payload(weights: dict[str, float]) -> dict[str, float]:
    invalid_keys = sorted(set(weights) - set(ALLOWED_WEIGHT_KEYS))
    if invalid_keys:
        raise ValueError(
            "Invalid weight keys: "
            + ", ".join(invalid_keys)
            + ". Allowed keys: "
            + ", ".join(sorted(ALLOWED_WEIGHT_KEYS))
        )

    for key, value in weights.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Weight '{key}' must be between 0.0 and 1.0")

    return weights