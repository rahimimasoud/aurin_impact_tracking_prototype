"""
Data capture module for AURIN Impact Tracking Dashboard.

Fetches all data from the Dimensions API and persists it to SQLite.
This module has no Streamlit dependency — progress is reported via callback.
All API interaction is contained here; the rest of the application only reads
from aurin_cache.db via AurinDatabase.
"""
import datetime
import time
from typing import Callable, List, Optional

import dimcli
import pandas as pd

from data.database import AurinDatabase, TREND_FIXED


_AURIN_SEARCH_TERMS = (
    '"\\\"Australian Urban Research Infrastructure Network\\\"'
    ' OR \\\"Australia\'s Spatial Intelligence Network\\\"'
    ' OR (\\\"AURIN\\\" AND \\\"NCRIS\\\")"'
)

_PUBLICATIONS_QUERY = f"""
    search publications for {_AURIN_SEARCH_TERMS}
    return publications[id+title+authors+pages+type+volume+issue+journal+times_cited+date+date_online+category_for+category_sdg+concepts]
"""

_POLICY_QUERY = f"""
    search policy_documents for {_AURIN_SEARCH_TERMS}
    return policy_documents[id+title+year+linkout+publisher_org+publisher_org_country+publisher_org_city]
"""

_GRANTS_QUERY = f"""
    search grants for {_AURIN_SEARCH_TERMS}
    return grants[id+title+start_date+end_date+funder_org_name+funding_usd+funder_org_countries+linkout]
"""

_PATENTS_QUERY = f"""
    search patents for {_AURIN_SEARCH_TERMS}
    return patents[id+title+publication_date+filing_date+assignees+inventor_names+jurisdiction+legal_status+dimensions_url]
"""

