"""
Media Monitor component: displays AURIN media mentions fetched from Google News.
"""
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.express as px

from components.base_component import BaseComponent
from components.tab_ai_tools import (
    render_tab_ai_tools,
    build_media_monitor_context,
    _SUMMARY_PROMPT_MEDIA_MONITOR,
)
from data import AurinDatabase, MediaCapture
from data_loader import _load_media_mentions


class MediaMonitorComponent(BaseComponent):
    """Renders the Media Monitor tab: fetch, timeline, source breakdown, and mentions table."""

    def __init__(self, openrouter_api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.openrouter_api_key = openrouter_api_key

    def render(self) -> None:
        st.markdown("## 📰 Media Monitor")
        st.caption("AURIN mentions sourced from Google News RSS.")

        # self._render_fetch_button()

        df = _load_media_mentions()
        self.set_data(df)

        if not self.validate_data():
            st.info(
                "No media mentions cached yet. "
                "Click **Fetch Latest Mentions** above to pull results from Google News."
            )
            return

        render_tab_ai_tools(
            "media_monitor", "Media Monitor",
            build_media_monitor_context(df),
            self.openrouter_api_key,
            _SUMMARY_PROMPT_MEDIA_MONITOR,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising media coverage...",
        )

        self._render_summary(df)
        self._render_timeline(df)

        col_left, col_right = st.columns([2, 1])
        with col_left:
            self._render_table(df)
        with col_right:
            self._render_source_breakdown(df)

    def _render_fetch_button(self) -> None:
        if st.button("🔄 Fetch Latest Mentions", type="primary"):
            _progress = st.progress(0.0, text="Fetching media mentions…")
            try:
                db = AurinDatabase()
                capture = MediaCapture()
                capture.capture_all(
                    db,
                    progress_callback=lambda frac, label: _progress.progress(frac, text=label),
                )
                st.cache_data.clear()
                st.success("Media mentions updated.")
            except Exception as e:
                st.error(f"Fetch failed: {e}")
            finally:
                _progress.empty()
            st.rerun()

    def _render_summary(self, df: pd.DataFrame) -> None:
        total = len(df)
        unique_sources = df["source"].nunique()
        has_dates = "published_at" in df.columns and df["published_at"].notna().any()
        date_range = ""
        if has_dates:
            earliest = df["published_at"].min()
            latest = df["published_at"].max()
            date_range = f"{earliest.strftime('%d %b %Y')} – {latest.strftime('%d %b %Y')}"

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Mentions", total)
        c2.metric("Unique Sources", unique_sources)
        c3.metric("Date Range", date_range or "—")

    def _render_timeline(self, df: pd.DataFrame) -> None:
        if "published_at" not in df.columns or df["published_at"].isna().all():
            return

        df_dated = df.dropna(subset=["published_at"]).copy()
        df_dated["quarter"] = df_dated["published_at"].dt.to_period("Q").dt.start_time
        monthly = df_dated.groupby("quarter").size().reset_index(name="mentions")

        fig = px.bar(
            monthly,
            x="quarter",
            y="mentions",
            labels={"quarter": "Quarter", "mentions": "Mentions"},
            title="Mentions Over Time (quarterly)",
            color_discrete_sequence=["#0068c9"],
        )
        fig.update_layout(margin=dict(t=40, b=20), height=280)
        st.plotly_chart(fig, use_container_width=True)

    def _render_table(self, df: pd.DataFrame) -> None:
        st.markdown("### Mentions")

        # Term filter
        terms = sorted(df["search_term"].dropna().unique().tolist())
        selected = st.multiselect("Filter by search term", terms, default=terms, key="mm_term_filter")
        filtered = df[df["search_term"].isin(selected)] if selected else df

        display = filtered[["published_at", "title", "source", "url", "snippet"]].copy()
        display = display.sort_values("published_at", ascending=False).reset_index(drop=True)

        st.dataframe(
            display,
            use_container_width=True,
            height=450,
            column_config={
                "published_at": st.column_config.DateColumn("Date", width="small", format="DD MMM YYYY"),
                "title": st.column_config.TextColumn("Title", width="large"),
                "source": st.column_config.TextColumn("Source", width="medium"),
                "url": st.column_config.LinkColumn("Link", width="small", display_text="Open"),
                "snippet": st.column_config.TextColumn("Snippet", width="large"),
            },
            hide_index=True,
        )

    def _render_source_breakdown(self, df: pd.DataFrame) -> None:
        st.markdown("### Top Sources")
        top_sources = (
            df["source"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .head(15)
            .reset_index()
        )
        top_sources.columns = ["source", "count"]

        if top_sources.empty:
            st.caption("No source data available.")
            return

        fig = px.bar(
            top_sources,
            x="count",
            y="source",
            orientation="h",
            labels={"count": "Mentions", "source": ""},
            color_discrete_sequence=["#0068c9"],
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(t=10, b=20),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
