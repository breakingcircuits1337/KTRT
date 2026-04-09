from __future__ import annotations

from app.graph.state import SourceItem


def deduplicate(sources: list[dict]) -> list[dict]:
    """Remove duplicate URLs, keeping first occurrence."""
    seen: set[str] = set()
    unique = []
    for s in sources:
        url = s.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(s)
    return unique


def rank_sources(sources: list[dict]) -> list[SourceItem]:
    """Convert raw search results to SourceItem objects with basic credibility scoring."""
    high_credibility_domains = {
        "arxiv.org", "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov",
        "docs.python.org", "developer.mozilla.org", "github.com",
        "stackoverflow.com", "medium.com", "reuters.com", "apnews.com",
    }
    deduped = deduplicate(sources)
    ranked = []
    for item in deduped:
        url = item.get("url", "")
        credibility = 0.5
        for domain in high_credibility_domains:
            if domain in url:
                credibility = 0.85
                break
        ranked.append(
            SourceItem(
                title=item.get("title", ""),
                url=url,
                snippet=item.get("snippet"),
                published_at=item.get("published_at"),
                source_type=item.get("source_type", "web"),
                credibility=credibility,
            )
        )
    # sort by credibility descending
    ranked.sort(key=lambda s: s.credibility or 0, reverse=True)
    return ranked
