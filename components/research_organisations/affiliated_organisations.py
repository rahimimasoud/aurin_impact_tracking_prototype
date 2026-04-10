"""
Affiliated organisations component for displaying impact analysis.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px


class AffiliatedOrganisationsComponent(BaseComponent):
    """Component for displaying affiliated organisations analysis."""
    
    def __init__(self, main_data: Optional[pd.DataFrame] = None,
                 affiliations_data: Optional[pd.DataFrame] = None, **kwargs):
        """
        Initialize the affiliated organisations component.
        
        Args:
            main_data: Main publications DataFrame
            affiliations_data: Affiliations DataFrame
        """
        super().__init__(data=main_data, **kwargs)
        self.affiliations_data = affiliations_data
    
    def render(self) -> None:
        """Render the affiliated organisations component."""
        if self.affiliations_data is None or self.affiliations_data.empty:
            st.info("No affiliated organisations found.")
            return
        
        st.markdown('<div class="section-header">🏢 Affiliated Organisations We Had Impact On</div>', unsafe_allow_html=True)
        
        # Calculate metrics per organization, grouped by aff_name and aff_country
        # Count unique researcher_id values for each organization
        # Group by both aff_name and aff_country, then count unique researcher_ids
        org_metrics = self.affiliations_data.groupby(['aff_name', 'aff_country']).agg({
            'researcher_id': 'nunique'  # Count unique researcher IDs
        }).reset_index()
        org_metrics.columns = ['aff_name', 'aff_country', 'researcher_count']

        
        # Add citation data if available
        if 'times_cited' in self.affiliations_data.columns:
            # First, ensure pub_id is unique per organization before counting citations
            # Group by aff_name, aff_country, and pub_id to get unique publications per org
            unique_pubs = self.affiliations_data.groupby(['aff_name', 'aff_country', 'pub_id'])['times_cited'].first().reset_index()
            # Now sum citations per organization
            org_citations = unique_pubs.groupby(['aff_name', 'aff_country'])['times_cited'].sum().reset_index()
            org_metrics = org_metrics.merge(org_citations, on=['aff_name', 'aff_country'], how='left')
            org_metrics['times_cited'] = org_metrics['times_cited'].fillna(0)
        else:
            org_metrics['times_cited'] = 0
        
        # Sort by publication count (descending)
        org_metrics = org_metrics.sort_values('researcher_count', ascending=False)
        
        # Summary metrics
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            st.metric("Total Organizations", len(org_metrics))
        with col2:
            st.metric("Avg Publications/Org", f"{org_metrics['researcher_count'].mean():.1f}")
        with col3:
            top_org_name = org_metrics.iloc[0]['aff_name']
            st.metric("Top Contributing Org", top_org_name)
        
        # Search and filter options
        st.subheader("🔍 Organization Explorer")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Search organizations:", placeholder="Type to filter organizations...")
        with col2:
            sort_by = st.selectbox("Sort by:", ["Publications", "Citations", "Name", "Country"])
        
        # Filter organizations based on search
        if search_term:
            filtered_orgs = org_metrics[org_metrics['aff_name'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_orgs = org_metrics.copy()
        
        # Sort based on selection
        if sort_by == "Researchers":
            filtered_orgs = filtered_orgs.sort_values('researcher_count', ascending=False)
        elif sort_by == "Citations":
            filtered_orgs = filtered_orgs.sort_values('times_cited', ascending=False)
        elif sort_by == "Name":
            filtered_orgs = filtered_orgs.sort_values('aff_name')
        elif sort_by == "Country":
            filtered_orgs = filtered_orgs.sort_values('aff_country')
        
        # Display filtered results
        if not filtered_orgs.empty:
            st.info(f"Showing {len(filtered_orgs)} organizations (filtered from {len(org_metrics)} total)")
            
            # Create expandable sections for top organizations
            st.subheader("🏆 Top Contributing Organizations")
            
            # Show top 10 in expandable format
            for i, (_, org) in enumerate(filtered_orgs.head(10).iterrows()):
                with st.expander(f"#{i+1} {org['aff_name']} ({org['researcher_count']} unique researchers)"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Unique Researchers", org['researcher_count'])
                    with col2:
                        st.metric("Total Citations", f"{org['times_cited']:,}")
                    with col3:
                        st.metric("Country", org['aff_country'])
                    
                    # Show publications from this organization
                    org_researcher = self.affiliations_data[self.affiliations_data['aff_name'] == org['aff_name']]
                    if not org_researcher.empty:
                        st.write("**Researchers from this organization:**")
                        st.write(f"• {org['researcher_count']} unique researchers found")
                        # If we have researcher IDs, we could link to main research groups
                        if 'researcher_id' in self.affiliations_data.columns:
                            # Get top 3 most recurring researcher IDs (drop empty ones)
                            # printing top three researchers from this organisation
                            num_researchers = 3
                            org_researcher_filtered = org_researcher[org_researcher['researcher_id'].notna() & (org_researcher['researcher_id'] != '')]
                            researcher_counts = org_researcher_filtered['researcher_id'].value_counts().head(num_researchers)
                            researcher_ids = researcher_counts.index.tolist()
                            if len(researcher_ids) > 0:
                                # Check if we have name columns
                                has_names = 'first_name' in self.affiliations_data.columns and 'last_name' in self.affiliations_data.columns
                                if has_names:
                                    st.write("**Top researchers from this organisation:**")
                                    for idx, researcher_id in enumerate(researcher_ids, 1):
                                        researcher_affiliation = self.affiliations_data[
                                            self.affiliations_data['researcher_id'] == researcher_id
                                        ]
                                        if not researcher_affiliation.empty:
                                            first_name = researcher_affiliation['first_name'].iloc[0]
                                            last_name = researcher_affiliation['last_name'].iloc[0]
                                            pub_count = researcher_counts[researcher_id]
                                            st.markdown(f"**{idx}.** {first_name} {last_name} ({pub_count} publication{'s' if pub_count > 1 else ''})")
                        else:
                            st.write("• Researcher details available in main dataset")
            
            # Interactive data table
            st.subheader("📊 Complete Organization Data")
            display_orgs = filtered_orgs[['aff_name', 'aff_country', 'researcher_count', 'times_cited']].copy()
            display_orgs.columns = ['Organization', 'Country', 'Publications', 'Total Citations']
            display_orgs['Avg Citations'] = (display_orgs['Total Citations'] / display_orgs['Publications']).round(1)
            
            st.dataframe(
                display_orgs,
                use_container_width=True,
                hide_index=True
            )
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 15 organizations by publications
                top_15 = filtered_orgs.head(15)
                fig_orgs = px.bar(
                    top_15,
                    x='researcher_count',
                    y='aff_name',
                    orientation='h',
                    title="Top 15 Organizations by Researcher Count",
                    labels={'researcher_count': 'Number of Researchers', 'aff_name': 'Organisation'},
                    color='researcher_count',
                    color_continuous_scale='Blues'
                )
                fig_orgs.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_orgs, use_container_width=True)
            
            with col2:
                # Organizations by country
                country_org_counts = filtered_orgs.groupby('aff_country').size().sort_values(ascending=False)
                fig_countries = px.pie(
                    values=country_org_counts.values,
                    names=country_org_counts.index,
                    title="Organizations by Country"
                )
                fig_countries.update_layout(height=500)
                st.plotly_chart(fig_countries, use_container_width=True)
        else:
            st.warning("No organizations found matching your search criteria.")

