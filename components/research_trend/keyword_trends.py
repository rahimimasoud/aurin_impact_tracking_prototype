"""
Section 3 — Emerging Keywords in Top Trending Fields.

Renders a tag-cloud of the most frequent research concepts
for each of the top trending FOR fields.
"""
from typing import Dict, List

import pandas as pd
import streamlit as st

from ._constants import FOR_TIERS, TIER_BADGE, KEYWORD_STOPWORDS


def render_keyword_trends(
    df_exploded: pd.DataFrame,
    publications_data: pd.DataFrame,
    top10_divisions: List[str],
    current_start: int,
) -> None:
    st.subheader("Emerging Keywords in Top Trending Fields")
    st.caption(
        "Most frequent research concepts within the current window "
        "for the top 10 trending FOR fields."
    )

    if publications_data is None or publications_data.empty:
        st.warning("No data available for keyword analysis.")
        return

    if "concepts" not in publications_data.columns:
        st.info("Concept/keyword data is not available in this dataset.")
        return

    df_pubs = publications_data.copy()
    df_pubs["year"] = pd.to_numeric(
        df_pubs.get("year", pd.Series(dtype=float)), errors="coerce"
    )
    df_pubs = df_pubs[df_pubs["year"] >= current_start]

    for division in top10_divisions:
        tier_info  = FOR_TIERS.get(division, {})
        field_name = tier_info.get("name", division)
        tier       = tier_info.get("tier", "Core")
        badge      = TIER_BADGE.get(tier, TIER_BADGE["Core"])

        matching_ids = set(
            df_exploded[df_exploded["for_division"] == division]["pub_id"].unique()
        )
        if "id" in df_pubs.columns:
            df_field = df_pubs[df_pubs["id"].isin(matching_ids)]
        else:
            df_field = df_pubs

        concept_counts: Dict[str, int] = {}
        for _, row in df_field.iterrows():
            concepts = row.get("concepts")
            if not isinstance(concepts, list):
                continue
            for c in concepts:
                if isinstance(c, dict):
                    concept = c.get("concept") or c.get("name") or c.get("id", "")
                elif isinstance(c, str):
                    concept = c
                else:
                    continue
                concept = concept.strip().lower()
                if concept and len(concept) > 2 and concept not in KEYWORD_STOPWORDS:
                    concept_counts[concept] = concept_counts.get(concept, 0) + 1

        if not concept_counts:
            st.info(f"No concept data found for **{field_name}**.")
            continue

        top_concepts = sorted(concept_counts.items(), key=lambda x: -x[1])[:20]
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
