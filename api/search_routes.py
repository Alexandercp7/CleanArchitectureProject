from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from api.weights_validation import validate_weights_payload
from application.search.search_service import SearchService

router = APIRouter(tags=["search"])


class SearchRequestBody(BaseModel):
    query: str = Field(min_length=1)
    weights: dict[str, float] = {
        "price": 0.6,
        "months_without_interest": 0.2,
        "in_stock": 0.2,
        "delivery_days": 0.0,
    }

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, weights: dict[str, float]) -> dict[str, float]:
        return validate_weights_payload(weights)


class ProductResponse(BaseModel):
    cash_price: float
    title: str
    installment_price: float | None
    months_without_interest: bool
    msi_months: int | None
    in_stock: bool
    delivery_days: int | None
    url: str


@dataclass(frozen=True)
class SearchRouteDependencies:
    orchestrator: SearchService


def get_search_dependencies() -> SearchRouteDependencies:
    raise RuntimeError("Dependency provider must be overridden by main.create_app")


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/search", response_model=list[ProductResponse])
async def search(
    body: SearchRequestBody,
    response: Response,
    deps: SearchRouteDependencies = Depends(get_search_dependencies),
) -> list[ProductResponse]:
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    products, from_cache = await deps.orchestrator.search(query=query, weights=body.weights)
    response.headers["X-Cache"] = "HIT" if from_cache else "MISS"
    return [ProductResponse(**vars(product)) for product in products]
