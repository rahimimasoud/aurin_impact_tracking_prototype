"""
Research Trends Analysis component for identifying under-served spatial/urban research areas.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px


class ResearchTrendsAnalysisComponent(BaseComponent):
    """Component for identifying research trends in Australian spatial and urban research."""

    def __init__(self, grants_data: Optional[pd.DataFrame], publications_data: Optional[pd.DataFrame]):
        """
        Initialize the component.

        Args:
            grants_data: DataFrame of Australian urban/spatial grants
            publications_data: DataFrame of AU spatial publications not citing AURIN
        """
        super().__init__()
        self.grants_data = grants_data
        self.publications_data = publications_data

    def _explode_for_classifications(self, df: pd.DataFrame, col: str = "category_for") -> pd.DataFrame:
        """
        Explode the category_for column into one row per FOR category.

        Args:
            df: DataFrame containing a category_for column
            col: Name of the column holding FOR classification data

        Returns:
            DataFrame with a `for_name` column, one row per category per original row
        """
        if col not in df.columns:
            return pd.DataFrame()

        rows = []
        for idx, row in df.iterrows():
            val = row[col]
            if val is None:
                continue
            if not isinstance(val, list):
                continue
            for item in val:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("id", "")
                elif isinstance(item, str):
                    name = item
                else:
                    continue
                if name:
                    new_row = row.to_dict()
                    new_row["for_name"] = name
                    rows.append(new_row)

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)

    def _build_grants_chart(self, df_exploded: pd.DataFrame):
        """
        Build a horizontal bar chart of grant counts by FOR category.

        Args:
            df_exploded: DataFrame with a `for_name` column (one row per category)

        Returns:
            Plotly figure
        """
        counts = df_exploded["for_name"].value_counts().reset_index()
        counts.columns = ["FOR Category", "Grant Count"]
        counts = counts.sort_values("Grant Count", ascending=True)

        fig = px.bar(
            counts,
            x="Grant Count",
            y="FOR Category",
            orientation="h",
            title="AU Grants by Field of Research Category",
            labels={"Grant Count": "Number of Grants", "FOR Category": ""},
            color="Grant Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            height=max(400, len(counts) * 28),
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

    def _build_publications_chart(self, df_exploded: pd.DataFrame):
        """
        Build a horizontal bar chart of publication counts by FOR category.

        Args:
            df_exploded: DataFrame with a `for_name` column (one row per category)

        Returns:
            Plotly figure
        """
        counts = df_exploded["for_name"].value_counts().reset_index()
        counts.columns = ["FOR Category", "Publication Count"]
        counts = counts.sort_values("Publication Count", ascending=True)

        fig = px.bar(
            counts,
            x="Publication Count",
            y="FOR Category",
            orientation="h",
            title="Publications by Field of Research Category (Last 5 Years)",
            labels={"Publication Count": "Number of Publications", "FOR Category": ""},
            color="Publication Count",
            color_continuous_scale="Oranges",
        )
        fig.update_layout(
            height=max(400, len(counts) * 28),
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

    def _build_publications_trend_chart(self, df_exploded: pd.DataFrame, top_categories: list):
        """
        Build a line chart showing publication counts per year for top FOR categories.

        Args:
            df_exploded: DataFrame with `for_name` and `year` columns
            top_categories: List of FOR category names to include

        Returns:
            Plotly figure
        """
        df_top = df_exploded[df_exploded["for_name"].isin(top_categories)].copy()
        df_top["year"] = pd.to_numeric(df_top["year"], errors="coerce")
        df_top = df_top.dropna(subset=["year"])
        df_top["year"] = df_top["year"].astype(int)

        trend = df_top.groupby(["year", "for_name"]).size().reset_index(name="Publication Count")
        trend = trend.sort_values("year")

        fig = px.line(
            trend,
            x="year",
            y="Publication Count",
            color="for_name",
            markers=True,
            title="Publication Trends by FOR Category (Last 5 Years — Top 10)",
            labels={"year": "Year", "Publication Count": "Number of Publications", "for_name": "FOR Category"},
        )
        fig.update_layout(
            height=420,
            xaxis=dict(dtick=1),
            legend=dict(title="FOR Category", orientation="v"),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

    def _format_publications_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a display DataFrame for the publications table.

        Args:
            df: Raw publications DataFrame

        Returns:
            Display DataFrame with columns: Title, Year, Times Cited, FOR Categories, Link
        """
        display_rows = []
        for _, row in df.iterrows():
            for_names = ""
            val = row.get("category_for")
            if isinstance(val, list):
                names = []
                for item in val:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("id", "")
                    elif isinstance(item, str):
                        name = item
                    else:
                        continue
                    if name:
                        names.append(name)
                for_names = ", ".join(names)

            display_rows.append({
                "Title": row.get("title", ""),
                "Year": row.get("year", ""),
                "Times Cited": row.get("times_cited", ""),
                "FOR Categories": for_names,
                "Link": row.get("linkout", ""),
            })

        return pd.DataFrame(display_rows)

    def render(self) -> None:
        """Render the research trends analysis component."""
        st.markdown(
            '<div class="section-header">🔍 Research Trends Analysis</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Identifies under-served spatial and urban research areas in Australia "
            "by analysing grant coverage and publications that use spatial data without citing AURIN."
        )

        # ── Section A ────────────────────────────────────────────────────────
        st.subheader("Emerging research areas (AU grants by Field of Research)")

        grants_empty = self.grants_data is None or (isinstance(self.grants_data, pd.DataFrame) and self.grants_data.empty)
        if grants_empty:
            st.warning("No grants data available for the selected date range.")
        else:
            df_grants_exploded = self._explode_for_classifications(self.grants_data)
            if df_grants_exploded.empty:
                st.warning("No FOR classification data found in grants.")
            else:
                st.plotly_chart(self._build_grants_chart(df_grants_exploded), use_container_width=True)

                # Top 15 summary table
                counts = df_grants_exploded["for_name"].value_counts().reset_index()
                counts.columns = ["FOR Category", "Grant Count"]
                counts = counts.head(15)

                # Add total funding per category
                if "funding_usd" in df_grants_exploded.columns:
                    funding_by_cat = (
                        df_grants_exploded.groupby("for_name")["funding_usd"]
                        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
                        .reset_index()
                    )
                    funding_by_cat.columns = ["FOR Category", "Total Funding (USD)"]
                    counts = counts.merge(funding_by_cat, on="FOR Category", how="left")
                    counts["Total Funding (USD)"] = counts["Total Funding (USD)"].fillna(0)

                st.dataframe(counts, use_container_width=True, hide_index=True)

        # ── Section B ────────────────────────────────────────────────────────
        st.subheader("FOR categories with low grant coverage")

        if grants_empty:
            st.warning("No grants data available to assess trends.")
        else:
            df_grants_exploded = self._explode_for_classifications(self.grants_data)
            if df_grants_exploded.empty:
                st.warning("No FOR classification data found in grants.")
            else:
                counts = df_grants_exploded["for_name"].value_counts()
                low_coverage = counts[counts < 3].index.tolist()

                if low_coverage:
                    names_list = "\n".join(f"- {n}" for n in sorted(low_coverage))
                    st.info(
                        "These categories have fewer than 3 associated AU grants and may represent "
                        f"data supply trends.\n\n{names_list}"
                    )
                else:
                    st.success(
                        "All tracked FOR categories have sufficient grant coverage in the selected date range."
                    )

        # ── Section C ────────────────────────────────────────────────────────
        st.subheader("Emerging research areas (AU recent publications by Field of Research)")

        pubs_empty = self.publications_data is None or (isinstance(self.publications_data, pd.DataFrame) and self.publications_data.empty)
        if pubs_empty:
            st.warning("No publications data available for the selected date range.")
        else:
            # Filter to last 5 years
            current_year = pd.Timestamp.now().year
            cutoff_year = current_year - 5
            df_pubs_5y = self.publications_data.copy()
            if "year" in df_pubs_5y.columns:
                df_pubs_5y["year"] = pd.to_numeric(df_pubs_5y["year"], errors="coerce")
                df_pubs_5y = df_pubs_5y[df_pubs_5y["year"] >= cutoff_year]

            if df_pubs_5y.empty:
                st.warning(f"No publications data found in the last 5 years ({cutoff_year}–{current_year}).")
            else:
                df_pubs_exploded = self._explode_for_classifications(df_pubs_5y)
                if df_pubs_exploded.empty:
                    st.warning("No FOR classification data found in publications.")
                else:
                    st.plotly_chart(self._build_publications_chart(df_pubs_exploded), use_container_width=True)

                    # Summary table: paper count + total citations + avg citations per category
                    counts = df_pubs_exploded["for_name"].value_counts().reset_index()
                    counts.columns = ["FOR Category", "Paper Count"]

                    if "times_cited" in df_pubs_exploded.columns:
                        citation_stats = (
                            df_pubs_exploded.groupby("for_name")["times_cited"]
                            .apply(lambda s: pd.to_numeric(s, errors="coerce"))
                            .groupby(level=0)
                            .agg(total_citations="sum", avg_citations="mean")
                            .reset_index()
                            .rename(columns={"for_name": "FOR Category"})
                        )
                        citation_stats["Total Citations"] = citation_stats["total_citations"].fillna(0).astype(int)
                        citation_stats["Avg Citations"] = citation_stats["avg_citations"].fillna(0).round(1)
                        counts = counts.merge(
                            citation_stats[["FOR Category", "Total Citations", "Avg Citations"]],
                            on="FOR Category",
                            how="left",
                        )

                    counts = counts.sort_values("Paper Count", ascending=False).head(15)
                    st.dataframe(counts, use_container_width=True, hide_index=True)

                    # Highlight the top 3 most active categories
                    top3 = counts.head(3)["FOR Category"].tolist()
                    if top3:
                        top3_str = ", ".join(f"**{n}**" for n in top3)
                        st.info(
                            f"Most active urban research areas by publication volume: {top3_str}. "
                            "These categories may represent growing researcher demand for spatial data infrastructure."
                        )

                    # Trend chart: year-by-year for top 10 categories
                    if "year" in df_pubs_exploded.columns:
                        st.subheader("Publication trends over time by FOR Category")
                        top10_cats = counts.head(10)["FOR Category"].tolist()
                        st.plotly_chart(
                            self._build_publications_trend_chart(df_pubs_exploded, top10_cats),
                            use_container_width=True,
                        )
