"""
Research categories component for displaying Field of Research (FOR) breakdown.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px


class ResearchCategoriesComponent(BaseComponent):
    """Component for displaying paper counts by Field of Research (FOR) category."""

    def __init__(self, data: Optional[pd.DataFrame] = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def _parse_categories(self) -> Optional[pd.DataFrame]:
        """Explode category_for into one row per category and return counts."""
        if 'category_for' not in self.data.columns:
            return None

        df = self.data[['id', 'category_for']].dropna(subset=['category_for'])
        if df.empty:
            return None

        rows = []
        for _, row in df.iterrows():
            cats = row['category_for']
            if not isinstance(cats, list):
                continue
            for cat in cats:
                if isinstance(cat, dict):
                    name = cat.get('name') or cat.get('id', '')
                elif isinstance(cat, str):
                    name = cat
                else:
                    continue
                if name:
                    rows.append(name)

        if not rows:
            return None

        counts = pd.Series(rows).value_counts().reset_index()
        counts.columns = ['Category', 'Papers']
        return counts

    def render(self) -> None:
        """Render the research categories component."""
        if not self.validate_data():
            st.info("No category data available.")
            return

        counts = self._parse_categories()
        if counts is None or counts.empty:
            st.info("No Field of Research categories found in the data.")
            return

        st.markdown('<div class="section-header">🔬 Field of Research (FOR) Categories</div>', unsafe_allow_html=True)

        top5 = counts.head(5)

        # Top 5 highlight cards
        st.markdown("**Top 5 Categories**")
        cols = st.columns(5)
        for i, (_, row) in enumerate(top5.iterrows()):
            with cols[i]:
                st.metric(label=row['Category'], value=f"{row['Papers']} papers")

        with st.expander(f"View all {len(counts)} categories"):
            fig = px.bar(
                counts,
                x='Papers',
                y='Category',
                orientation='h',
                title="Papers by FOR Category",
                labels={'Papers': 'Number of Papers', 'Category': ''},
                color='Papers',
                color_continuous_scale='Blues',
            )
            fig.update_layout(
                height=max(400, len(counts) * 28),
                yaxis={'categoryorder': 'total ascending'},
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, width='stretch')
