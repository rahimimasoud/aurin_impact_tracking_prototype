"""
Data loading module for AURIN Impact Tracking Dashboard.
Provides abstract base class and concrete implementation for loading data from Dimensions API.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import time
import streamlit as st
import dimcli
import pandas as pd
from data import AurinDatabase, TREND_FIXED


_AURIN_SEARCH_TERMS = (
    '"\\\"Australian Urban Research Infrastructure Network\\\"'
    ' OR \\\"Australia\'s Spatial Intelligence Network\\\"'
    ' OR (\\\"AURIN\\\" AND \\\"NCRIS\\\")"'
)


class BaseDataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load_data(self, api_key: str) -> Tuple[Optional[pd.DataFrame], ...]:
        """
        Load data from the data source.
        
        Args:
            api_key: API key for authentication
            
        Returns:
            Tuple of DataFrames (main, authors, affiliations, funders, investigators)
        """
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate the API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass


def _validate_api_key(api_key: str) -> bool:
    """
    Validate the API key.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not api_key.strip():
        return False
    return True


def build_query_with_dates(
    query: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    date_field: str = "date",
    year_only: bool = False,
) -> str:
    """
    Build query string with date filters.

    Args:
        query: Base query string
        from_date: Start date for filtering (YYYY-MM-DD format) or None
        to_date: End date for filtering (YYYY-MM-DD format) or None
        date_field: Name of the date field to filter on (default: "date")
        year_only: If True, extract only the year from dates and use integer comparison

    Returns:
        Query string with date filters applied
    """
    final_query = query
    if from_date or to_date:
        where_clauses = []
        if year_only:
            if from_date:
                where_clauses.append(f'{date_field} >= {from_date[:4]}')
            if to_date:
                where_clauses.append(f'{date_field} <= {to_date[:4]}')
        else:
            if from_date:
                where_clauses.append(f'{date_field} >= "{from_date}"')
            if to_date:
                where_clauses.append(f'{date_field} <= "{to_date}"')

        if where_clauses:
            where_clause = " and ".join(where_clauses)
            has_where = "where" in final_query.lower()
            connector = "and" if has_where else "where"
            # Insert date clause before return statement
            if "return" in final_query.lower():
                return_idx = final_query.lower().find("return")
                final_query = final_query[:return_idx].strip() + f"\n{connector} {where_clause}\n" + final_query[return_idx:]
            else:
                final_query = final_query.strip() + f"\n{connector} {where_clause}"
    return final_query


