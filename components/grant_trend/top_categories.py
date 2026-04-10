"""
Section 2 — Most Active Grant Categories (Last 3 Years).

Horizontal bar chart ranking FOR fields by grant volume
in the current three-year window.
"""
import pandas as pd
import streamlit as st

from ._constants import FOR_TIERS, TIER_BADGE


def render_top_categories_by_volume(
    df_exploded: pd.DataFrame,
    current_start: int,
    current_end: int,
) -> None:
    st.subheader("Most Active Grant Categories (Last 3 Years)")
    st.caption(
        f"FOR fields ranked by total grants awarded in the recent three-year period "
        f"({current_start}–{current_end})."
    )

    df = df_exploded.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df[df["year"] >= current_start]

    if df.empty:
        st.warning("No data available for the recent three-year period.")
        return

    counts = (
        df.groupby("for_division")["grant_id"]
        .nunique()
        .rename("count")
        .reset_index()
    )
    counts["display_name"] = counts["for_division"].map(
        lambda d: FOR_TIERS.get(d, {}).get("name", d)
    )
    counts["tier"] = counts["for_division"].map(
        lambda d: FOR_TIERS.get(d, {}).get("tier", "Unknown")
    )
    counts = counts.sort_values("count", ascending=False).reset_index(drop=True)

    max_count = counts["count"].max()

    for _, row in counts.iterrows():
        tier      = row["tier"]
        badge     = TIER_BADGE.get(tier, TIER_BADGE["Contextual"])
        bar_color = badge["fg"]
        bar_pct   = int(row["count"] / max_count * 100) if max_count > 0 else 0

        st.markdown(
            f"""
            <div style="margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between;
                          align-items:center; margin-bottom:3px;">
                <span style="font-size:13px; font-weight:600; color:inherit;">
                  {row["display_name"]}
                </span>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="background:{bar_color}33; color:{bar_color};
                               font-size:10px; padding:1px 7px; border-radius:10px;
                               font-weight:500;">{tier}</span>
                  <span style="font-size:13px; font-weight:700; color:inherit;
                               min-width:40px; text-align:right;">{row["count"]:,}</span>
                </div>
              </div>
              <div style="background:rgba(128,128,128,0.2); border-radius:4px; height:8px;">
                <div style="width:{bar_pct}%; background:{bar_color};
                            border-radius:4px; height:8px;"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
