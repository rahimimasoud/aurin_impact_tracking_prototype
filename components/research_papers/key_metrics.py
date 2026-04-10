"""
Key metrics component for displaying summary statistics.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd


class KeyMetricsComponent(BaseComponent):
    """Component for displaying key metrics."""
    
    def __init__(self, main_data: Optional[pd.DataFrame] = None, 
                 affiliations_data: Optional[pd.DataFrame] = None, **kwargs):
        """
        Initialize the key metrics component.
        
        Args:
            main_data: Main publications DataFrame
            affiliations_data: Affiliations DataFrame
        """
        super().__init__(data=main_data, **kwargs)
        self.affiliations_data = affiliations_data
    
    def render(self) -> None:
        """Render the key metrics component."""
        if not self.validate_data():
            st.warning("No data available to display metrics.")
            return
        
        st.markdown('<div class="section-header">📈 Key Metrics (All Time)</div>', unsafe_allow_html=True)
        
        # Calculate metrics
        total_publications = len(self.data)
        total_citations = self.data['times_cited'].sum()
        
        affiliated_organisations_count = 0
        affiliated_countries_count = 0
        
        if self.affiliations_data is not None and not self.affiliations_data.empty:
            affiliated_organisations_count = len(self.affiliations_data['aff_name'].unique())
            affiliated_countries_count = len(self.affiliations_data['aff_country'].unique())
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Publications",
                value=total_publications,
                delta=None
            )
        
        with col2:
            st.metric(
                label="Total Citations",
                value=f"{total_citations:,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Affiliated Organisations",
                value=affiliated_organisations_count,
                delta=None
            )
        
        with col4:
            st.metric(
                label="Affiliated Countries",
                value=affiliated_countries_count,
                delta=None
            )
    
    def set_affiliations_data(self, affiliations_data: pd.DataFrame) -> None:
        """
        Set the affiliations data.
        
        Args:
            affiliations_data: Affiliations DataFrame
        """
        self.affiliations_data = affiliations_data

