import os

from components.search_engine.base import SearchProvider, SearchResult

_DEFAULT_ENGINE = "google"


class SerpAPIProvider(SearchProvider):
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    def _resolve_key(self) -> str:
        return self._api_key or os.getenv("SERPAPI_KEY", "")

    def is_available(self) -> bool:
        return bool(self._resolve_key())

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        api_key = self._resolve_key()
        if not api_key:
            raise RuntimeError(
                "SerpAPI key is not set. "
                "Set SERPAPI_KEY in .env or pass --serpapi-key to the agent."
            )
        try:
            from serpapi import GoogleSearch
        except ImportError:
            raise RuntimeError(
                "google-search-results is not installed. "
                "Run: uv add google-search-results"
            )

        params = {
            "q": query,
            "engine": _DEFAULT_ENGINE,
            "num": max_results,
            "api_key": api_key,
        }
        data = GoogleSearch(params).get_dict()
        if "error" in data:
            raise RuntimeError(f"SerpAPI error: {data['error']}")
        return [
            SearchResult(href=r.get("link", ""), title=r.get("title", ""))
            for r in data.get("organic_results", [])
            if r.get("link")
        ]
