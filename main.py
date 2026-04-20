"""
Main Streamlit application for AURIN Impact Tracking Dashboard.
This file orchestrates all components and data loading.
"""
import streamlit as st

from components._constants import _ENV_DIMENSIONS, _ENV_OPENROUTER
from data_loader import DimensionsDataLoader, PolicyDocumentsDataLoader, GrantsDataLoader, PatentsDataLoader, ResearchTrendMonitorDataLoader, GrantTrendMonitorDataLoader, WebPolicyDocumentsDataLoader, FundingSignalDataLoader
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
from components.media_monitor import MediaMonitorComponent
from components.ai_summary import AISummaryComponent
from components.ai_providers.openrouter_provider import OpenRouterProvider
from components.funding_signal import FundingSignalMonitorComponent
from components.tab_ai_tools import (
    render_tab_ai_tools,
    build_research_papers_context,
    build_research_organisations_context,
    build_policy_documents_context,
    build_research_trend_context,
    build_grant_trend_context,
    _SUMMARY_PROMPT_RESEARCH_PAPERS,
    _SUMMARY_PROMPT_RESEARCH_ORGANISATIONS,
    _SUMMARY_PROMPT_POLICY_DOCUMENTS,
    _SUMMARY_PROMPT_RESEARCH_TREND,
    _SUMMARY_PROMPT_GRANT_TREND,
)
from components.pdf_export import (
    generate_research_papers_pdf,
    generate_research_organisations_pdf,
    generate_policy_documents_pdf,
    generate_patents_pdf,
    generate_grants_pdf,
    generate_research_trend_pdf,
    generate_grant_trend_pdf,
)

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
st.session_state.api_key = _ENV_DIMENSIONS if _ENV_DIMENSIONS else None
st.session_state.openrouter_api_key = _ENV_OPENROUTER if _ENV_OPENROUTER else None

# Sidebar: navigation + config
sidebar.render()

# Header: title
header.render()

# Retrieve credentials and active tab
api_key = sidebar.get_api_key()
openrouter_api_key = sidebar.get_openrouter_api_key()
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
        capture = DataCapture(api_key, from_date_str, to_date_str, openrouter_api_key=openrouter_api_key)
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
df_web_policies = WebPolicyDocumentsDataLoader().load_data()
df_patents = PatentsDataLoader().load_data(from_date=from_date_str, to_date=to_date_str)
df_grants = GrantsDataLoader().load_data(from_date=from_date_str, to_date=to_date_str)
def _export_btn(label: str, pdf_bytes: bytes, filename: str) -> None:
    """Render a PDF download button aligned to the right of the page."""
    _, col = st.columns([5, 1])
    with col:
        st.download_button(
            label=label,
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )


# Media Monitor tab: works independently of Dimensions data
if active_tab == "media_monitor":
    MediaMonitorComponent(openrouter_api_key=openrouter_api_key).render()
    st.stop()

# Render the active section
has_data = df_aurin_main is not None and not df_aurin_main.empty

