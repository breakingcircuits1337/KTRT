from __future__ import annotations

import httpx
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAX_RESULTS = 8


async def tavily_search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Search via Tavily and return a list of source dicts."""
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY not set — skipping search")
        return []

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
        resp = await client.post("https://api.tavily.com/search", json=payload)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:600],
                "published_at": item.get("published_date"),
                "source_type": "web",
            }
        )
    return results


async def exa_search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Search via Exa and return source dicts."""
    if not settings.exa_api_key:
        logger.warning("EXA_API_KEY not set — skipping Exa search")
        return []

    headers = {"x-api-key": settings.exa_api_key, "Content-Type": "application/json"}
    payload = {
        "query": query,
        "numResults": max_results,
        "useAutoprompt": True,
        "contents": {"text": {"maxCharacters": 600}},
    }
    async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
        resp = await client.post(
            "https://api.exa.ai/search", headers=headers, json=payload
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": (item.get("text") or "")[:600],
                "published_at": item.get("publishedDate"),
                "source_type": "web",
            }
        )
    return results


async def searxng_search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Search via a self-hosted SearXNG JSON endpoint and return source dicts."""
    if not settings.searxng_url:
        logger.warning("SEARXNG_URL not set — skipping SearXNG search")
        return []

    base = settings.searxng_url.rstrip("/")
    params = {"q": query, "format": "json"}
    async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
        resp = await client.get(f"{base}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": (item.get("content") or "")[:600],
                "published_at": item.get("publishedDate"),
                "source_type": "web",
            }
        )
    return results


async def search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Try SearXNG, then Tavily, then Exa. Logs an error if all providers fail."""
    if not (settings.searxng_url or settings.tavily_api_key or settings.exa_api_key):
        logger.error(
            "No search provider configured — set SEARXNG_URL, TAVILY_API_KEY or EXA_API_KEY"
        )
        return []

    if settings.searxng_url:
        try:
            results = await searxng_search(query, max_results)
            if results:
                return results
        except Exception as exc:
            logger.warning("SearXNG search failed, trying Tavily/Exa", error=str(exc))

    if settings.tavily_api_key:
        try:
            return await tavily_search(query, max_results)
        except Exception as exc:
            logger.warning("Tavily search failed, trying Exa", error=str(exc))

    if settings.exa_api_key:
        try:
            return await exa_search(query, max_results)
        except Exception as exc:
            logger.error("Exa search also failed", error=str(exc))

    logger.error("All configured search providers failed — workflow will proceed without sources")
    return []
