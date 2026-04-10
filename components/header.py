"""
Header component for the dashboard.
"""
from components.base_component import BaseComponent
import streamlit as st


class HeaderComponent(BaseComponent):
    """Component for rendering the dashboard header."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._inject_custom_css()

    def _inject_custom_css(self) -> None:
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1f77b4;
            }
            .section-header {
                font-size: 1.5rem;
                font-weight: bold;
                color: #2c3e50;
                margin-top: 2rem;
                margin-bottom: 1rem;
            }
            /* Sidebar nav group labels */
            [data-testid="stSidebar"] .nav-group-label {
                font-size: 0.95rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: #1f77b4;
                margin: 1.5rem 0 0.4rem 0;
                padding: 0.4rem 0.5rem;
                border-left: 3px solid #1f77b4;
                background: rgba(31, 119, 180, 0.08);
                border-radius: 0 4px 4px 0;
            }
            /* Sidebar nav buttons — flat, left-aligned */
            [data-testid="stSidebar"] .stButton {
                width: 100% !important;
            }
            [data-testid="stSidebar"] .stButton > button {
                justify-content: flex-start !important;
                text-align: left !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                font-size: 0.875rem !important;
                padding: 0.3rem 0.5rem !important;
                border-radius: 4px !important;
                width: 100% !important;
                transition: background 0.15s !important;
            }
            [data-testid="stSidebar"] .stButton > button:hover {
                background: rgba(255,255,255,0.08) !important;
            }
            [data-testid="stSidebar"] .stButton > button:hover {
                background: rgba(255,255,255,0.08) !important;
            }
            /* Tab list container */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background-color: transparent;
                padding-bottom: 4px;
            }
            /* Individual tab */
            .stTabs [data-baseweb="tab"] {
                height: 44px;
                padding: 0 20px;
                border-radius: 6px 6px 0 0;
                font-size: 0.875rem;
                font-weight: 500;
                color: #8899aa;
                background-color: transparent;
                border-bottom: 3px solid transparent;
                transition: color 0.2s, border-color 0.2s, background-color 0.2s;
            }
            .stTabs [data-baseweb="tab"]:hover {
                color: #1f77b4;
                background-color: rgba(31, 119, 180, 0.08);
            }
            .stTabs [aria-selected="true"] {
                color: #1f77b4 !important;
                background-color: rgba(31, 119, 180, 0.12) !important;
                border-bottom: 3px solid #1f77b4 !important;
                font-weight: 600 !important;
            }
            .stTabs [data-baseweb="tab-highlight"] {
                display: none;
            }
            .stTabs [data-baseweb="tab-border"] {
                background-color: rgba(255,255,255,0.1);
            }
        </style>
        """, unsafe_allow_html=True)

    def render(self) -> None:
        st.markdown(
            '<h1 class="main-header">📊 AURIN Impact Tracking Dashboard</h1>',
            unsafe_allow_html=True
        )
