"""
Shared data helpers for the Grant Trend Monitor sections.
"""
from typing import Optional
import re

import pandas as pd

from ._constants import FOR_TIERS


def for_division(name: str) -> Optional[str]:
    """Return the first 4 digits of a FOR code string (e.g. '330401 ...' → '3304')."""
    m = re.match(r"^(\d{4})", str(name))
    return m.group(1) if m else None


def extract_year(start_date) -> Optional[int]:
    """Extract year from a start_date value (string 'YYYY-MM-DD' or int)."""
    if pd.isna(start_date):
        return None
    s = str(start_date).strip()
    m = re.match(r"^(\d{4})", s)
    return int(m.group(1)) if m else None


def explode_with_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode category_for to one row per FOR item (filtered to FOR_TIERS),
    returning columns: grant_id, year, for_name, for_division, funding_org_name, funding_usd.
    Year is derived from the start_date field.
    """
    if "category_for" not in df.columns:
        return pd.DataFrame()

    rows = []
    for _, row in df.iterrows():
        val = row.get("category_for")
        if not isinstance(val, list):
            continue
        year = extract_year(row.get("start_date"))
        grant_id = row.get("id", "")
        funder = row.get("funding_org_name", "")
        funding_usd = row.get("funding_usd", 0)
        for item in val:
            if isinstance(item, dict):
                name = item.get("name") or item.get("id", "")
            elif isinstance(item, str):
                name = item
            else:
                continue
            if not name:
                continue
            division = for_division(name)
            if division and division in FOR_TIERS:
                rows.append({
                    "grant_id":        grant_id,
                    "year":            year,
                    "for_name":        name,
                    "for_division":    division,
                    "funding_org_name": funder,
                    "funding_usd":     funding_usd,
                })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def compute_momentum(
    df_exploded: pd.DataFrame,
    current_start: int,
    prior_start: int,
    prior_end: int,
) -> pd.DataFrame:
    """
    Compare grant counts in the current vs prior window.

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
        .groupby("for_division")["grant_id"]
        .nunique()
        .rename("current_count")
    )
    prior = (
        df[(df["year"] >= prior_start) & (df["year"] <= prior_end)]
        .groupby("for_division")["grant_id"]
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
