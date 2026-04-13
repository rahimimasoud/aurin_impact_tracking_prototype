"""
Affiliated countries component for displaying geographic impact.
"""
from components.base_component import BaseComponent
from components.utils import get_country_code, PYCOUNTRY_AVAILABLE
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px


class AffiliatedCountriesComponent(BaseComponent):
    """Component for displaying affiliated countries analysis."""
    
    def __init__(self, affiliations_data: Optional[pd.DataFrame] = None, **kwargs):
        """
        Initialize the affiliated countries component.
        
        Args:
            affiliations_data: Affiliations DataFrame
        """
        super().__init__(data=affiliations_data, **kwargs)
    
    def render(self) -> None:
        """Render the affiliated countries component."""
        if not self.validate_data():
            st.info("No affiliated countries found.")
            return
        
        st.markdown('<div class="section-header">🌍 Affiliated Countries We Had Impact On</div>', unsafe_allow_html=True)
        
        # Get unique countries (drop empty records)
        affiliated_countries = self.data[self.data['aff_country'].notna() & (self.data['aff_country'] != '')]['aff_country'].unique()
        
        if len(affiliated_countries) > 0:
            # Create a DataFrame for better display
            country_df = pd.DataFrame({
                'Country': affiliated_countries
            }).sort_values('Country')
            
            # Display in columns
            cols = st.columns(4)
            for i, country in enumerate(country_df['Country']):
                with cols[i % 4]:
                    st.write(f"• {country}")
            
            # Create a world map visualization
            country_counts = self.data[self.data['aff_country'].notna() & (self.data['aff_country'] != '')]['aff_country'].value_counts()
            
            # Prepare data for choropleth map
            map_df = pd.DataFrame({
                'country': country_counts.index,
                'count': country_counts.values
            })
            
            # Convert country names to ISO-3 codes if pycountry is available
            if PYCOUNTRY_AVAILABLE:
                map_df['iso_code'] = map_df['country'].apply(get_country_code)
                map_df = map_df[map_df['iso_code'].notna()]  # Remove countries without ISO codes
                
                if len(map_df) > 0:
                    # Create binary indicator for highlighting countries
                    map_df['highlight'] = 1
                    fig_map = px.choropleth(
                        map_df,
                        locations='iso_code',
                        color='highlight',
                        hover_name='country',
                        hover_data={'count': True, 'iso_code': False, 'highlight': False},
                        title="Distribution of Publications by Country",
                        labels={'count': 'Number of Publications'}
                    )
                    # Set all countries to green color (override colorscale)
                    fig_map.update_traces(
                        marker_line_color='white',
                        marker_line_width=0.5,
                        colorscale=[[0, '#2ecc71'], [1, '#2ecc71']],  # Single green color
                        colorbar=None  # Remove colorbar
                    )
                    fig_map.update_layout(
                        height=800,
                        showlegend=False,
                        coloraxis_showscale=False,  # Hide color scale
                        dragmode=False,
                        geo=dict(
                            showframe=False,
                            showcoastlines=True,
                            projection_type='natural earth',
                            bgcolor='rgba(0,0,0,0)'
                        )
                    )
                    st.plotly_chart(fig_map, width='stretch', config={'scrollZoom': False, 'displayModeBar': False})
                else:
                    # Fallback to pie chart if no ISO codes found
                    fig_countries = px.pie(
                        values=country_counts.values,
                        names=country_counts.index,
                        title="Distribution of Publications by Country"
                    )
                    fig_countries.update_layout(height=800)
                    st.plotly_chart(fig_countries, width='stretch')
            else:
                # Fallback: try using country names directly (plotly may recognize some)
                try:
                    # Create binary indicator for highlighting countries
                    map_df['highlight'] = 1
                    fig_map = px.choropleth(
                        map_df,
                        locations='country',
                        locationmode='country names',
                        color='highlight',
                        hover_name='country',
                        hover_data={'count': True, 'highlight': False},
                        title="Distribution of Publications by Country",
                        labels={'count': 'Number of Publications'}
                    )
                    # Set all countries to green color (override colorscale)
                    fig_map.update_traces(
                        marker_line_color='white',
                        marker_line_width=0.5,
                        colorscale=[[0, '#2ecc71'], [1, '#2ecc71']],  # Single green color
                        colorbar=None  # Remove colorbar
                    )
                    fig_map.update_layout(
                        height=800,
                        showlegend=False,
                        coloraxis_showscale=False,  # Hide color scale
                        dragmode=False,
                        geo=dict(
                            showframe=False,
                            showcoastlines=True,
                            projection_type='natural earth',
                            bgcolor='rgba(0,0,0,0)'
                        )
                    )
                    st.plotly_chart(fig_map, width='stretch', config={'scrollZoom': False, 'displayModeBar': False})
                except Exception:
                    # Final fallback to pie chart
                    fig_countries = px.pie(
                        values=country_counts.values,
                        names=country_counts.index,
                        title="Distribution of Publications by Country"
                    )
                    fig_countries.update_layout(height=800)
                    st.plotly_chart(fig_countries, width='stretch')
        else:
            st.info("No affiliated countries found.")

