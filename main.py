"""
Main Streamlit application for AURIN Impact Tracking Dashboard.
This file orchestrates all components and data loading.
"""
import streamlit as st

from data_loader import DimensionsDataLoader, PolicyDocumentsDataLoader, GrantsDataLoader, PatentsDataLoader, ResearchTrendMonitorDataLoader, GrantTrendMonitorDataLoader
from components.sidebar import SidebarComponent
from components.header import HeaderComponent
from components.key_metrics import KeyMetricsComponent
from components.top_cited_articles import TopCitedArticlesComponent
from components.affiliated_organisations import AffiliatedOrganisationsComponent
from components.affiliated_countries import AffiliatedCountriesComponent
from components.recent_papers import RecentPapersComponent
from components.policy_documents import PolicyDocumentsComponent
from components.grants import GrantsComponent
from components.patents import PatentsComponent
from components.research_categories import ResearchCategoriesComponent
from components.sdg_categories import SDGCategoriesComponent
from components.concepts import ConceptsComponent
from components.trends import TrendsComponent
from components.research_trend_monitor import ResearchTrendMonitorComponent
from components.grant_trend_monitor import GrantTrendMonitorComponent
from components.ai_summary import AISummaryComponent
from components.ai_summary.gemini_provider import GeminiProvider


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

# Get API key, Gemini key and date range from sidebar
api_key = sidebar.get_api_key()
gemini_api_key = sidebar.get_gemini_api_key()
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

    tab_ai_summary, tab_research, tab_research_organisations, tab_policies, tab_patents, tab_grants, tab_trend_monitor, tab_grant_trend_monitor = st.tabs(["AI Summary", "Research Papers", "Research Organisations", "Policy Documents", "Patents", "AURIN Fundings", "Research Trend Monitor", "Grant Trend Monitor"])

    with tab_ai_summary:
        ai_summary = AISummaryComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations,
            policies_data=df_policies,
            patents_data=df_patents,
            grants_data=df_grants,
            date_from=from_date_str,
            date_to=to_date_str,
            provider=GeminiProvider(api_key=gemini_api_key),
        )
        ai_summary.render()

    with tab_research:
        # Initialize and render all components
        key_metrics = KeyMetricsComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations
        )
        key_metrics.render()

        trends = TrendsComponent(data=df_aurin_main)
        trends.render()

        top_cited = TopCitedArticlesComponent(data=df_aurin_main)
        top_cited.render()

        recent_papers = RecentPapersComponent(data=df_aurin_main)
        recent_papers.render()

        research_categories = ResearchCategoriesComponent(data=df_aurin_main)
        research_categories.render()

        sdg_categories = SDGCategoriesComponent(data=df_aurin_main)
        sdg_categories.render()

        concepts = ConceptsComponent(data=df_aurin_main)
        concepts.render()



    with tab_research_organisations:
        affiliated_orgs = AffiliatedOrganisationsComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations
        )
        affiliated_orgs.render()

        affiliated_countries = AffiliatedCountriesComponent(affiliations_data=df_affiliations)
        affiliated_countries.render()
        

    with tab_policies:
        policy_docs = PolicyDocumentsComponent(data=df_policies)
        policy_docs.render()

    with tab_patents:
        patents = PatentsComponent(data=df_patents)
        patents.render()

    with tab_grants:
        grants = GrantsComponent(data=df_grants)
        grants.render()

    with tab_trend_monitor:
        trend_monitor = ResearchTrendMonitorComponent(publications_data=df_trend_monitor)
        trend_monitor.render()

    with tab_grant_trend_monitor:
        grant_trend_monitor = GrantTrendMonitorComponent(grants_data=df_grant_trend_monitor)
        grant_trend_monitor.render()

else:
    if not api_key:
        st.info("👆 Please enter your Dimensions API key in the sidebar to load the dashboard data.")
    else:
        st.error("Failed to load data. Please check your API credentials and connection.")
