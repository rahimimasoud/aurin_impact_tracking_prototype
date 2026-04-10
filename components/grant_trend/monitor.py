"""
Grant Trend Monitor — wires all sections together.

Surfaces emerging and trending grant activity within the urban research domain,
mapped to AURIN's Field of Research (FOR) classification.

Sections:
  1. Trending FOR fields       — momentum cards (current vs prior window)
  2. Most active categories    — grant volume ranking (last 3 years)
  3. Top funders per field     — leading funders for top-10 trending fields
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
from .funder_breakdown import render_funder_breakdown
from .signal_to_action import render_signal_to_action


class GrantTrendMonitorComponent(BaseComponent):

    def __init__(self, grants_data: Optional[pd.DataFrame]):
        super().__init__()
        self.grants_data = grants_data
        now = datetime.datetime.now().year
        self._current_end   = now - 1
        self._current_start = now - 4
        self._prior_end     = now - 5
        self._prior_start   = now - 8

    def render(self) -> None:
        st.markdown(
            '<div class="section-header">💰 Grant Trend Monitor</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Surfaces emerging and trending grant activity within the urban research domain, "
            "mapped to AURIN's Field of Research (FOR) classification. "
            f"Current window: {self._current_start}–{self._current_end} "
            f"| Prior window: {self._prior_start}–{self._prior_end}."
        )

        data_empty = self.grants_data is None or (
            isinstance(self.grants_data, pd.DataFrame)
            and self.grants_data.empty
        )
        if data_empty:
            st.warning(
                "No data available for grant trend monitoring. "
                "Please check your API connection."
            )
            return

        df_exploded = explode_with_year(self.grants_data)
        if df_exploded.empty:
            st.warning("No FOR classification data found in the grants dataset.")
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

        core_df = momentum_df.head(10).reset_index(drop=True)
        top10_divisions = core_df["for_division"].tolist() if not core_df.empty else []

        # ── Section 3 ──────────────────────────────────────────────────
        if top10_divisions:
            render_funder_breakdown(
                df_exploded, top10_divisions, self._current_start
            )
        else:
            st.info("No FOR fields found in the dataset — funder analysis skipped.")

        st.divider()

        # ── Section 4 ──────────────────────────────────────────────────
        if not core_df.empty:
            render_signal_to_action(core_df)
        else:
            st.info("No FOR fields found in the dataset — signal-to-action skipped.")
