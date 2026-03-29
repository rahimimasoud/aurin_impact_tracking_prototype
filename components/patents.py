"""
Patents component for displaying patents relevant to AURIN.
"""
from components.base_component import BaseComponent
import streamlit as st
import pandas as pd


class PatentsComponent(BaseComponent):
    """Component for displaying patents referencing AURIN."""

    def __init__(self, data: pd.DataFrame = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def render(self) -> None:
        """Render the patents component."""
        st.markdown(
            '<div class="section-header">🔬 Patents Including AURIN</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Patents discovered via full-text search for "
            '"Australian Urban Research Infrastructure Network" or "Australia\'s Spatial Intelligence Network" '
            "in the Dimensions Patents database."
        )

        if not self.validate_data():
            st.info("No patents found for AURIN.")
            return

        df = self.data.copy()

        # ── column selection ────────────────────────────────────────────────
        col_map = {}
        if "title" in df.columns:
            col_map["title"] = "Title"
        if "publication_date" in df.columns:
            col_map["publication_date"] = "Publication Date"
        if "filing_date" in df.columns:
            col_map["filing_date"] = "Filing Date"
        if "assignees" in df.columns:
            col_map["assignees"] = "Assignees"
        if "inventors" in df.columns:
            col_map["inventors"] = "Inventors"
        if "jurisdiction" in df.columns:
            col_map["jurisdiction"] = "Jurisdiction"
        if "legal_status" in df.columns:
            col_map["legal_status"] = "Status"
        if "dimensions_url" in df.columns:
            col_map["dimensions_url"] = "Link"

        available_cols = [c for c in col_map if c in df.columns]
        if not available_cols:
            st.dataframe(df, use_container_width=True, hide_index=True)
            return

        display_df = df[available_cols].rename(columns=col_map)

        # ── metrics ─────────────────────────────────────────────────────────
        total = len(df)
        n_jurisdictions = df["jurisdiction"].nunique() if "jurisdiction" in df.columns else None
        n_assignees = df["assignee_names"].nunique() if "assignee_names" in df.columns else (df["assignees"].nunique() if "assignees" in df.columns else None)

        cols = st.columns(3)
        cols[0].metric("Total Patents", total)
        if n_jurisdictions is not None:
            cols[1].metric("Jurisdictions", n_jurisdictions)
        if n_assignees is not None:
            cols[2].metric("Assignees", n_assignees)

        # Sort by publication_date descending
        if "Publication Date" in display_df.columns:
            display_df = display_df.sort_values("Publication Date", ascending=False, na_position="last")

        column_config = {
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Assignees": st.column_config.TextColumn("Assignees", width="medium"),
            "Inventors": st.column_config.TextColumn("Inventors", width="medium"),
            "Jurisdiction": st.column_config.TextColumn("Jurisdiction", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Publication Date": st.column_config.TextColumn("Publication Date", width="small"),
            "Filing Date": st.column_config.TextColumn("Filing Date", width="small"),
        }
        if "Link" in display_df.columns:
            column_config["Link"] = st.column_config.LinkColumn("Link", display_text="Open", width="small")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )

        st.caption(f"Total: {len(display_df)} patent(s) found.")

        # Download
        csv_df = df[available_cols].rename(columns=col_map)
        csv = csv_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download patents as CSV",
            data=csv,
            file_name="aurin_patents.csv",
            mime="text/csv",
        )
