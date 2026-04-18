from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    href: str
    title: str


class SearchProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def search(self, query: str, max_results: int) -> list[SearchResult]: ...
