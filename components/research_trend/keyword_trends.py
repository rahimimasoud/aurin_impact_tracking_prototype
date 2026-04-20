"""
Section 3 — Emerging Keywords in Top Trending Fields.

Renders a tag-cloud of the most frequent research concepts
for each of the top trending FOR fields.

Uses the pre-aggregated concept_counts table (for_division, year, concept, count)
built during data capture, avoiding the expensive per-session JSON deserialisation
of ~200k raw concept blobs.
"""
from typing import List

import pandas as pd
import streamlit as st

from ._constants import FOR_TIERS, TIER_BADGE, KEYWORD_STOPWORDS


def render_keyword_trends(
    df_exploded: pd.DataFrame,
    concept_counts_df: pd.DataFrame,
    top20_divisions: List[str],
    current_start: int,
) -> None:
    if concept_counts_df is None or concept_counts_df.empty:
        st.info(
            "Keyword concept data not yet available. "
            "Re-run data capture to generate the concept index."
        )
        return

    # Filter stopwords and trivially short concepts at load time (fast — no JSON)
    df = concept_counts_df[
        (concept_counts_df["concept"].str.len() > 2) &
        (~concept_counts_df["concept"].isin(KEYWORD_STOPWORDS))
    ]

    # Narrow to current window years
    df = df[pd.to_numeric(df["year"], errors="coerce") >= current_start]

    for division in top20_divisions:
        tier_info  = FOR_TIERS.get(division, {})
        field_name = tier_info.get("name", division)
        tier       = tier_info.get("tier", "Core")
        badge      = TIER_BADGE.get(tier, TIER_BADGE["Core"])

        division_df = df[df["for_division"] == division]
        if division_df.empty:
            st.info(f"No concept data found for **{field_name}**.")
            continue

        concept_counts = (
            division_df.groupby("concept")["count"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
        )

        top_concepts = list(concept_counts.items())
        max_freq = top_concepts[0][1]
        min_freq = top_concepts[-1][1]

        tags_html = []
        for concept, freq in top_concepts:
            size = (
                12 + int((freq - min_freq) / (max_freq - min_freq) * 14)
                if max_freq > min_freq
                else 18
            )
            opacity = 0.55 + 0.45 * (freq / max_freq)
            tags_html.append(
                f'<span style="font-size:{size}px; color:#1a56db; opacity:{opacity:.2f}; '
                f'margin:3px 7px; display:inline-block; cursor:default;" '
                f'title="{freq} occurrence{"s" if freq != 1 else ""}">'
                f"{concept}</span>"
            )

        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb; border-radius:8px;
                        padding:12px 16px; margin-bottom:12px; background:#fafafa;">
              <div style="margin-bottom:8px;">
                <span style="font-weight:600; font-size:14px; color:#111827;">{field_name}</span>
                <span style="background:{badge['bg']}; color:{badge['fg']}; font-size:11px;
                             padding:2px 8px; border-radius:12px; margin-left:8px;
                             font-weight:500;">FOR {division}</span>
              </div>
              <div style="line-height:2.2;">{"".join(tags_html)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
