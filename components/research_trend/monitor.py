"""
Research Trend Monitor — wires all sections together.

Surfaces emerging and trending research topics within the urban research domain,
mapped to AURIN's Field of Research (FOR) classification.

Sections:
  1. Trending FOR fields       — momentum cards (current vs prior window)
  2. Most active categories    — publication volume ranking (last 3 years)
  3. Keyword tag clouds        — top concepts per top-10 trending field
  4. Signal-to-action          — rule-based recommended actions
"""
import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from components.base_component import BaseComponent
from ._helpers import explode_with_year, compute_momentum
from .trending_cards import render_trending_cards
from .top_categories import render_top_categories_by_volume
from .keyword_trends import render_keyword_trends
from .signal_to_action import render_signal_to_action
from data_loader import _load_research_trend_monitor, _load_research_trend_concepts


@st.cache_data
def _cached_explode() -> pd.DataFrame:
    """Load and explode the research trend DataFrame, cached across Streamlit reruns."""
    return explode_with_year(_load_research_trend_monitor())


class ResearchTrendMonitorComponent(BaseComponent):

    def __init__(self, publications_data: Optional[pd.DataFrame]):
        super().__init__()
        self.publications_data = publications_data
        now = datetime.datetime.now().year
        # Current window : last 3 years  (e.g. 2022–2025)
        # Prior window   : 3 years before (e.g. 2019–2021)
        self._current_end   = now - 1
        self._current_start = now - 4
        self._prior_end     = now - 5
        self._prior_start   = now - 8

    def render(self) -> None:
        st.markdown(
            '<div class="section-header">📈 Research Trend Monitor</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Surfaces emerging and trending research topics within the urban research domain, "
            "mapped to AURIN's Field of Research (FOR) classification. "
            f"Current window: {self._current_start}–{self._current_end} "
            f"| Prior window: {self._prior_start}–{self._prior_end}."
        )

        data_empty = self.publications_data is None or (
            isinstance(self.publications_data, pd.DataFrame)
            and self.publications_data.empty
        )
        if data_empty:
            st.warning(
                "No data available for trend monitoring. "
                "Please check your API connection."
            )
            return

        df_exploded = _cached_explode()
        if df_exploded.empty:
            st.warning("No FOR classification data found in the publications dataset.")
            return

        momentum_df = compute_momentum(
            df_exploded,
            self._current_start,
            self._prior_start,
            self._prior_end,
        )
        if momentum_df.empty:
            st.warning("Insufficient data to compute momentum scores.")
            return

        # ── Section 1 ──────────────────────────────────────────────────
        render_trending_cards(
            df_exploded, momentum_df,
            self._current_start, self._current_end,
            self._prior_start, self._prior_end,
        )

        st.divider()

        # ── Section 2 ──────────────────────────────────────────────────
        render_top_categories_by_volume(
            df_exploded, self._current_start, self._current_end
        )

        st.divider()

        core_df = momentum_df.head(20).reset_index(drop=True)
        top20_divisions = core_df["for_division"].tolist() if not core_df.empty else []

        # ── Section 3 ──────────────────────────────────────────────────
        if top20_divisions:
            concepts_df = _load_research_trend_concepts()
            render_keyword_trends(
                df_exploded, concepts_df,
                top20_divisions, self._current_start,
            )
        else:
            st.info("No FOR fields found in the dataset — keyword analysis skipped.")

        st.divider()

        # ── Section 4 ──────────────────────────────────────────────────
        if not core_df.empty:
            render_signal_to_action(core_df)
        else:
            st.info("No FOR fields found in the dataset — signal-to-action skipped.")
