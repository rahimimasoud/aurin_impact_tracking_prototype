"""
Sidebar component for API key management and configuration.
"""
from components.base_component import BaseComponent
import streamlit as st
from pathlib import Path


class SidebarComponent(BaseComponent):
    """Component for managing sidebar configuration and API key."""
    
    def __init__(self, **kwargs):
        """Initialize the sidebar component."""
        super().__init__(**kwargs)
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state variables if they don't exist."""
        if 'api_key' not in st.session_state:
            st.session_state.api_key = None
        if 'api_key_input' not in st.session_state:
            st.session_state.api_key_input = ""
        if 'gemini_api_key' not in st.session_state:
            st.session_state.gemini_api_key = None
        if 'gemini_api_key_input' not in st.session_state:
            st.session_state.gemini_api_key_input = ""
        if 'from_date' not in st.session_state:
            st.session_state.from_date = None
        if 'to_date' not in st.session_state:
            st.session_state.to_date = None
    
    def _render_logo(self) -> None:
        """Render AURIN logo at the top of the sidebar."""
        logo_path = "https://data.aurin.org.au/assets/aurin-logo-400-D0zkc36m.png"
        st.sidebar.image(logo_path, use_container_width=True)
    
    def render(self) -> None:
        """Render the sidebar component."""
        # Add AURIN logo at the top
        self._render_logo()
        st.sidebar.info("This dashboard displays AURIN research impact, metrics and analytics.")
                
        st.sidebar.subheader("🔑 Enter Your Credentials")
        # Dimensions API Key input
        api_key_input = st.sidebar.text_input(
            "Dimensions API Key",
            type="password",
            help="Enter your Dimensions API key to access the data",
            placeholder="Enter your Dimensions API key here...",
            value=st.session_state.get('api_key_input', '')
        )

        # Gemini API Key input
        gemini_api_key_input = st.sidebar.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key to enable AI summaries",
            placeholder="Enter your Gemini API key here...",
            value=st.session_state.get('gemini_api_key_input', '')
        )

        with st.sidebar.expander("📅 Date Range Filter"):
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

            # Validate date range
            if from_date and to_date and from_date > to_date:
                st.error("❌ From date must be before To date")
            else:
                st.session_state.from_date = from_date
                st.session_state.to_date = to_date
        
       
        # Button row for API key actions
        with st.sidebar:
            submit_key = st.button("🔑 Submit Key", type="primary", use_container_width=True)
            clear_key = st.button("🗑️ Clear", use_container_width=True)
        
        # Handle API key submission
        if submit_key and api_key_input:
            st.session_state.api_key = api_key_input
            st.session_state.api_key_input = api_key_input
            if gemini_api_key_input:
                st.session_state.gemini_api_key = gemini_api_key_input
                st.session_state.gemini_api_key_input = gemini_api_key_input
            st.sidebar.success("✅ API key(s) submitted successfully!")
            st.rerun()
        elif submit_key and not api_key_input:
            st.sidebar.error("❌ Please enter a Dimensions API key before submitting")

        # Handle API key clearing
        if clear_key:
            st.session_state.api_key = None
            st.session_state.api_key_input = ""
            st.session_state.gemini_api_key = None
            st.session_state.gemini_api_key_input = ""
            st.sidebar.info("🗑️ API keys cleared")
            st.rerun()

        # Store input values in session state for persistence
        if api_key_input != st.session_state.get('api_key_input', ''):
            st.session_state.api_key_input = api_key_input
        if gemini_api_key_input != st.session_state.get('gemini_api_key_input', ''):
            st.session_state.gemini_api_key_input = gemini_api_key_input

        st.sidebar.markdown("---")
        # Show status
        if st.session_state.get('api_key'):
            st.sidebar.success("✅ Dimensions API key is active")
        else:
            st.sidebar.warning("⚠️ Please enter and submit your Dimensions API key to load data")
        if st.session_state.get('gemini_api_key'):
            st.sidebar.success("✅ Gemini API key is active")
    
    def get_api_key(self) -> str:
        """
        Get the current API key from session state.
        
        Returns:
            API key string or None
        """
        return st.session_state.get('api_key')
    
    def get_gemini_api_key(self) -> str:
        """
        Get the current Gemini API key from session state.

        Returns:
            Gemini API key string or None
        """
        return st.session_state.get('gemini_api_key')

    def get_date_range(self) -> tuple:
        """
        Get the current date range from session state.
        
        Returns:
            Tuple of (from_date, to_date) or (None, None) if not set
        """
        return (
            st.session_state.get('from_date'),
            st.session_state.get('to_date')
        )

