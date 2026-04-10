"""
Trends component for visualizing publication and citation trends over time.
"""
from components.base_component import BaseComponent
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class TrendsComponent(BaseComponent):
    """Component for displaying publication and citation trends over time."""

    def __init__(self, data: pd.DataFrame = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def _prepare_yearly_data(self) -> pd.DataFrame:
        df = self.data.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['year'] = df['date'].dt.year
        df = df[df['year'] >= 2009] # Filter for publications from 2009 onwards when AURIN started contributing.
        return df

    def _render_papers_per_year(self, df: pd.DataFrame) -> None:
        yearly_counts = df.groupby('year').size().reset_index(name='papers')
        yearly_counts = yearly_counts.sort_values('year')

        fig = go.Figure()
        fig.add_bar(
            x=yearly_counts['year'],
            y=yearly_counts['papers'],
            name='Papers per Year',
            marker_color='steelblue',
        )

        if 'times_cited' in df.columns:
            yearly_citations = (
                df.groupby('year')['times_cited']
                .sum()
                .reset_index(name='total_citations')
                .sort_values('year')
            )
            yearly_citations['cumulative_citations'] = yearly_citations['total_citations'].cumsum()
            fig.add_scatter(
                x=yearly_citations['year'],
                y=yearly_citations['cumulative_citations'],
                name='Cumulative Citations',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='orange', width=2),
            )
            fig.update_layout(
                yaxis2=dict(title='Cumulative Citations', overlaying='y', side='right'),
            )

        fig.update_layout(
            title='Papers Published per Year',
            height=350,
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title='Number of Papers'),
            legend=dict(orientation='h', y=1.1),
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_publication_types_over_time(self, df: pd.DataFrame) -> None:
        if 'type' not in df.columns:
            return

        type_year = (
            df.groupby(['year', 'type'])
            .size()
            .reset_index(name='count')
            .sort_values('year')
        )

        fig = px.area(
            type_year,
            x='year',
            y='count',
            color='type',
            title='Publication Types Over Time',
            labels={'year': 'Year', 'count': 'Number of Papers', 'type': 'Type'},
        )
        fig.update_layout(height=350, xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig, use_container_width=True)


    def render(self) -> None:
        """Render the trends component."""
        if not self.validate_data():
            st.warning("No data available to display trends.")
            return

        st.markdown('<div class="section-header">📈 Research Trends Over Time</div>', unsafe_allow_html=True)

        df = self._prepare_yearly_data()
        if df.empty:
            st.info("No dated publications available for trend analysis.")
            return

        col1, col2 = st.columns(2)
        with col1:
            self._render_papers_per_year(df)
        with col2:
            self._render_publication_types_over_time(df)

