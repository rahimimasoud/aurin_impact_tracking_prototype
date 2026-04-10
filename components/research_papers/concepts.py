"""
Concepts component for displaying key research concepts breakdown.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt


class ConceptsComponent(BaseComponent):
    """Component for displaying paper counts by research concept."""

    def __init__(self, data: Optional[pd.DataFrame] = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def _parse_concepts(self) -> Optional[pd.DataFrame]:
        """Explode concepts into one row per concept and return counts."""
        if 'concepts' not in self.data.columns:
            return None

        df = self.data[['id', 'concepts']].dropna(subset=['concepts'])
        if df.empty:
            return None

        rows = []
        for _, row in df.iterrows():
            cats = row['concepts']
            if not isinstance(cats, list):
                continue
            for cat in cats:
                if isinstance(cat, dict):
                    name = cat.get('concept') or cat.get('name') or cat.get('id', '')
                elif isinstance(cat, str):
                    name = cat
                else:
                    continue
                if name:
                    rows.append(name)

        if not rows:
            return None

        counts = pd.Series(rows).value_counts().reset_index()
        counts.columns = ['Concept', 'Papers']
        return counts

    def render(self) -> None:
        """Render the concepts component."""
        if not self.validate_data():
            st.info("No concepts data available.")
            return

        counts = self._parse_concepts()
        if counts is None or counts.empty:
            st.info("No concepts found in the data.")
            return

        st.markdown('<div class="section-header">💡 Key Research Concepts</div>', unsafe_allow_html=True)

        freq = dict(zip(counts['Concept'], counts['Papers']))
        wc = WordCloud(width=1200, height=500, background_color='white', colormap='Purples').generate_from_frequencies(freq)

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        plt.close(fig)
