"""
Sidebar component: hierarchical navigation + modal config dialog.
"""
from components.base_component import BaseComponent
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()


IMPACT_METRICS_TABS = [
    ("🤖 AI Summary", "ai_summary"),
    ("📄 Research Papers", "research_papers"),
    ("🏢 Research Organisations", "research_organisations"),
    ("📋 Policy Documents", "policy_documents"),
    ("🔬 Patents", "patents"),
    ("💰 AURIN Fundings", "aurin_fundings"),
]

IMPACT_SPACE_TABS = [
    ("📈 Research Trend Monitor", "research_trend_monitor"),
    ("📊 Grant Trend Monitor", "grant_trend_monitor"),
]


@st.dialog("⚙️ Configure Dashboard")
def _show_config_dialog():
    """Modal dialog for entering API credentials and date range."""
    _env_dimensions = os.getenv('DIMENSIONS_API_KEY', '')
    _env_gemini = os.getenv('GEMINI_API_KEY', '')

    if _env_dimensions:
        st.success("✅ Dimensions API key loaded from .env")
        api_key_input = _env_dimensions
    else:
        api_key_input = st.text_input(
            "Dimensions API Key",
            type="password",
            help="Enter your Dimensions API key to access the data",
            placeholder="Enter your Dimensions API key here...",
            value=st.session_state.get('api_key_input', '')
        )

    if _env_gemini:
        st.success("✅ Gemini API key loaded from .env")
        gemini_api_key_input = _env_gemini
    else:
        gemini_api_key_input = st.text_input(
            "Gemini API Key (optional)",
            type="password",
            help="Enter your Google Gemini API key to enable AI summaries",
            placeholder="Enter your Gemini API key here...",
            value=st.session_state.get('gemini_api_key_input', '')
        )

    with st.expander("📅 Date Range Filter"):
        st.info("Filter reports by date range (optional)")
        from_date = st.date_input(
            "From Date",
            value=st.session_state.get('from_date'),
            help="Select the start date for filtering publications"
        )
        to_date = st.date_input(
            "To Date",
            value=st.session_state.get('to_date'),
            help="Select the end date for filtering publications"
        )
        if from_date and to_date and from_date > to_date:
            st.error("❌ From date must be before To date")
        else:
            st.session_state.from_date = from_date
            st.session_state.to_date = to_date

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", type="primary", width='stretch'):
            if not api_key_input:
                st.error("❌ DimensionsAPI key is required to refresh data")
            else:
                st.session_state.api_key = api_key_input
                st.session_state.api_key_input = api_key_input
                if gemini_api_key_input:
                    st.session_state.gemini_api_key = gemini_api_key_input
                    st.session_state.gemini_api_key_input = gemini_api_key_input
                st.session_state.refresh_requested = True
                st.session_state.show_config = False
                st.rerun()
    with col2:
        if st.button("🗑️ Clear", width='stretch'):
            st.session_state.api_key = None
            st.session_state.api_key_input = ""
            st.session_state.gemini_api_key = None
            st.session_state.gemini_api_key_input = ""
            st.session_state.show_config = False
            st.rerun()


class SidebarComponent(BaseComponent):
    """Sidebar with hierarchical navigation and modal configuration."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        defaults = {
            'api_key': None,
            'api_key_input': "",
            'gemini_api_key': None,
            'gemini_api_key_input': "",
            'from_date': None,
            'to_date': None,
            'active_tab': 'ai_summary',
            'show_config': False,
            'refresh_requested': False,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _nav_button(self, label: str, key: str) -> None:
        is_active = st.session_state.get('active_tab') == key
        btn_label = f"▸ {label}" if is_active else f"   {label}"
        if st.sidebar.button(btn_label, key=f"nav_{key}"):
            st.session_state.active_tab = key
            st.rerun()

    def render(self) -> None:
        st.sidebar.image(
            "https://data.aurin.org.au/assets/aurin-logo-400-D0zkc36m.png",
            width='stretch'
        )

        st.sidebar.markdown(
            '<p class="nav-group-label">📊 Impact Metrics</p>',
            unsafe_allow_html=True
        )
        for label, key in IMPACT_METRICS_TABS:
            self._nav_button(label, key)

        st.sidebar.markdown(
            '<p class="nav-group-label">🌏 Impact Space</p>',
            unsafe_allow_html=True
        )
        for label, key in IMPACT_SPACE_TABS:
            self._nav_button(label, key)

        st.sidebar.markdown("---")

        if st.sidebar.button("⚙️ Configure", width='stretch'):
            st.session_state.show_config = True

        if st.session_state.get('show_config'):
            _show_config_dialog()

        if st.session_state.get('api_key'):
            st.sidebar.success("✅ Dimensions API key active")
        if st.session_state.get('gemini_api_key'):
            st.sidebar.success("✅ Gemini API key active")

    def get_active_tab(self) -> str:
        return st.session_state.get('active_tab', 'research_papers')

    def get_api_key(self) -> str:
        return st.session_state.get('api_key')

    def get_gemini_api_key(self) -> str:
        return st.session_state.get('gemini_api_key')

    def get_date_range(self) -> tuple:
        return (
            st.session_state.get('from_date'),
            st.session_state.get('to_date')
        )
