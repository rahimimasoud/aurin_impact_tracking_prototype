"""
Section 3 — Top Funders in Trending Fields.

For each of the top 10 trending FOR fields, shows the leading funding
organisations by grant count and total funding in the current window.
"""
from typing import List

import pandas as pd
import streamlit as st

from ._constants import FOR_TIERS, TIER_BADGE


def render_funder_breakdown(
    df_exploded: pd.DataFrame,
    top10_divisions: List[str],
    current_start: int,
) -> None:
    st.subheader("Top Funders in Trending Fields")
    st.caption(
        "Leading funding organisations within the current window "
        "for the top 10 trending FOR fields."
    )

    if df_exploded.empty:
        st.warning("No data available for funder analysis.")
        return

    df = df_exploded.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df[df["year"] >= current_start]

    for division in top10_divisions:
        tier_info  = FOR_TIERS.get(division, {})
        field_name = tier_info.get("name", division)
        tier       = tier_info.get("tier", "Core")
        badge      = TIER_BADGE.get(tier, TIER_BADGE["Core"])

        df_field = df[df["for_division"] == division].copy()
        if df_field.empty:
            st.info(f"No grant data found for **{field_name}** in the current window.")
            continue

        # Aggregate by funder
        funder_stats = (
            df_field.groupby("funding_org_name")
            .agg(
                grant_count=("grant_id", "nunique"),
                total_usd=("funding_usd", "sum"),
            )
            .sort_values("grant_count", ascending=False)
            .head(8)
            .reset_index()
        )

        funder_stats = funder_stats[funder_stats["funding_org_name"].notna()]
        funder_stats = funder_stats[funder_stats["funding_org_name"].str.strip() != ""]

        if funder_stats.empty:
            st.info(f"No funder information available for **{field_name}**.")
            continue

        max_count = funder_stats["grant_count"].max()

        funder_rows_html = []
        for _, fr in funder_stats.iterrows():
            bar_pct = int(fr["grant_count"] / max_count * 100) if max_count > 0 else 0
            usd_str = (
                f"${fr['total_usd']:,.0f}"
                if fr["total_usd"] and fr["total_usd"] > 0
                else "—"
            )
            funder_rows_html.append(
                f'<div style="margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">'
                f'<span style="font-size:12px;color:#374151;max-width:65%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{fr["funding_org_name"]}">{fr["funding_org_name"]}</span>'
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<span style="font-size:11px;color:#6b7280;">{usd_str}</span>'
                f'<span style="font-size:12px;font-weight:700;color:#111827;">{fr["grant_count"]:,}</span>'
                f'</div></div>'
                f'<div style="background:rgba(128,128,128,0.15);border-radius:3px;height:5px;">'
                f'<div style="width:{bar_pct}%;background:{badge["fg"]};border-radius:3px;height:5px;"></div>'
                f'</div></div>'
            )

        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb; border-radius:8px;
                        padding:12px 16px; margin-bottom:12px; background:#fafafa;">
              <div style="margin-bottom:10px;">
                <span style="font-weight:600; font-size:14px; color:#111827;">{field_name}</span>
                <span style="background:{badge['bg']}; color:{badge['fg']}; font-size:11px;
                             padding:2px 8px; border-radius:12px; margin-left:8px;
                             font-weight:500;">FOR {division}</span>
              </div>
              <div style="font-size:11px; color:#9ca3af; margin-bottom:8px;
                          display:flex; justify-content:space-between;">
                <span>Funder</span>
                <span>Total Funding &nbsp;|&nbsp; Grants</span>
              </div>
              {"".join(funder_rows_html)}
            </div>
            """,
            unsafe_allow_html=True,
        )
