"""
Main Streamlit application for AURIN Impact Tracking Dashboard.
This file orchestrates all components and data loading.
"""
import streamlit as st

from data_loader import DimensionsDataLoader, PolicyDocumentsDataLoader, GrantsDataLoader, PatentsDataLoader, ResearchTrendMonitorDataLoader, GrantTrendMonitorDataLoader
from components.sidebar import SidebarComponent
from components.header import HeaderComponent
from components.research_papers import (
    KeyMetricsComponent,
    TrendsComponent,
    TopCitedArticlesComponent,
    RecentPapersComponent,
    ResearchCategoriesComponent,
    SDGCategoriesComponent,
    ConceptsComponent,
)
from components.research_organisations import AffiliatedOrganisationsComponent, AffiliatedCountriesComponent
from components.policy_documents import PolicyDocumentsComponent
from components.patents import PatentsComponent
from components.aurin_fundings import GrantsComponent
from components.research_trend import ResearchTrendMonitorComponent
from components.grant_trend import GrantTrendMonitorComponent
from components.ai_summary import AISummaryComponent
from components.ai_summary.gemini_provider import GeminiProvider


# Page configuration
st.set_page_config(
    page_title="AURIN Impact Tracking Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
sidebar = SidebarComponent()
header = HeaderComponent()

# Sidebar: navigation + config
sidebar.render()

# Header: title
header.render()

# Retrieve credentials and active tab
api_key = sidebar.get_api_key()
gemini_api_key = sidebar.get_gemini_api_key()
from_date, to_date = sidebar.get_date_range()
active_tab = sidebar.get_active_tab()

# Convert date objects to strings in YYYY-MM-DD format if they exist
from_date_str = from_date.strftime("%Y-%m-%d") if from_date else None
to_date_str = to_date.strftime("%Y-%m-%d") if to_date else None

# Load data
data_loader = DimensionsDataLoader()

if api_key:
    with st.spinner("Loading AURIN data from Dimensions API..."):
        df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators = data_loader.load_data(
            api_key,
            from_date=from_date_str,
            to_date=to_date_str
        )
else:
    df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators = None, None, None, None, None

if df_aurin_main is not None:
    # Load secondary datasets up front so the AI summary can use them all
    with st.spinner("Loading policy documents from Dimensions API..."):
        df_policies = PolicyDocumentsDataLoader().load_data(api_key, from_date=from_date_str, to_date=to_date_str)
    with st.spinner("Loading patents from Dimensions API..."):
        df_patents = PatentsDataLoader().load_data(api_key, from_date=from_date_str, to_date=to_date_str)
    with st.spinner("Loading grants from Dimensions API..."):
        df_grants = GrantsDataLoader().load_data(api_key, from_date=from_date_str, to_date=to_date_str)
    with st.spinner("Loading 10-year trend monitor data from Dimensions API..."):
        df_trend_monitor = ResearchTrendMonitorDataLoader().load_data(api_key)
    with st.spinner("Loading grant trend monitor data from Dimensions API..."):
        df_grant_trend_monitor = GrantTrendMonitorDataLoader().load_data(api_key)

    # Render the active section
    if active_tab == "ai_summary":
        AISummaryComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations,
            policies_data=df_policies,
            patents_data=df_patents,
            grants_data=df_grants,
            date_from=from_date_str,
            date_to=to_date_str,
            provider=GeminiProvider(api_key=gemini_api_key),
        ).render()

    elif active_tab == "research_papers":
        KeyMetricsComponent(main_data=df_aurin_main, affiliations_data=df_affiliations).render()
        TrendsComponent(data=df_aurin_main).render()
        TopCitedArticlesComponent(data=df_aurin_main).render()
        RecentPapersComponent(data=df_aurin_main).render()
        ResearchCategoriesComponent(data=df_aurin_main).render()
        SDGCategoriesComponent(data=df_aurin_main).render()
        ConceptsComponent(data=df_aurin_main).render()

    elif active_tab == "research_organisations":
        AffiliatedOrganisationsComponent(main_data=df_aurin_main, affiliations_data=df_affiliations).render()
        AffiliatedCountriesComponent(affiliations_data=df_affiliations).render()

    elif active_tab == "policy_documents":
        PolicyDocumentsComponent(data=df_policies).render()

    elif active_tab == "patents":
        PatentsComponent(data=df_patents).render()

    elif active_tab == "aurin_fundings":
        GrantsComponent(data=df_grants).render()

    elif active_tab == "research_trend_monitor":
        ResearchTrendMonitorComponent(publications_data=df_trend_monitor).render()

    elif active_tab == "grant_trend_monitor":
        GrantTrendMonitorComponent(grants_data=df_grant_trend_monitor).render()

else:
    if not api_key:
        st.info("👈 Please configure your Dimensions API key using the sidebar to load the dashboard.")
    else:
        st.error("Failed to load data. Please check your API credentials and connection.")
