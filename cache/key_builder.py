import hashlib
import json


def build_cache_key(query: str, weights: dict[str, float]) -> str:
    payload = json.dumps({"query": query, "weights": weights}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
