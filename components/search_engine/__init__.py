import os

from components.search_engine.base import SearchProvider, SearchResult
from components.search_engine.duckduckgo_provider import DuckDuckGoProvider
from components.search_engine.serpapi_provider import SerpAPIProvider

__all__ = [
    "SearchResult",
    "SearchProvider",
    "DuckDuckGoProvider",
    "SerpAPIProvider",
    "get_provider",
]


def get_provider(prefer: str | None = None, serpapi_key: str | None = None) -> SearchProvider:
    """
    Return the best available SearchProvider.

    Priority:
      prefer='serpapi'    → SerpAPIProvider (fails fast if key absent)
      prefer='duckduckgo' → DuckDuckGoProvider
      prefer=None         → SerpAPIProvider if SERPAPI_KEY in env, else DuckDuckGoProvider
    """
    if prefer == "serpapi":
        return SerpAPIProvider(api_key=serpapi_key)
    if prefer == "duckduckgo":
        return DuckDuckGoProvider()
    key = serpapi_key or os.getenv("SERPAPI_KEY", "")
    if key:
        return SerpAPIProvider(api_key=key)
    return DuckDuckGoProvider()