def _query_all_paginated(
    dsl,
    query: str,
    limit: int = 1000,
    fetch_sub_entities: bool = False,
) -> dict:
    """
    Paginator that handles the Dimensions API's inconsistent total_count.

    dimcli's query_iterative stops when it receives fewer than `limit` records
    in a page, which causes premature termination when the API momentarily
    underestimates its total — a known behaviour of distributed search clusters.

    This function:
    - Stops only when a page returns 0 records (truly exhausted)
    - Tracks the highest total_count ever reported and retries empty pages up
      to 3 times before giving up, in case the total temporarily dips below skip
    - Deduplicates records by `id` across pages
    - Optionally collects sub-entity frames (authors, affiliations, investigators)

    Note: the Dimensions API hard-caps skip at 50,000 per query. For datasets
    larger than that, split by year and call this function once per year.

    Returns a dict with keys: 'main', 'authors', 'affiliations', 'investigators'.
    """
    seen_ids: set = set()
    main_dfs, author_dfs, affil_dfs, invest_dfs = [], [], [], []
    skip = 0
    max_seen_total = 0
    consecutive_empty = 0
    MAX_CONSECUTIVE_EMPTY = 3
    API_SKIP_CAP = 50_000

    print(f"Starting iteration with limit={limit} skip=0 ...")

    while skip < API_SKIP_CAP:
        t0 = time.time()
        q = query.rstrip() + f"\nlimit {limit} skip {skip}"
        res = dsl.query(q)
        elapsed = time.time() - t0

        if res.errors:
            break

        try:
            batch_df = res.as_dataframe()
        except Exception:
            break

        # Track the highest total the API has ever reported for this query
        try:
            reported = int(res.stats.get("total_count", 0) or 0)
            max_seen_total = max(max_seen_total, reported)
        except (ValueError, TypeError):
            pass

        if batch_df is None or batch_df.empty:
            # The API sometimes returns nothing when total_count dips below skip.
            # Retry a few times before accepting this as the real end.
            if skip < max_seen_total and consecutive_empty < MAX_CONSECUTIVE_EMPTY:
                consecutive_empty += 1
                print(f"[Retry {consecutive_empty}/{MAX_CONSECUTIVE_EMPTY}] empty at skip={skip}, max seen total={max_seen_total}")
                time.sleep(2)
                continue
            break

        consecutive_empty = 0
        batch_size = len(batch_df)
        print(f"{skip}-{skip + batch_size} / {max_seen_total or '?'} ({elapsed:.2f}s)")

        if "id" in batch_df.columns:
            new_rows = batch_df[~batch_df["id"].isin(seen_ids)]
            seen_ids.update(batch_df["id"].tolist())
        else:
            new_rows = batch_df

        if not new_rows.empty:
            main_dfs.append(new_rows)

        if fetch_sub_entities:
            for method_name, target in [
                ("as_dataframe_authors", author_dfs),
                ("as_dataframe_authors_affiliations", affil_dfs),
                ("as_dataframe_investigators", invest_dfs),
            ]:
                fn = getattr(res, method_name, None)
                if fn is not None:
                    try:
                        sub_df = fn()
                        if sub_df is not None and not sub_df.empty:
                            target.append(sub_df)
                    except Exception:
                        pass

        skip += batch_size

    final_main = pd.concat(main_dfs, ignore_index=True) if main_dfs else pd.DataFrame()
    final_ids = set(final_main["id"].tolist()) if "id" in final_main.columns else None

    def _build_sub(dfs, pub_id_col="pub_id"):
        if not dfs:
            return None
        df = pd.concat(dfs, ignore_index=True)
        if final_ids is not None and pub_id_col in df.columns:
            df = df[df[pub_id_col].isin(final_ids)]
        try:
            return df.drop_duplicates()
        except TypeError:
            # Some columns (e.g. 'affiliations') contain lists which are not hashable.
            # Deduplicate only on columns whose sampled values are all scalar.
            safe_cols = [
                c for c in df.columns
                if not any(isinstance(v, (list, dict)) for v in df[c].dropna().head(20))
            ]
            return df.drop_duplicates(subset=safe_cols) if safe_cols else df

    return {
        "main": final_main,
        "authors": _build_sub(author_dfs),
        "affiliations": _build_sub(affil_dfs),
        "investigators": _build_sub(invest_dfs),
    }


@st.cache_data
def _load_dimensions_data(api_key: str, endpoint: str, query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], ...]:
    """
    Cached function to load and process AURIN data from Dimensions API.
    
    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint
        query: Query string for fetching publications
        from_date: Start date for filtering (YYYY-MM-DD format) or None
        to_date: End date for filtering (YYYY-MM-DD format) or None
        
    Returns:
        Tuple of DataFrames (main, authors, affiliations, funders, investigators)
    """
    db = AurinDatabase()
    if db.is_cached("publications", from_date, to_date):
        return (
            db.read_table("publications"),
            db.read_table("authors"),
            db.read_table("affiliations"),
            None,
            db.read_table("investigators"),
        )

    try:
        if not _validate_api_key(api_key):
            st.error("Please enter your Dimensions API key in the sidebar to load data.")
            return None, None, None, None, None

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()
        
        # Build query with date filters if provided
        final_query = build_query_with_dates(query, from_date, to_date)
        result = _query_all_paginated(dsl, final_query, fetch_sub_entities=True)
        df_aurin_main = result["main"]
        df_authors = result["authors"]
        df_affiliations = result["affiliations"]
        df_funders = None
        df_investigators = result["investigators"]
        
        # Join times_cited from df_aurin_main to df_affiliations
        # Join on pub_id (df_affiliations) and id (df_aurin_main)
        if df_affiliations is not None and not df_affiliations.empty and df_aurin_main is not None and not df_aurin_main.empty:
            if 'pub_id' in df_affiliations.columns and 'id' in df_aurin_main.columns and 'times_cited' in df_aurin_main.columns:
                # Create a subset of df_aurin_main with only id and times_cited for the join
                citation_df = df_aurin_main[['id', 'times_cited']].copy()
                # Merge times_cited into df_affiliations based on pub_id = id
                # Use suffixes to handle potential conflicts if times_cited already exists
                df_affiliations = df_affiliations.merge(
                    citation_df,
                    left_on='pub_id',
                    right_on='id',
                    how='left',
                    suffixes=('', '_from_main')
                )
                # Update times_cited column: use merged value if available, otherwise keep original
                if 'times_cited_from_main' in df_affiliations.columns:
                    df_affiliations['times_cited'] = df_affiliations['times_cited_from_main']
                    df_affiliations = df_affiliations.drop(columns=['times_cited_from_main'], errors='ignore')
                # Drop the 'id' column from citation_df that was added during merge
                if 'id' in df_affiliations.columns:
                    df_affiliations = df_affiliations.drop(columns=['id'], errors='ignore')
        
        wrote = db.write_dataframe(df_aurin_main,     "publications")
        db.write_dataframe(df_authors,         "authors")
        db.write_dataframe(df_affiliations,    "affiliations")
        db.write_dataframe(df_investigators,   "investigators")
        if wrote:
            db.record_fetch("publications", from_date, to_date, len(df_aurin_main) if df_aurin_main is not None else 0)

        return df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed. Please check your API key.")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            st.error("❌ Connection error. Please check your internet connection.")
        else:
            st.error(f"❌ Error loading data: {error_msg}")
        return None, None, None, None, None


