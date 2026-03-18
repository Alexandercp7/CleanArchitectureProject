from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from orchestrator import SearchOrchestrator, SearchRequest

app = FastAPI(title="Search Orchestrator API")


class SearchRequestBody(BaseModel):
    query: str
    weights: dict[str, float] = {
        "price": 0.6,
        "months_without_interest": 0.2,
        "in_stock": 0.2,
        "delivery_days": 0.0,
    }


class ProductResponse(BaseModel):
    cash_price: float
    title: str
    installment_price: float | None
    months_without_interest: bool
    msi_months: int | None
    in_stock: bool
    delivery_days: int | None
    url: str


def create_router(orchestrator: SearchOrchestrator) -> FastAPI:

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/search", response_model=list[ProductResponse])
    def search(body: SearchRequestBody, response: Response):
        if not body.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        results, from_cache = orchestrator.search_and_rank_with_cache_status(
            SearchRequest(query=body.query, weights=body.weights)
        )
        response.headers["X-Cache"] = "HIT" if from_cache else "MISS"
        return [ProductResponse(**vars(p)) for p in results]

    return app