"""
Data loading module for AURIN Impact Tracking Dashboard.

Reads data exclusively from the local SQLite cache (aurin_cache.db).
No API calls are made here — use data.capture.DataCapture to populate the DB.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import streamlit as st
import pandas as pd
from data import AurinDatabase, TREND_FIXED


class BaseDataLoader(ABC):
    """Abstract base class for data loaders."""

    @abstractmethod
    def load_data(self, **kwargs) -> Tuple[Optional[pd.DataFrame], ...]:
        pass

    def validate_api_key(self, api_key: str) -> bool:
        return True


# ------------------------------------------------------------------
# Cached DB-reader functions (in-session memoisation via @st.cache_data)
# ------------------------------------------------------------------

@st.cache_data
def _load_dimensions_data(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Tuple[Optional[pd.DataFrame], ...]:
    db = AurinDatabase()
    return (
        db.read_table("publications"),
        db.read_table("authors"),
        db.read_table("affiliations"),
        None,
        db.read_table("investigators"),
    )


@st.cache_data
def _load_policy_documents(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    return AurinDatabase().read_table("policy_documents")


@st.cache_data
def _load_grants(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    return AurinDatabase().read_table("grants")


@st.cache_data
def _load_patents(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    return AurinDatabase().read_table("patents")


@st.cache_data
def _load_research_trend_monitor() -> pd.DataFrame:
    return AurinDatabase().read_table("research_trend")


@st.cache_data
def _load_grant_trend_monitor() -> pd.DataFrame:
    return AurinDatabase().read_table("grant_trend")


# ------------------------------------------------------------------
# Loader classes (public API, unchanged interfaces)
# ------------------------------------------------------------------

class DimensionsDataLoader(BaseDataLoader):
    """Reads AURIN publications and sub-entities from the local cache."""

    def load_data(
        self,
        api_key: str = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[Optional[pd.DataFrame], ...]:
        return _load_dimensions_data(from_date, to_date)


class PolicyDocumentsDataLoader:
    """Reads policy documents from the local cache."""

    def load_data(
        self,
        api_key: str = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> pd.DataFrame:
        return _load_policy_documents(from_date, to_date)


class GrantsDataLoader:
    """Reads grants from the local cache."""

    def load_data(
        self,
        api_key: str = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> pd.DataFrame:
        return _load_grants(from_date, to_date)


class PatentsDataLoader:
    """Reads patents from the local cache."""

    def load_data(
        self,
        api_key: str = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> pd.DataFrame:
        return _load_patents(from_date, to_date)


class ResearchTrendMonitorDataLoader:
    """Reads 10-year AU urban research publications from the local cache."""

    def load_data(self, api_key: str = None, **kwargs) -> pd.DataFrame:
        return _load_research_trend_monitor()


class GrantTrendMonitorDataLoader:
    """Reads 10-year AU urban research grants from the local cache."""

    def load_data(self, api_key: str = None, **kwargs) -> pd.DataFrame:
        return _load_grant_trend_monitor()
