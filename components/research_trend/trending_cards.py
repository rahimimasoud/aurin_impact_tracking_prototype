"""
Section 1 — Trending Fields of Research.

Momentum cards comparing the current vs prior publication window,
with a per-field sparkline bar chart.
"""
from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ._constants import FOR_TIERS, TIER_BADGE, MOMENTUM_COLOR
from ._helpers import momentum_tier


def _build_sparkline(df_exploded: pd.DataFrame, division: str) -> go.Figure:
    """Compact year-by-year bar chart for a FOR division (full data period)."""
    df = df_exploded[df_exploded["for_division"] == division].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    if df.empty:
        counts = pd.DataFrame({"year": [], "count": []})
    else:
        min_year = df["year"].min()
        max_year = df["year"].max()
        all_years = list(range(min_year, max_year + 1))
        yearly = df.groupby("year")["pub_id"].nunique().rename("count")
        counts = (
            yearly.reindex(all_years, fill_value=0)
            .reset_index()
            .rename(columns={"index": "year"})
        )

    fig = go.Figure(
        go.Bar(
            x=counts["year"],
            y=counts["count"],
            marker_color="#3b82f6",
            marker_line_width=0,
        )
    )
    fig.update_layout(
        height=65,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def render_trending_cards(
    df_exploded: pd.DataFrame,
    momentum_df: pd.DataFrame,
    current_start: int,
    current_end: int,
    prior_start: int,
    prior_end: int,
) -> None:
    st.subheader("Trending Fields of Research")
    st.caption(
        f"Publication momentum: current window {current_start}–{current_end} "
        f"vs prior window {prior_start}–{prior_end}. "
        "Top 10 FOR fields by momentum score."
    )

    top10 = momentum_df.head(10).reset_index(drop=True)
    if top10.empty:
        st.warning("Insufficient data to compute momentum scores.")
        return

    cols = st.columns(2)
    for i, row in top10.iterrows():
        tier     = row["tier"]
        badge    = TIER_BADGE.get(tier, TIER_BADGE["Contextual"])
        momentum = row["momentum_pct"]
        m_tier   = momentum_tier(momentum)
        m_color  = MOMENTUM_COLOR[m_tier]
        arrow    = "↑" if momentum >= 0 else "↓"
        sign     = "+" if momentum >= 0 else ""

        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb; border-radius:8px;
                            padding:12px 16px 2px 16px; background:#fff;">
                  <div style="display:flex; justify-content:space-between;
                              align-items:flex-start; margin-bottom:4px;">
                    <span style="font-weight:600; font-size:14px; color:#111827;
                                 max-width:70%;">{row["display_name"]}</span>
                    <span style="background:{badge['bg']}; color:{badge['fg']};
                                 font-size:11px; padding:2px 8px; border-radius:12px;
                                 font-weight:500; white-space:nowrap;">{tier}</span>
                  </div>
                  <div style="font-size:24px; font-weight:700; color:{m_color};">
                    {arrow} {sign}{momentum:.0f}%
                  </div>
                  <div style="font-size:11px; color:#6b7280; margin-bottom:2px;">
                    Recent Three-Year Period: {row["current_count"]:,} &nbsp;|&nbsp;
                    Preceding three-year period: {row["prior_count"]:,} publications
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fig = _build_sparkline(df_exploded, row["for_division"])
            st.plotly_chart(
                fig,
                width='stretch',
                config={"displayModeBar": False},
                key=f"sparkline_{row['for_division']}",
            )
