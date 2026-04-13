"""
Grants component for displaying grants relevant to AURIN.
"""
from components.base_component import BaseComponent
import streamlit as st
import pandas as pd


class GrantsComponent(BaseComponent):
    """Component for displaying grants referencing AURIN."""

    def __init__(self, data: pd.DataFrame = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def render(self) -> None:
        """Render the grants component."""
        st.markdown(
            '<div class="section-header">💰 Grants Enabling AURIN</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Grants discovered via full-text search for "
            '"Australian Urban Research Infrastructure Network"'
            "in the Dimensions Grants database."
        )

        if not self.validate_data():
            st.info("No grants found for AURIN.")
            return

        df = self.data.copy()

        # ── column selection ────────────────────────────────────────────────
        col_map = {}
        if "title" in df.columns:
            col_map["title"] = "Title"
        if "start_date" in df.columns:
            col_map["start_date"] = "Start Date"
        if "end_date" in df.columns:
            col_map["end_date"] = "End Date"
        if "funding_org_name" in df.columns:
            col_map["funding_org_name"] = "Funder"
        if "funding_usd" in df.columns:
            col_map["funding_usd"] = "Funding (USD)"
        if "linkout" in df.columns:
            col_map["linkout"] = "Link"

        available_cols = [c for c in col_map if c in df.columns]
        if not available_cols:
            st.dataframe(df, width='stretch', hide_index=True)
            return

        display_df = df[available_cols].rename(columns=col_map)

        # ── metrics ─────────────────────────────────────────────────────────
        total = len(df)
        n_funders = df["funding_org_name"].nunique() if "funding_org_name" in df.columns else None
        total_funding = None
        if "funding_usd" in df.columns:
            funding_vals = pd.to_numeric(df["funding_usd"], errors="coerce").dropna()
            if not funding_vals.empty:
                total_funding = funding_vals.sum()

        cols = st.columns(3)
        cols[0].metric("Total Grants", total)
        if n_funders is not None:
            cols[1].metric("Funders", n_funders)
        if total_funding is not None:
            cols[2].metric("Total Funding (USD)", f"${total_funding:,.0f}")

        # Sort by start_date descending
        if "Start Date" in display_df.columns:
            display_df = display_df.sort_values("Start Date", ascending=False, na_position="last")

        column_config = {
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Funder": st.column_config.TextColumn("Funder", width="medium"),
            "Funding (USD)": st.column_config.NumberColumn("Funding (USD)", format="$%d", width="small"),
            "Start Date": st.column_config.TextColumn("Start Date", width="small"),
            "End Date": st.column_config.TextColumn("End Date", width="small"),
        }
        if "Link" in display_df.columns:
            column_config["Link"] = st.column_config.LinkColumn("Link", display_text="Open", width="small")

        st.dataframe(
            display_df,
            width='stretch',
            hide_index=True,
            column_config=column_config,
        )

        st.caption(f"Total: {len(display_df)} grant(s) found.")

        # Download
        csv_df = df[available_cols].rename(columns=col_map)
        csv = csv_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download grants as CSV",
            data=csv,
            file_name="aurin_grants.csv",
            mime="text/csv",
        )
