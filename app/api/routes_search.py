from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.config import settings
from app.graph.state import SourceItem
from app.research.search import search
from app.research.rank import rank_sources

router = APIRouter(prefix="/v1", tags=["search"])

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    if not settings.ktrt_api_key:
        return "dev"
    if api_key != settings.ktrt_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key


class SearchRequest(BaseModel):
    query: str
    max_results: int = 8


class SearchResponse(BaseModel):
    query: str
    results: list[SourceItem]


@router.post("/search", response_model=SearchResponse, summary="Raw search endpoint")
async def search_endpoint(
    request: SearchRequest,
    _: str = Depends(_require_api_key),
) -> SearchResponse:
    raw = await search(request.query, request.max_results)
    ranked = rank_sources(raw)
    return SearchResponse(query=request.query, results=ranked)
