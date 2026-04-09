from __future__ import annotations

import re

import trafilatura

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]


def _sanitize(text: str) -> str:
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def extract_text(html: str, url: str = "") -> str:
    """Extract readable text from HTML, sanitize for prompt injection."""
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )
    if not text:
        return ""
    return _sanitize(text)[:4000]
