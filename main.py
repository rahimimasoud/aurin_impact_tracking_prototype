"""
Main Streamlit application for AURIN Impact Tracking Dashboard.
This file orchestrates all components and data loading.
"""
import streamlit as st
import datetime

from data_loader import DimensionsDataLoader, PolicyDocumentsDataLoader
from components.sidebar import SidebarComponent
from components.header import HeaderComponent
from components.key_metrics import KeyMetricsComponent
from components.top_cited_articles import TopCitedArticlesComponent
from components.affiliated_organisations import AffiliatedOrganisationsComponent
from components.affiliated_countries import AffiliatedCountriesComponent
from components.recent_papers import RecentPapersComponent
from components.papers_last_6_months import PapersLast6MonthsComponent
from components.citation_distribution import CitationDistributionComponent
from components.policy_documents import PolicyDocumentsComponent


# Page configuration
st.set_page_config(
    page_title="AURIN Impact Tracking Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize sidebar component
sidebar = SidebarComponent()
sidebar.render()

# Initialize header component
header = HeaderComponent()
header.render()

# Get API key and date range from sidebar
api_key = sidebar.get_api_key()
from_date, to_date = sidebar.get_date_range()

# Convert date objects to strings in YYYY-MM-DD format if they exist
from_date_str = from_date.strftime("%Y-%m-%d") if from_date else None
to_date_str = to_date.strftime("%Y-%m-%d") if to_date else None

# Initialize data loader
data_loader = DimensionsDataLoader()

# Load data
if api_key:
    with st.spinner("Loading AURIN data from Dimensions API..."):
        df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators = data_loader.load_data(
            api_key, 
            from_date=from_date_str, 
            to_date=to_date_str
        )
else:
    df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators = None, None, None, None, None

# Render components if data is available
if df_aurin_main is not None:
    tab_research, tab_research_organisations, tab_policies = st.tabs(["Research Papers", "Research Organisations", "Policies"])

    with tab_research:
        # Initialize and render all components
        key_metrics = KeyMetricsComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations
        )
        key_metrics.render()

        top_cited = TopCitedArticlesComponent(data=df_aurin_main)
        top_cited.render()

        recent_papers = RecentPapersComponent(data=df_aurin_main)
        recent_papers.render()

        if not from_date_str and not to_date_str:
            papers_6_months = PapersLast6MonthsComponent(data=df_aurin_main)
            papers_6_months.render()

    with tab_research_organisations:
        affiliated_orgs = AffiliatedOrganisationsComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations
        )
        affiliated_orgs.render()

        affiliated_countries = AffiliatedCountriesComponent(affiliations_data=df_affiliations)
        affiliated_countries.render()
        

    with tab_policies:
        policy_loader = PolicyDocumentsDataLoader()
        with st.spinner("Loading policy documents from Dimensions API..."):
            df_policies = policy_loader.load_data(api_key)
        policy_docs = PolicyDocumentsComponent(data=df_policies)
        policy_docs.render()

else:
    if not api_key:
        st.info("👆 Please enter your Dimensions API key in the sidebar to load the dashboard data.")
    else:
        st.error("Failed to load data. Please check your API credentials and connection.")
