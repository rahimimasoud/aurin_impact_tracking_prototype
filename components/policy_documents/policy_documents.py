"""
Policy documents component for displaying policy documents relevant to AURIN.
"""
from components.base_component import BaseComponent
import streamlit as st
import pandas as pd


class PolicyDocumentsComponent(BaseComponent):
    """Component for displaying policy documents referencing AURIN."""

    def __init__(self, data: pd.DataFrame = None, web_data: pd.DataFrame = None, **kwargs):
        super().__init__(data=data, **kwargs)
        self.web_data = web_data

    def _normalize(self, df: pd.DataFrame, source_label: str) -> pd.DataFrame:
        """Return a normalised slice with canonical column names and a Source column."""
        col_map = {
            "title": "Title",
            "year": "Year",
            "linkout": "Link",
        }
        # Publisher column differs between sources
        if "publisher_org.name" in df.columns:
            col_map["publisher_org.name"] = "Publisher"
        elif "publisher_name" in df.columns:
            col_map["publisher_name"] = "Publisher"

        # Country column differs between sources
        if "publisher_org.country_name" in df.columns:
            col_map["publisher_org.country_name"] = "Country"
        elif "publisher_country" in df.columns:
            col_map["publisher_country"] = "Country"

        available = [c for c in col_map if c in df.columns]
        out = df[available].rename(columns=col_map).copy()
        out["Source"] = source_label
        return out

    def render(self) -> None:
        """Render the policy documents component."""
        st.markdown(
            '<div class="section-header">📄 Policy Documents Referencing AURIN</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Combines Dimensions Policy Documents database results with web-discovered documents "
            "(via DuckDuckGo + Gemini AI filtering). Duplicates removed by title."
        )

        has_db = self.validate_data()
        has_web = self.web_data is not None and not self.web_data.empty

        if not has_db and not has_web:
            st.info("No policy documents found for AURIN.")
            return

        parts = []
        if has_db:
            parts.append(self._normalize(self.data, "Dimensions"))
        if has_web:
            parts.append(self._normalize(self.web_data, "Web"))

        combined = pd.concat(parts, ignore_index=True)

        # Deduplicate on normalised title (case-insensitive, stripped)
        combined["_title_key"] = combined["Title"].str.lower().str.strip() if "Title" in combined.columns else ""
        combined = combined.drop_duplicates(subset="_title_key", keep="first").drop(columns="_title_key")

        # ── metrics ─────────────────────────────────────────────────────────
        total = len(combined)
        n_countries = combined["Country"].nunique() if "Country" in combined.columns else None
        n_publishers = combined["Publisher"].nunique() if "Publisher" in combined.columns else None
        year_range = None
        if "Year" in combined.columns:
            years = combined["Year"].dropna()
            if not years.empty:
                year_range = f"{int(years.min())}–{int(years.max())}"

        cols = st.columns(4)
        cols[0].metric("Policy Documents", total)
        if n_countries is not None:
            cols[1].metric("Countries", n_countries)
        if n_publishers is not None:
            cols[2].metric("Publishers", n_publishers)
        if year_range:
            cols[3].metric("Year Range", year_range)

        # Sort by year descending
        if "Year" in combined.columns:
            combined = combined.sort_values("Year", ascending=False, na_position="last")

        column_config = {
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Publisher": st.column_config.TextColumn("Publisher", width="medium"),
            "Country": st.column_config.TextColumn("Country", width="small"),
            "Year": st.column_config.NumberColumn("Year", width="small"),
            "Source": st.column_config.TextColumn("Source", width="small"),
        }
        if "Link" in combined.columns:
            column_config["Link"] = st.column_config.LinkColumn("Link", display_text="Open", width="small")

        st.dataframe(
            combined,
            width='stretch',
            hide_index=True,
            column_config=column_config,
        )

        st.caption(f"Total: {total} policy document(s) found.")

        csv = combined.to_csv(index=False)
        st.download_button(
            label="⬇️ Download policy documents as CSV",
            data=csv,
            file_name="aurin_policy_documents.csv",
            mime="text/csv",
        )