if has_data:
    if active_tab == "ai_summary":
        # No structured data to export — AI summary is generated text
        AISummaryComponent(
            main_data=df_aurin_main,
            affiliations_data=df_affiliations,
            policies_data=df_policies,
            patents_data=df_patents,
            grants_data=df_grants,
            date_from=from_date_str,
            date_to=to_date_str,
            provider=OpenRouterProvider(api_key=openrouter_api_key),
        ).render()

    elif active_tab == "research_papers":
        _export_btn(
            "📄 Export PDF",
            generate_research_papers_pdf(df_aurin_main, df_affiliations, from_date_str, to_date_str),
            "research_papers.pdf",
        )
        render_tab_ai_tools(
            "research_papers", "Research Papers",
            build_research_papers_context(df_aurin_main, df_affiliations),
            openrouter_api_key,
            _SUMMARY_PROMPT_RESEARCH_PAPERS,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising research papers...",
        )
        KeyMetricsComponent(main_data=df_aurin_main, affiliations_data=df_affiliations).render()
        TrendsComponent(data=df_aurin_main).render()
        TopCitedArticlesComponent(data=df_aurin_main).render()
        RecentPapersComponent(data=df_aurin_main).render()
        ResearchCategoriesComponent(data=df_aurin_main).render()
        SDGCategoriesComponent(data=df_aurin_main).render()
        ConceptsComponent(data=df_aurin_main).render()

    elif active_tab == "research_organisations":
        _export_btn(
            "📄 Export PDF",
            generate_research_organisations_pdf(df_affiliations, from_date_str, to_date_str),
            "research_organisations.pdf",
        )
        render_tab_ai_tools(
            "research_organisations", "Research Organisations",
            build_research_organisations_context(df_aurin_main, df_affiliations),
            openrouter_api_key,
            _SUMMARY_PROMPT_RESEARCH_ORGANISATIONS,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising research organisations...",
        )
        AffiliatedOrganisationsComponent(main_data=df_aurin_main, affiliations_data=df_affiliations).render()
        AffiliatedCountriesComponent(affiliations_data=df_affiliations).render()

    elif active_tab == "policy_documents":
        _export_btn(
            "📄 Export PDF",
            generate_policy_documents_pdf(df_policies, df_web_policies, from_date_str, to_date_str),
            "policy_documents.pdf",
        )
        render_tab_ai_tools(
            "policy_documents", "Policy Documents",
            build_policy_documents_context(df_policies, df_web_policies),
            openrouter_api_key,
            _SUMMARY_PROMPT_POLICY_DOCUMENTS,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising policy documents...",
        )
        PolicyDocumentsComponent(data=df_policies, web_data=df_web_policies).render()

    elif active_tab == "patents":
        _export_btn(
            "📄 Export PDF",
            generate_patents_pdf(df_patents, from_date_str, to_date_str),
            "patents.pdf",
        )
        PatentsComponent(data=df_patents).render()

    elif active_tab == "aurin_fundings":
        _export_btn(
            "📄 Export PDF",
            generate_grants_pdf(df_grants, from_date_str, to_date_str),
            "aurin_fundings.pdf",
        )
        GrantsComponent(data=df_grants).render()

    elif active_tab == "research_trend_monitor":
        df_trend_monitor = ResearchTrendMonitorDataLoader().load_data()
        _export_btn(
            "📄 Export PDF",
            generate_research_trend_pdf(df_trend_monitor),
            "research_trend_monitor.pdf",
        )
        render_tab_ai_tools(
            "research_trend_monitor", "Research Trend Monitor",
            build_research_trend_context(df_trend_monitor),
            openrouter_api_key,
            _SUMMARY_PROMPT_RESEARCH_TREND,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising research trends...",
        )
        ResearchTrendMonitorComponent(publications_data=df_trend_monitor).render()

    elif active_tab == "grant_trend_monitor":
        df_grant_trend_monitor = GrantTrendMonitorDataLoader().load_data()
        _export_btn(
            "📄 Export PDF",
            generate_grant_trend_pdf(df_grant_trend_monitor),
            "grant_trend_monitor.pdf",
        )
        render_tab_ai_tools(
            "grant_trend_monitor", "Grant Trend Monitor",
            build_grant_trend_context(df_grant_trend_monitor),
            openrouter_api_key,
            _SUMMARY_PROMPT_GRANT_TREND,
            summary_button_label="Generate Summary",
            summary_spinner="Summarising grant trends...",
        )
        GrantTrendMonitorComponent(grants_data=df_grant_trend_monitor).render()

    elif active_tab == "funding_signal_monitor":
        df_fsm_trend  = FundingSignalDataLoader().load_data()
        FundingSignalMonitorComponent(
            grant_trend_data=df_fsm_trend,
            publications_data=df_aurin_main,
            openrouter_api_key=openrouter_api_key,
        ).render()

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
