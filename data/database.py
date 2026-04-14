"""
SQLite persistence layer for the AURIN Impact Tracking Dashboard.

Provides a write-through cache so that data fetched from the Dimensions API
is stored locally and served from SQLite on subsequent sessions, avoiding
repeated costly API calls for the same date range.

Cache invalidation is keyed on (dataset_name, from_date, to_date). Changing
the date filter in the sidebar produces a new cache key and triggers a fresh
API fetch. The trend monitor datasets use a fixed sentinel (TREND_FIXED) as
their date key and additionally support a max_age_days staleness check.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

DB_PATH = Path(__file__).parent / "aurin_cache.db"

# Sentinel value for datasets that have no user-selectable date range.
# The trend monitors always query a fixed 10-year window computed at runtime,
# so they share a single cache key regardless of the calendar date they run.
TREND_FIXED = "TREND_FIXED"

# Registry of columns that contain Python list/dict objects returned by dimcli.
# These must be JSON-serialised before writing to SQLite and deserialised on read.
# If a column listed here is absent from a particular DataFrame, it is silently skipped.
JSON_COLUMNS: Dict[str, List[str]] = {
    "publications":     ["authors", "journal", "category_for", "category_sdg", "concepts"],
    "authors":          ["affiliations"],
    "affiliations":     [],
    "funders":          [],
    "investigators":    [],
    "policy_documents": ["publisher_org"],
    "grants":           ["funder_org_countries"],
    "patents":          ["assignees", "inventor_names"],
    "research_trend":   ["category_for", "concepts"],
    "grant_trend":      ["funder_org_countries", "category_for"],
}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cache_metadata (
    dataset_name  TEXT NOT NULL,
    from_date     TEXT NOT NULL DEFAULT '',
    to_date       TEXT NOT NULL DEFAULT '',
    fetched_at    TEXT NOT NULL,
    row_count     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dataset_name, from_date, to_date)
);
"""


def _serialize_json_columns(df: pd.DataFrame, json_cols: List[str]) -> pd.DataFrame:
    """Convert list/dict columns to JSON strings so they can be stored in SQLite TEXT fields."""
    for col in json_cols:
        if col not in df.columns:
            continue
        df[col] = df[col].apply(
            lambda v: json.dumps(v)
            if v is not None and not (isinstance(v, float) and pd.isna(v))
            else None
        )
    return df


def _deserialize_json_columns(df: pd.DataFrame, json_cols: List[str]) -> pd.DataFrame:
    """Convert JSON strings back to Python objects after reading from SQLite."""
    for col in json_cols:
        if col not in df.columns:
            continue
        df[col] = df[col].apply(lambda v: json.loads(v) if isinstance(v, str) else v)
    return df


class AurinDatabase:
    """
    Thin SQLite wrapper providing schema initialisation, cache metadata
    management, and DataFrame read/write with automatic JSON column handling.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")  # safe for concurrent Streamlit reads
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)

    # ------------------------------------------------------------------
    # Cache metadata helpers
    # ------------------------------------------------------------------

    def is_cached(
        self,
        dataset_name: str,
        from_date: Optional[str],
        to_date: Optional[str],
        max_age_days: Optional[int] = None,
    ) -> bool:
        """
        Return True if a valid cache entry exists for this dataset / date-range pair.

        Args:
            dataset_name: Logical name of the dataset (e.g. "publications").
            from_date: Start date string used in the API query, or None.
            to_date: End date string used in the API query, or None.
            max_age_days: If set, treat cache entries older than this many days as a miss.
        """
        sql = """
            SELECT fetched_at FROM cache_metadata
            WHERE dataset_name=? AND from_date=? AND to_date=?
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(sql, (dataset_name, from_date or "", to_date or "")).fetchone()

        if row is None:
            return False

        if max_age_days is not None:
            fetched_at = datetime.fromisoformat(row["fetched_at"])
            age = datetime.now(timezone.utc) - fetched_at
            if age.days >= max_age_days:
                return False

        return True

    def record_fetch(
        self,
        dataset_name: str,
        from_date: Optional[str],
        to_date: Optional[str],
        row_count: int,
    ) -> None:
        """Upsert a metadata row to mark this dataset/date-range as freshly cached."""
        sql = """
            INSERT OR REPLACE INTO cache_metadata
                (dataset_name, from_date, to_date, fetched_at, row_count)
            VALUES (?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            conn.execute(
                sql,
                (
                    dataset_name,
                    from_date or "",
                    to_date or "",
                    datetime.now(timezone.utc).isoformat(),
                    row_count,
                ),
            )

    def invalidate_all(self) -> None:
        """
        Wipe the cache_metadata table entirely.
        The next load_data call will treat every dataset as a cache miss
        and re-fetch everything from the Dimensions API.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM cache_metadata")

    # ------------------------------------------------------------------
    # DataFrame I/O
    # ------------------------------------------------------------------

    def read_table(self, table_name: str) -> pd.DataFrame:
        """
        Read an entire data table into a DataFrame, deserialising JSON columns.
        Returns an empty DataFrame if the table does not exist or has no rows.
        """
        try:
            with self._connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        except Exception:
            return pd.DataFrame()

        return _deserialize_json_columns(df, JSON_COLUMNS.get(table_name, []))

    def write_dataframe(self, df: Optional[pd.DataFrame], table_name: str) -> bool:
        """
        Write a DataFrame to SQLite, serialising JSON columns first.

        Uses if_exists='replace' which drops and recreates the table so the
        schema always reflects the current DataFrame structure (handles API
        column changes without requiring schema migrations).

        Returns True on success, False otherwise. Callers should only call
        record_fetch when this returns True to avoid poisoning the cache
        with a metadata entry that points to a missing or incomplete table.
        """
        if df is None or df.empty:
            return False

        df_out = _serialize_json_columns(df.copy(), JSON_COLUMNS.get(table_name, []))
        try:
            with self._connect() as conn:
                df_out.to_sql(table_name, conn, if_exists="replace", index=False)
            return True
        except Exception:
            return False

    def upsert_dataframe(
        self,
        df: Optional[pd.DataFrame],
        table_name: str,
        id_column: str = "id",
    ) -> bool:
        """
        Append only rows whose id_column value is not already present in table_name.

        If the table does not yet exist, behaves identically to write_dataframe
        (creates the table from scratch with all rows).

        Returns True if any new rows were written, False otherwise.
        """
        if df is None or df.empty:
            return False

        df_out = _serialize_json_columns(df.copy(), JSON_COLUMNS.get(table_name, []))
        try:
            with self._connect() as conn:
                try:
                    existing_ids = set(
                        pd.read_sql(f"SELECT {id_column} FROM [{table_name}]", conn)[id_column]
                    )
                except Exception:
                    existing_ids = set()

                new_rows = df_out[~df_out[id_column].isin(existing_ids)]
                if new_rows.empty:
                    return False
                if not existing_ids:
                    # Table is empty (or didn't exist): replace so the schema
                    # is always up to date with whatever the API currently returns.
                    new_rows.to_sql(table_name, conn, if_exists="replace", index=False)
                else:
                    new_rows.to_sql(table_name, conn, if_exists="append", index=False)
            return True
        except Exception:
            return False
