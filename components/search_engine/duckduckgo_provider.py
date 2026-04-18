from components.search_engine.base import SearchProvider, SearchResult


class DuckDuckGoProvider(SearchProvider):
    def is_available(self) -> bool:
        try:
            import ddgs  # noqa: F401
            return True
        except ImportError:
            return False

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        from ddgs import DDGS
        raw = DDGS().text(query, max_results=max_results)
        return [
            SearchResult(href=r.get("href", ""), title=r.get("title", ""))
            for r in (raw or [])
            if r.get("href")
        ]
