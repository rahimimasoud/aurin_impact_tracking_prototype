"""
Shared data helpers for the Research Trend Monitor sections.
"""
from typing import Optional
import re

import pandas as pd

from ._constants import FOR_TIERS


def for_division(name: str) -> Optional[str]:
    """Return the first 4 digits of a FOR code string (e.g. '330401 ...' → '3304')."""
    m = re.match(r"^(\d{4})", str(name))
    return m.group(1) if m else None


def explode_with_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode category_for to one row per FOR item (filtered to FOR_TIERS),
    returning columns: pub_id, year, for_name, for_division.
    """
    if "category_for" not in df.columns:
        return pd.DataFrame()

    df_work = df[["id", "year", "category_for"]].copy()
    df_work = df_work[df_work["category_for"].apply(lambda x: isinstance(x, list))]
    if df_work.empty:
        return pd.DataFrame()

    df_work = df_work.explode("category_for").dropna(subset=["category_for"])

    def _extract_name(item):
        if isinstance(item, dict):
            return item.get("name") or item.get("id") or ""
        return item if isinstance(item, str) else ""

    df_work["for_name"] = df_work["category_for"].apply(_extract_name)
    df_work = df_work[df_work["for_name"] != ""]
    df_work["for_division"] = df_work["for_name"].str.extract(r"^(\d{4})", expand=False)
    df_work = df_work[df_work["for_division"].isin(FOR_TIERS)]

    return (
        df_work.rename(columns={"id": "pub_id"})
        [["pub_id", "year", "for_name", "for_division"]]
        .reset_index(drop=True)
    )


def compute_momentum(
    df_exploded: pd.DataFrame,
    current_start: int,
    prior_start: int,
    prior_end: int,
) -> pd.DataFrame:
    """
    Compare publication counts in the current vs prior window.

    Returns DataFrame sorted by momentum_pct (descending) with columns:
    for_division, display_name, tier, current_count, prior_count, momentum_pct.
    """
    if df_exploded.empty or "year" not in df_exploded.columns:
        return pd.DataFrame()

    df = df_exploded.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    current = (
        df[df["year"] >= current_start]
        .groupby("for_division")["pub_id"]
        .nunique()
        .rename("current_count")
    )
    prior = (
        df[(df["year"] >= prior_start) & (df["year"] <= prior_end)]
        .groupby("for_division")["pub_id"]
        .nunique()
        .rename("prior_count")
    )

    result = pd.DataFrame({"current_count": current, "prior_count": prior}).fillna(0)
    result = result.astype(int)

    def _momentum(r):
        if r["prior_count"] > 0:
            return (r["current_count"] - r["prior_count"]) / r["prior_count"] * 100
        return 100.0 if r["current_count"] > 0 else 0.0

    result["momentum_pct"] = result.apply(_momentum, axis=1)
    result["display_name"] = result.index.map(lambda d: FOR_TIERS.get(d, {}).get("name", d))
    result["tier"]         = result.index.map(lambda d: FOR_TIERS.get(d, {}).get("tier", "Unknown"))
    result = result.reset_index()

    return result.sort_values("momentum_pct", ascending=False).reset_index(drop=True)


def momentum_tier(pct: float) -> str:
    if pct > 30:
        return "high"
    if pct >= 10:
        return "medium"
    if pct >= 0:
        return "low"
    return "decline"
