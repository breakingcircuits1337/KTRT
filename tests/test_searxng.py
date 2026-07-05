from app.research import search as search_mod


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class _FakeClient:
    """Stands in for httpx.AsyncClient(...) as an async context manager."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, params=None):
        assert params is not None and params["format"] == "json"
        assert url.endswith("/search")
        return _FakeResp(
            {
                "results": [
                    {"title": "T1", "url": "https://a.example", "content": "snippet one"},
                    {"title": "T2", "url": "https://b.example", "content": "snippet two"},
                ]
            }
        )


async def test_searxng_search_maps_results(monkeypatch):
    monkeypatch.setattr(search_mod.settings, "searxng_url", "http://searx.local:8080/")
    monkeypatch.setattr(search_mod.httpx, "AsyncClient", _FakeClient)

    out = await search_mod.searxng_search("hello", max_results=8)

    assert out == [
        {
            "title": "T1",
            "url": "https://a.example",
            "snippet": "snippet one",
            "published_at": None,
            "source_type": "web",
        },
        {
            "title": "T2",
            "url": "https://b.example",
            "snippet": "snippet two",
            "published_at": None,
            "source_type": "web",
        },
    ]


async def test_searxng_search_returns_empty_when_unconfigured(monkeypatch):
    monkeypatch.setattr(search_mod.settings, "searxng_url", "")
    out = await search_mod.searxng_search("hello")
    assert out == []
