"""
Main Streamlit application for AURIN Impact Tracking Dashboard.
This file orchestrates all components and data loading.
"""
import streamlit as st

from data_loader import DimensionsDataLoader, PolicyDocumentsDataLoader, GrantsDataLoader, PatentsDataLoader, ResearchTrendMonitorDataLoader, GrantTrendMonitorDataLoader
from data.capture import DataCapture, CaptureError
from data import AurinDatabase
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

# ── Phase 1: Refresh (runs only when the Refresh Data button was clicked) ──
if st.session_state.get('refresh_requested'):
    # Consume the flag immediately to prevent an infinite rerun loop
    st.session_state.refresh_requested = False
    _progress = st.progress(0.0, text="Starting data capture…")
    try:
        db = AurinDatabase()
        capture = DataCapture(api_key, from_date_str, to_date_str)
        capture.capture_all(
            db,
            progress_callback=lambda frac, label: _progress.progress(frac, text=label),
        )
        _progress.progress(1.0, text="Capture complete.")
        st.cache_data.clear()
        st.success("Data refreshed successfully.")
    except CaptureError as e:
        st.error(f"Refresh failed: {e}")
    except Exception as e:
        st.error(f"Unexpected error during refresh: {e}")
    finally:
        _progress.empty()

# ── Phase 2: Read from DB (always — no API key required to view cached data) ──
data_loader = DimensionsDataLoader()
df_aurin_main, df_authors, df_affiliations, df_funders, df_investigators = data_loader.load_data(
    from_date=from_date_str, to_date=to_date_str
)
df_policies = PolicyDocumentsDataLoader().load_data(from_date=from_date_str, to_date=to_date_str)
df_patents = PatentsDataLoader().load_data(from_date=from_date_str, to_date=to_date_str)
df_grants = GrantsDataLoader().load_data(from_date=from_date_str, to_date=to_date_str)
df_trend_monitor = ResearchTrendMonitorDataLoader().load_data()
df_grant_trend_monitor = GrantTrendMonitorDataLoader().load_data()

# Render the active section
has_data = df_aurin_main is not None and not df_aurin_main.empty

if has_data:
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
        st.info(
            "👈 Please configure your Dimensions API key using the sidebar, "
            "then click **Refresh Data** to load the dashboard."
        )
    else:
        st.info(
            "No data in cache yet. Open **Configure** in the sidebar and click "
            "**🔄 Refresh Data** to fetch from the API."
        )