# Shared FOR category terms used for both publications and grants trend queries.
# Chunked to stay within the Dimensions API complexity limit (~12 conditions per query).
_TREND_FOR_CATEGORIES = [
    "urban", "planning", "geography", "geomatic", "spatial", "geomatics", "demography",
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


class CaptureError(Exception):
    """Raised when data capture fails with a user-actionable message."""


def build_query_with_dates(
    query: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    date_field: str = "date",
    year_only: bool = False,
) -> str:
    """
    Inject date WHERE/AND clauses into a Dimensions DSL query.

    Args:
        query: Base DSL query string.
        from_date: Start date (YYYY-MM-DD) or None.
        to_date: End date (YYYY-MM-DD) or None.
        date_field: Name of the date field to filter on.
        year_only: If True, extract only the year from dates and use integer comparison.

    Returns:
        Query string with date filters inserted before the RETURN clause.
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
            if "return" in final_query.lower():
                return_idx = final_query.lower().find("return")
                final_query = (
                    final_query[:return_idx].strip()
                    + f"\n{connector} {where_clause}\n"
                    + final_query[return_idx:]
                )
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

        try:
            reported = int(res.stats.get("total_count", 0) or 0)
            max_seen_total = max(max_seen_total, reported)
        except (ValueError, TypeError):
            pass

        if batch_df is None or batch_df.empty:
            if skip < max_seen_total and consecutive_empty < MAX_CONSECUTIVE_EMPTY:
                consecutive_empty += 1
                print(
                    f"[Retry {consecutive_empty}/{MAX_CONSECUTIVE_EMPTY}] "
                    f"empty at skip={skip}, max seen total={max_seen_total}"
                )
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


def _build_trend_query(entity: str, where_country: str, return_fields: str, terms: List[str]) -> str:
    """Build a trend DSL query for a subset of FOR category wildcard terms."""
    conditions = " or\n        ".join(f'category_for.name @ "*{t}*"' for t in terms)
    return f"""    search {entity}
    where {where_country}
    and ({conditions})
    return {entity}[{return_fields}]
"""


class DataCapture:
    """
    Fetches all AURIN data from the Dimensions API and persists it to SQLite.

    Usage::

        capture = DataCapture(api_key, from_date, to_date)
        capture.capture_all(db, progress_callback=lambda f, lbl: print(f, lbl))
    """

    def __init__(
        self,
        api_key: str,
        from_date: Optional[str],
        to_date: Optional[str],
        endpoint: str = "https://app.dimensions.ai",
    ) -> None:
        self.api_key = api_key
        self.from_date = from_date
        self.to_date = to_date
        self.endpoint = endpoint

    def capture_all(
        self,
        db: AurinDatabase,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        """
        Run all capture steps in sequence.

        progress_callback receives (fraction: float 0.0–1.0, label: str).
        Raises CaptureError on authentication failure.
        Per-dataset failures are collected and raised together at the end so
        that a single failing dataset does not abort the remaining ones.
        """
        try:
            dimcli.login(key=self.api_key, endpoint=self.endpoint)
            dsl = dimcli.Dsl()
        except Exception as e:
            raise CaptureError(f"Authentication failed: {e}") from e

        progress_callback(0.0, "Starting data capture…")
        errors: list = []

        progress_callback(0.02, "Fetching AURIN publications…")
        try:
            self._capture_publications(db, dsl)
        except Exception as e:
            errors.append(f"Publications: {e}")
        progress_callback(0.10, "Publications done.")

        progress_callback(0.11, "Fetching policy documents…")
        try:
            self._capture_policy_documents(db, dsl)
        except Exception as e:
            errors.append(f"Policy documents: {e}")
        progress_callback(0.20, "Policy documents done.")

        progress_callback(0.21, "Fetching patents…")
        try:
            self._capture_patents(db, dsl)
        except Exception as e:
            errors.append(f"Patents: {e}")
        progress_callback(0.30, "Patents done.")

        progress_callback(0.31, "Fetching grants…")
        try:
            self._capture_grants(db, dsl)
        except Exception as e:
            errors.append(f"Grants: {e}")
        progress_callback(0.40, "Grants done.")

        try:
            self._capture_research_trend(
                db, dsl,
                lambda f, lbl: progress_callback(0.40 + f * 0.40, lbl),
            )
        except Exception as e:
            errors.append(f"Research trend: {e}")
        progress_callback(0.80, "Research trends done.")

        try:
            self._capture_grant_trend(
                db, dsl,
                lambda f, lbl: progress_callback(0.80 + f * 0.20, lbl),
            )
        except Exception as e:
            errors.append(f"Grant trend: {e}")
        progress_callback(1.0, "All data captured.")

        if errors:
            raise CaptureError(
                "Some datasets failed to capture:\n" + "\n".join(errors)
            )

    # ------------------------------------------------------------------
    # Per-dataset capture methods
    # ------------------------------------------------------------------

    def _capture_publications(self, db: AurinDatabase, dsl) -> None:
        query = build_query_with_dates(_PUBLICATIONS_QUERY, self.from_date, self.to_date)
        result = _query_all_paginated(dsl, query, fetch_sub_entities=True)
        df_main = result["main"]
        df_authors = result["authors"]
        df_affiliations = result["affiliations"]
        df_investigators = result["investigators"]

        # Join times_cited from df_main into df_affiliations
        if (df_affiliations is not None and not df_affiliations.empty
                and df_main is not None and not df_main.empty):
            if (
                'pub_id' in df_affiliations.columns
                and 'id' in df_main.columns
                and 'times_cited' in df_main.columns
            ):
                citation_df = df_main[['id', 'times_cited']].copy()
                df_affiliations = df_affiliations.merge(
                    citation_df,
                    left_on='pub_id',
                    right_on='id',
                    how='left',
                    suffixes=('', '_from_main'),
                )
                if 'times_cited_from_main' in df_affiliations.columns:
                    df_affiliations['times_cited'] = df_affiliations['times_cited_from_main']
                    df_affiliations = df_affiliations.drop(
                        columns=['times_cited_from_main'], errors='ignore'
                    )
                if 'id' in df_affiliations.columns:
                    df_affiliations = df_affiliations.drop(columns=['id'], errors='ignore')

        # Main table: upsert (non-duplicating by 'id')
        if db.upsert_dataframe(df_main, "publications"):
            total = len(db.read_table("publications"))
            db.record_fetch("publications", self.from_date, self.to_date, total)

        # Sub-entity tables: full replace (no stable single-ID key per row)
        db.write_dataframe(df_authors, "authors")
        db.write_dataframe(df_affiliations, "affiliations")
        db.write_dataframe(df_investigators, "investigators")

    def _capture_policy_documents(self, db: AurinDatabase, dsl) -> None:
        query = build_query_with_dates(
            _POLICY_QUERY, self.from_date, self.to_date, date_field="year", year_only=True
        )
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.upsert_dataframe(df, "policy_documents"):
            total = len(db.read_table("policy_documents"))
            db.record_fetch("policy_documents", self.from_date, self.to_date, total)

    def _capture_patents(self, db: AurinDatabase, dsl) -> None:
        query = build_query_with_dates(
            _PATENTS_QUERY, self.from_date, self.to_date, date_field="publication_date"
        )
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.upsert_dataframe(df, "patents"):
            total = len(db.read_table("patents"))
            db.record_fetch("patents", self.from_date, self.to_date, total)

    def _capture_grants(self, db: AurinDatabase, dsl) -> None:
        query = build_query_with_dates(
            _GRANTS_QUERY, self.from_date, self.to_date, date_field="start_date"
        )
        df = _query_all_paginated(dsl, query)["main"]
        df = df if df is not None and not df.empty else pd.DataFrame()
        if db.upsert_dataframe(df, "grants"):
            total = len(db.read_table("grants"))
            db.record_fetch("grants", self.from_date, self.to_date, total)

    def _capture_research_trend(
        self,
        db: AurinDatabase,
        dsl,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        current_year = datetime.datetime.now().year
        from_year = current_year - 10
        years = list(range(from_year, current_year + 1))
        chunks = [
            _TREND_FOR_CATEGORIES[i:i + _TREND_CHUNK_SIZE]
            for i in range(0, len(_TREND_FOR_CATEGORIES), _TREND_CHUNK_SIZE)
        ]
        total_steps = len(years) * len(chunks)
        step = 0
        all_dfs = []

        for year in years:
            for chunk in chunks:
                progress_callback(step / total_steps, f"Loading research trends: {year}…")
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

        df = (
            pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset="id")
            if all_dfs
            else pd.DataFrame()
        )
        if db.upsert_dataframe(df, "research_trend"):
            total = len(db.read_table("research_trend"))
            db.record_fetch("research_trend", TREND_FIXED, TREND_FIXED, total)

    def _capture_grant_trend(
        self,
        db: AurinDatabase,
        dsl,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        current_year = datetime.datetime.now().year
        from_year = current_year - 10
        years = list(range(from_year, current_year + 1))
        chunks = [
            _TREND_FOR_CATEGORIES[i:i + _TREND_CHUNK_SIZE]
            for i in range(0, len(_TREND_FOR_CATEGORIES), _TREND_CHUNK_SIZE)
        ]
        total_steps = len(years) * len(chunks)
        step = 0
        all_dfs = []

        for year in years:
            for chunk in chunks:
                progress_callback(step / total_steps, f"Loading grant trends: {year}…")
                query = _build_trend_query(
                    "grants",
                    'funder_org_countries.name = "Australia"',
                    "id+title+start_date+end_date+funder_org_name+funding_usd+funder_org_countries+category_for+linkout",
                    chunk,
                )
                query = build_query_with_dates(
                    query, f"{year}-01-01", f"{year}-12-31", "start_date"
                )
                chunk_df = _query_all_paginated(dsl, query)["main"]
                if chunk_df is not None and not chunk_df.empty:
                    all_dfs.append(chunk_df)
                step += 1

        df = (
            pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset="id")
            if all_dfs
            else pd.DataFrame()
        )
        if db.upsert_dataframe(df, "grant_trend"):
            total = len(db.read_table("grant_trend"))
            db.record_fetch("grant_trend", TREND_FIXED, TREND_FIXED, total)