_POLICY_QUERY = f"""
    search policy_documents for {_AURIN_SEARCH_TERMS}
    return policy_documents[id+title+year+linkout+publisher_org+publisher_org_country+publisher_org_city]
"""


@st.cache_data
def _load_policy_documents(api_key: str, endpoint: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Cached function to load AURIN-related policy documents from Dimensions API.

    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint
        from_date: Start date for filtering (YYYY-MM-DD format) or None
        to_date: End date for filtering (YYYY-MM-DD format) or None

    Returns:
        DataFrame of policy documents or None on failure
    """
    db = AurinDatabase()
    if db.is_cached("policy_documents", from_date, to_date):
        return db.read_table("policy_documents")

    try:
        if not _validate_api_key(api_key):
            return None

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()
        query = build_query_with_dates(_POLICY_QUERY, from_date, to_date, date_field="year", year_only=True)
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.write_dataframe(df, "policy_documents"):
            db.record_fetch("policy_documents", from_date, to_date, len(df))
        return df

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed when loading policy documents.")
        else:
            st.error(f"❌ Error loading policy documents: {error_msg}")
        return None


class PolicyDocumentsDataLoader:
    """Loader for AURIN-relevant policy documents from Dimensions API."""

    def __init__(self, endpoint: str = "https://app.dimensions.ai"):
        self.endpoint = endpoint

    def load_data(self, api_key: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        return _load_policy_documents(api_key, self.endpoint, from_date, to_date)


_GRANTS_QUERY = f"""
    search grants for {_AURIN_SEARCH_TERMS}
    return grants[id+title+start_date+end_date+funder_org_name+funding_usd+funder_org_countries+linkout]
"""


@st.cache_data
def _load_grants(api_key: str, endpoint: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Cached function to load AURIN-related grants from Dimensions API.

    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint
        from_date: Start date for filtering (YYYY-MM-DD format) or None
        to_date: End date for filtering (YYYY-MM-DD format) or None

    Returns:
        DataFrame of grants or None on failure
    """
    db = AurinDatabase()
    if db.is_cached("grants", from_date, to_date):
        return db.read_table("grants")

    try:
        if not _validate_api_key(api_key):
            return None

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()
        query = build_query_with_dates(_GRANTS_QUERY, from_date, to_date, date_field="start_date")
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.write_dataframe(df, "grants"):
            db.record_fetch("grants", from_date, to_date, len(df))
        return df

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed when loading grants.")
        else:
            st.error(f"❌ Error loading grants: {error_msg}")
        return None


class GrantsDataLoader:
    """Loader for AURIN-relevant grants from Dimensions API."""

    def __init__(self, endpoint: str = "https://app.dimensions.ai"):
        self.endpoint = endpoint

    def load_data(self, api_key: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        return _load_grants(api_key, self.endpoint, from_date, to_date)


_PATENTS_QUERY = f"""
    search patents for {_AURIN_SEARCH_TERMS}
    return patents[id+title+publication_date+filing_date+assignees+inventor_names+jurisdiction+legal_status+dimensions_url]
"""


@st.cache_data
def _load_patents(api_key: str, endpoint: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Cached function to load AURIN-related patents from Dimensions API.

    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint
        from_date: Start date for filtering (YYYY-MM-DD format) or None
        to_date: End date for filtering (YYYY-MM-DD format) or None

    Returns:
        DataFrame of patents or None on failure
    """
    db = AurinDatabase()
    if db.is_cached("patents", from_date, to_date):
        return db.read_table("patents")

    try:
        if not _validate_api_key(api_key):
            return None

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()
        query = build_query_with_dates(_PATENTS_QUERY, from_date, to_date, date_field="publication_date")
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.write_dataframe(df, "patents"):
            db.record_fetch("patents", from_date, to_date, len(df))
        return df

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed when loading patents.")
        else:
            st.error(f"❌ Error loading patents: {error_msg}")
        return None


class PatentsDataLoader:
    """Loader for AURIN-relevant patents from Dimensions API."""

    def __init__(self, endpoint: str = "https://app.dimensions.ai"):
        self.endpoint = endpoint

    def load_data(self, api_key: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        return _load_patents(api_key, self.endpoint, from_date, to_date)


# Shared FOR category terms used for both publications and grants trend queries.
# Kept as a list so loaders can chunk them and stay within the Dimensions API
# complexity limit (~12 conditions per query avoids the "too long or complex" warning).
_TREND_FOR_CATEGORIES = [
    "urban", "planning", "geography", "geomatics", "demography",
    "sociology", "community", "geospatial", "transport", "city",
    "regional", "rural", "housing", "infrastructure", "built",
    "civil", "asset management", "population", "social", "economic",
    "environment", "ecological", "ecology", "natural hazards",
    "hydrology", "water", "waste", "mining", "air quality", "energy",
    "sustainable", "sustainability", "commerce", "biodiversity", "epidemiology",
    "policy", "inequalities", "climate", "health", "photogrammetry",
    "remote sensing", "poverty", "wellbeing", "aboriginal", "indigenous",
    "torres strait islander", "development",
]

_TREND_CHUNK_SIZE = 12


def _build_trend_query(entity: str, where_country: str, return_fields: str, terms: list) -> str:
    """Build a trend DSL query for a subset of FOR category wildcard terms."""
    conditions = " or\n        ".join(f'category_for.name @ "*{t}*"' for t in terms)
    return f"""    search {entity}
    where {where_country}
    and ({conditions})
    return {entity}[{return_fields}]
"""


@st.cache_data
def _load_research_trend_monitor(api_key: str, endpoint: str) -> Optional[pd.DataFrame]:
    """
    Cached function to load Australian urban/spatial publications for the Research Trend Monitor.
    Always queries the last 10 years to support comparison windows.

    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint

    Returns:
        DataFrame of publications or empty DataFrame on failure
    """
    db = AurinDatabase()
    if db.is_cached("research_trend", TREND_FIXED, TREND_FIXED, max_age_days=7):
        return db.read_table("research_trend")

    try:
        if not _validate_api_key(api_key):
            return None

        import datetime
        current_year = datetime.datetime.now().year
        from_year = current_year - 10  # 10-year window (inclusive)
        years = list(range(from_year, current_year + 1))

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()

        chunks = [
            _TREND_FOR_CATEGORIES[i:i + _TREND_CHUNK_SIZE]
            for i in range(0, len(_TREND_FOR_CATEGORIES), _TREND_CHUNK_SIZE)
        ]
        total_steps = len(years) * len(chunks)
        step = 0
        all_dfs = []
        progress = st.progress(0, text="Loading research trend data…")
        for year in years:
            for chunk in chunks:
                progress.progress(step / total_steps, text=f"Loading research trends: {year}…")
                query = _build_trend_query(
                    "publications",
                    'research_org_country_names = "Australia"',
                    "id+year+category_for+concepts",
                    chunk,
                )
                query = build_query_with_dates(query, str(year), str(year), "year", year_only=True)
                chunk_df = _query_all_paginated(dsl, query)["main"]
                if chunk_df is not None and not chunk_df.empty:
                    all_dfs.append(chunk_df)
                step += 1
        progress.empty()

        df = pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset="id") if all_dfs else pd.DataFrame()
        if db.write_dataframe(df, "research_trend"):
            db.record_fetch("research_trend", TREND_FIXED, TREND_FIXED, len(df))
        return df

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed when loading trend monitor data.")
        else:
            st.error(f"❌ Error loading trend monitor data: {error_msg}")
        return pd.DataFrame()


class ResearchTrendMonitorDataLoader:
    """Loader for the Research Trend Monitor: 10-year AU urban research publications."""

    def __init__(self, endpoint: str = "https://app.dimensions.ai"):
        self.endpoint = endpoint

    def load_data(self, api_key: str, **kwargs) -> Optional[pd.DataFrame]:
        return _load_research_trend_monitor(api_key, self.endpoint)


@st.cache_data
def _load_grant_trend_monitor(api_key: str, endpoint: str) -> Optional[pd.DataFrame]:
    """
    Cached function to load Australian urban/spatial grants for the Grant Trend Monitor.
    Always queries the last 10 years to support comparison windows.

    Args:
        api_key: Dimensions API key
        endpoint: Dimensions API endpoint

    Returns:
        DataFrame of grants or empty DataFrame on failure
    """
    db = AurinDatabase()
    if db.is_cached("grant_trend", TREND_FIXED, TREND_FIXED, max_age_days=7):
        return db.read_table("grant_trend")

    try:
        if not _validate_api_key(api_key):
            return None

        import datetime
        current_year = datetime.datetime.now().year
        from_year = current_year - 10
        years = list(range(from_year, current_year + 1))

        dimcli.login(key=api_key, endpoint=endpoint)
        dsl = dimcli.Dsl()

        chunks = [
            _TREND_FOR_CATEGORIES[i:i + _TREND_CHUNK_SIZE]
            for i in range(0, len(_TREND_FOR_CATEGORIES), _TREND_CHUNK_SIZE)
        ]
        total_steps = len(years) * len(chunks)
        step = 0
        all_dfs = []
        progress = st.progress(0, text="Loading grant trend data…")
        for year in years:
            for chunk in chunks:
                progress.progress(step / total_steps, text=f"Loading grant trends: {year}…")
                query = _build_trend_query(
                    "grants",
                    'funder_org_countries.name = "Australia"',
                    "id+title+start_date+end_date+funder_org_name+funding_usd+funder_org_countries+category_for+linkout",
                    chunk,
                )
                query = build_query_with_dates(query, f"{year}-01-01", f"{year}-12-31", "start_date")
                chunk_df = _query_all_paginated(dsl, query)["main"]
                if chunk_df is not None and not chunk_df.empty:
                    all_dfs.append(chunk_df)
                step += 1
        progress.empty()

        df = pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset="id") if all_dfs else pd.DataFrame()
        if db.write_dataframe(df, "grant_trend"):
            db.record_fetch("grant_trend", TREND_FIXED, TREND_FIXED, len(df))
        return df

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("❌ Authentication failed when loading grant trend monitor data.")
        else:
            st.error(f"❌ Error loading grant trend monitor data: {error_msg}")
        return pd.DataFrame()


class GrantTrendMonitorDataLoader:
    """Loader for the Grant Trend Monitor: 10-year AU urban research grants."""

    def __init__(self, endpoint: str = "https://app.dimensions.ai"):
        self.endpoint = endpoint

    def load_data(self, api_key: str, **kwargs) -> Optional[pd.DataFrame]:
        return _load_grant_trend_monitor(api_key, self.endpoint)


class DimensionsDataLoader(BaseDataLoader):
    """Concrete implementation of data loader for Dimensions API."""
    
    def __init__(self, endpoint: str = "https://app.dimensions.ai", query: str = None):
        """
        Initialize the Dimensions data loader.
        
        Args:
            endpoint: Dimensions API endpoint
            query: Query string for fetching publications
        """
        self.endpoint = endpoint
        self.query = query or f"""
            search publications for {_AURIN_SEARCH_TERMS}
            return publications[id+title+authors+pages+type+volume+issue+journal+times_cited+date+date_online+category_for+category_sdg+concepts]
        """
    
    def build_query_with_dates(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> str:
        """
        Build query string with date filters.
        
        Args:
            from_date: Start date for filtering (YYYY-MM-DD format) or None
            to_date: End date for filtering (YYYY-MM-DD format) or None
            
        Returns:
            Query string with date filters applied
        """
        return build_query_with_dates(self.query, from_date, to_date)
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate the API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        return _validate_api_key(api_key)
    
    def load_data(self, api_key: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], ...]:
        """
        Load and process AURIN data from Dimensions API.
        
        Args:
            api_key: Dimensions API key
            from_date: Start date for filtering (YYYY-MM-DD format) or None
            to_date: End date for filtering (YYYY-MM-DD format) or None
            
        Returns:
            Tuple of DataFrames (main, authors, affiliations, funders, investigators)
        """
        return _load_dimensions_data(api_key, self.endpoint, self.query, from_date, to_date)

