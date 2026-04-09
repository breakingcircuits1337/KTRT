from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_api_key
from app.graph.state import SourceItem
from app.research.search import search
from app.research.rank import rank_sources

router = APIRouter(prefix="/v1", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    max_results: int = 8


class SearchResponse(BaseModel):
    query: str
    results: list[SourceItem]


@router.post("/search", response_model=SearchResponse, summary="Raw search endpoint")
async def search_endpoint(
    request: SearchRequest,
    _: str = Depends(require_api_key),
) -> SearchResponse:
    raw = await search(request.query, request.max_results)
    ranked = rank_sources(raw)
    return SearchResponse(query=request.query, results=ranked)
