"""
Funding Signal Monitor — strategic view of grant dollar flows by research field.

Answers:
  - Which fields have the strongest funding momentum and research relevance?
  - Where is AURIN underexposed relative to fast-growing funding pools?
  - Which funders should we target first in high-growth fields?
  - Which declining fields still attract large absolute dollars?
"""
import datetime
import re
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI

from components.base_component import BaseComponent
from components.grant_trend._helpers import explode_with_year, compute_momentum
from components.tab_ai_tools import render_qa_only


_SIGNAL_PROMPT = """\
You are a research funding strategist for AURIN (Australian Urban Research \
Infrastructure Network). Based on the funding signal data below, provide \
exactly 4 strategic bullets addressing:

1. **Momentum fields** — which fields have the strongest funding growth AND \
largest absolute dollars?
2. **Underexposure gaps** — where is AURIN underexposed relative to fast-growing \
funding pools?
3. **Funder targets** — which funders should AURIN approach first in high-growth \
fields?
4. **Declining-but-large** — which declining fields still attract enough absolute \
dollars to warrant continued engagement?

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for the label — do not use italic (*text*) anywhere.

DATA:
{context}"""


def _fmt_usd(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:.0f}"


class FundingSignalMonitorComponent(BaseComponent):
    """Four-card funding signal panel with optional LLM narrative."""

    def __init__(
        self,
        grant_trend_data: Optional[pd.DataFrame] = None,
        publications_data: Optional[pd.DataFrame] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        super().__init__()
        self.grant_trend_data = grant_trend_data
        self.publications_data = publications_data
        self.openrouter_api_key = openrouter_api_key
        now = datetime.datetime.now().year
        self._current_start = now - 4
        self._prior_start   = now - 8
        self._prior_end     = now - 5

    # ── public ─────────────────────────────────────────────────────────

    def render(self) -> None:
        st.markdown(
            '<div class="section-header">💵 Funding Signal Monitor</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Strategic view of grant dollar flows by research field — "
            "identifies momentum, concentration risk, and targeting opportunities."
        )

        if self.grant_trend_data is None or self.grant_trend_data.empty:
            st.warning("No grant trend data available.")
            return

        df_exp = explode_with_year(self.grant_trend_data)
        if df_exp.empty:
            st.warning("No FOR-classified grant data found.")
            return

        df_exp["funding_usd"] = pd.to_numeric(
            df_exp["funding_usd"], errors="coerce"
        ).fillna(0)

        col_summary, col_qa = st.columns(2)
        with col_summary:
            self._llm_signals(df_exp)
        with col_qa:
            render_qa_only(
                "funding_signal_monitor",
                "Funding Signal Monitor",
                self._build_context(df_exp, self.publications_data),
                self.openrouter_api_key,
                divider=False,
            )
        st.divider()


        col1, col2 = st.columns(2)
        with col1:
            self._card_total_by_field(df_exp)
        with col2:
            self._card_fastest_growing(df_exp)

        col3, col4 = st.columns(2)
        with col3:
            self._card_avg_grant_size(df_exp)
        with col4:
            self._card_funder_concentration(df_exp)

        
  

    # ── private cards ───────────────────────────────────────────────────

    def _card_total_by_field(self, df: pd.DataFrame) -> None:
        st.subheader("Total Dollars by Field")
        data = (
            df.groupby("for_name")["funding_usd"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .sort_values()
            .reset_index()
        )
        data.columns = ["Field", "USD"]
        fig = px.bar(
            data, x="USD", y="Field", orientation="h",
            color="USD", color_continuous_scale="Blues",
        )
        fig.update_layout(
            height=420, margin=dict(l=0, r=10, t=10, b=30),
            coloraxis_showscale=False, yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

    def _card_fastest_growing(self, df: pd.DataFrame) -> None:
        st.subheader("Fastest-Growing Fields by Funding Dollars")
        df_yr = df.copy()
        df_yr["year"] = pd.to_numeric(df_yr["year"], errors="coerce")
        df_yr = df_yr.dropna(subset=["year"])
        df_yr["year"] = df_yr["year"].astype(int)

        current = (
            df_yr[df_yr["year"] >= self._current_start]
            .groupby("for_name")["funding_usd"].sum()
        )
        prior = (
            df_yr[
                (df_yr["year"] >= self._prior_start)
                & (df_yr["year"] <= self._prior_end)
            ]
            .groupby("for_name")["funding_usd"].sum()
        )
        g = pd.concat([current.rename("c"), prior.rename("p")], axis=1).fillna(0)
        g["pct"] = g.apply(
            lambda r: (r["c"] - r["p"]) / r["p"] * 100
            if r["p"] > 0 else (100.0 if r["c"] > 0 else 0.0),
            axis=1,
        )
        data = (
            g[g["c"] > 0]
            .sort_values("pct", ascending=False)
            .head(10)
            .sort_values("pct")
            .reset_index()
        )
        data.columns = ["Field", "Current", "Prior", "Growth (%)"]
        fig = px.bar(
            data, x="Growth (%)", y="Field", orientation="h",
            color="Growth (%)", color_continuous_scale="RdYlGn",
        )
        fig.update_layout(
            height=420, margin=dict(l=0, r=10, t=10, b=30),
            coloraxis_showscale=False, yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

    def _card_avg_grant_size(self, df: pd.DataFrame) -> None:
        st.subheader("Largest Average Grant Size")
        data = (
            df[df["funding_usd"] > 0]
            .groupby("for_name")
            .agg(avg=("funding_usd", "mean"), n=("grant_id", "nunique"))
            .sort_values("avg", ascending=False)
            .head(10)
            .sort_values("avg")
            .reset_index()
        )
        data.columns = ["Field", "Avg Grant (USD)", "Grants"]
        fig = px.bar(
            data, x="Avg Grant (USD)", y="Field", orientation="h",
            color="Avg Grant (USD)", color_continuous_scale="Purples",
        )
        fig.update_layout(
            height=380, margin=dict(l=0, r=10, t=10, b=30),
            coloraxis_showscale=False, yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

    def _card_funder_concentration(self, df: pd.DataFrame) -> None:
        st.subheader("Top Funders in Trending Fields")
        momentum_df = compute_momentum(
            df, self._current_start, self._prior_start, self._prior_end
        )
        if momentum_df.empty:
            st.info("Not enough data to identify trending fields.")
            return

        top_divisions = momentum_df.head(8)["for_division"].tolist()

        df_yr = df.copy()
        df_yr["year"] = pd.to_numeric(df_yr["year"], errors="coerce")
        df_yr = df_yr.dropna(subset=["year"])
        df_yr["year"] = df_yr["year"].astype(int)
        df_trending = df_yr[
            df_yr["for_division"].isin(top_divisions)
            & (df_yr["year"] >= self._current_start)
        ]

        if df_trending.empty:
            st.info("No funder data available for trending fields.")
            return

        data = (
            df_trending.groupby("funder_org_name")
            .agg(total=("funding_usd", "sum"), n=("grant_id", "nunique"))
            .sort_values("total", ascending=False)
            .head(12)
            .reset_index()
        )
        data = data[
            data["funder_org_name"].notna()
            & (data["funder_org_name"].str.strip() != "")
        ]
        data = data.sort_values("total", ascending=True)
        data.columns = ["Funder", "Total (USD)", "Grants"]
        fig = px.bar(
            data, x="Total (USD)", y="Funder", orientation="h",
            color="Total (USD)", color_continuous_scale="Oranges",
            hover_data={"Grants": True},
        )
        fig.update_layout(
            height=380, margin=dict(l=0, r=10, t=10, b=30),
            coloraxis_showscale=False, yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── LLM signals ────────────────────────────────────────────────────

    def _llm_signals(self, df_exp: pd.DataFrame) -> None:
        st.subheader("AI Insights: Funding Signals")
        if not self.openrouter_api_key:
            st.info(
                "Enter your OpenRouter API key in Configure to enable AI funding signals."
            )
            return

        if st.button("Generate Funding Signals", type="primary"):
            with st.spinner("Analysing funding patterns..."):
                try:
                    client = OpenAI(
                        api_key=self.openrouter_api_key,
                        base_url="https://openrouter.ai/api/v1",
                    )
                    response = client.chat.completions.create(
                        model="openrouter/auto",
                        messages=[
                            {
                                "role": "user",
                                "content": _SIGNAL_PROMPT.format(
                                    context=self._build_context(
                                        df_exp, self.publications_data
                                    )
                                ),
                            }
                        ],
                        timeout=60,
                    )
                    content = response.choices[0].message.content
                    content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', content)
                    content = re.sub(r'`([^`\n]+)`', r'\1', content)
                    content = content.replace('$', r'\$')
                    st.markdown(content)
                except Exception as e:
                    st.error(f"Signal generation failed: {e}")

    def _pub_counts_by_for(self, publications: Optional[pd.DataFrame]) -> pd.Series:
        """Return publication count per FOR field name from the main publications df."""
        if publications is None or publications.empty or "category_for" not in publications.columns:
            return pd.Series(dtype=int)
        rows = []
        for val in publications["category_for"]:
            if not isinstance(val, list):
                continue
            for item in val:
                name = item.get("name") or item.get("id", "") if isinstance(item, dict) else str(item)
                if name:
                    rows.append(name)
        if not rows:
            return pd.Series(dtype=int)
        return pd.Series(rows).value_counts()

    def _build_context(self, df: pd.DataFrame, publications: Optional[pd.DataFrame] = None) -> str:
        lines: list[str] = []
        now = datetime.datetime.now().year

        top_total = (
            df.groupby("for_name")["funding_usd"].sum()
            .sort_values(ascending=False).head(10)
        )
        lines.append("TOP FIELDS BY TOTAL FUNDING:")
        for name, val in top_total.items():
            lines.append(f"  {name}: {_fmt_usd(val)}")

        df_yr = df.copy()
        df_yr["year"] = pd.to_numeric(df_yr["year"], errors="coerce")
        c = df_yr[df_yr["year"] >= now - 4].groupby("for_name")["funding_usd"].sum()
        p = df_yr[
            (df_yr["year"] >= now - 8) & (df_yr["year"] <= now - 5)
        ].groupby("for_name")["funding_usd"].sum()
        g = pd.concat([c.rename("c"), p.rename("p")], axis=1).fillna(0)
        g["pct"] = g.apply(
            lambda r: (r["c"] - r["p"]) / r["p"] * 100
            if r["p"] > 0 else (100.0 if r["c"] > 0 else 0.0),
            axis=1,
        )
        lines.append("\nFASTEST-GROWING FIELDS (YoY funding):")
        for name, row in g[g["c"] > 0].sort_values("pct", ascending=False).head(8).iterrows():
            sign = "+" if row["pct"] >= 0 else ""
            lines.append(
                f"  {name}: {sign}{row['pct']:.0f}% ({_fmt_usd(row['c'])} current)"
            )

        avg = (
            df[df["funding_usd"] > 0]
            .groupby("for_name")["funding_usd"].mean()
            .sort_values(ascending=False).head(8)
        )
        lines.append("\nLARGEST AVERAGE GRANT SIZE:")
        for name, val in avg.items():
            lines.append(f"  {name}: {_fmt_usd(val)} avg")

        top_funders = (
            df.groupby("funder_org_name")
            .agg(total=("funding_usd", "sum"), n=("grant_id", "nunique"))
            .sort_values("total", ascending=False).head(8)
        )
        lines.append("\nTOP FUNDERS:")
        for funder, row in top_funders.iterrows():
            if funder:
                lines.append(
                    f"  {funder}: {_fmt_usd(row['total'])} across {row['n']} grants"
                )

        pub_counts = self._pub_counts_by_for(publications)
        if not pub_counts.empty:
            lines.append("\nAURIN RESEARCH PAPERS BY FOR FIELD (from published research):")
            for name, count in pub_counts.head(15).items():
                lines.append(f"  {name}: {count} publications")

        return "\n".join(lines)
