"""
Streamlit UI component for the AI Summary tab.

Accepts all dashboard DataFrames, uses an AIProvider to generate the
summary on demand, and renders the result.
"""
from typing import Optional
import streamlit as st
import pandas as pd

from components.base_component import BaseComponent
from components.ai_summary.base import AIProvider, ImpactContext
from components.ai_providers.openrouter_provider import OpenRouterProvider


class AISummaryComponent(BaseComponent):
    """Streamlit component that renders the AI-generated impact summary tab."""

    def __init__(
        self,
        main_data: Optional[pd.DataFrame] = None,
        affiliations_data: Optional[pd.DataFrame] = None,
        policies_data: Optional[pd.DataFrame] = None,
        patents_data: Optional[pd.DataFrame] = None,
        grants_data: Optional[pd.DataFrame] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[AIProvider] = None,
        **kwargs,
    ):
        super().__init__(data=main_data, **kwargs)
        self.affiliations_data = affiliations_data
        self.policies_data = policies_data
        self.patents_data = patents_data
        self.grants_data = grants_data
        self.date_from = date_from
        self.date_to = date_to
        self.provider: AIProvider = provider or OpenRouterProvider()

    def render(self) -> None:
        st.markdown("## AI-Generated Impact Summary")
        st.caption(f"Powered by {type(self.provider).__name__.replace('Provider', '')}")

        if not self.validate_data():
            st.warning("No research data available to summarise.")
            return

        if not self.provider.is_available():
            st.warning(
                "AI provider is not configured. "
                "Enter your Gemini API key in the sidebar to enable AI summaries."
            )
            return
        
        if st.button("Generate Impact Summary", type="primary"):
            context = ImpactContext(
                main_data=self.data,
                affiliations_data=self.affiliations_data,
                policies_data=self.policies_data,
                patents_data=self.patents_data,
                grants_data=self.grants_data,
                date_from=self.date_from,
                date_to=self.date_to,
            )
            with st.spinner("Analysing research data..."):
                try:
                    summary = self.provider.generate_summary(context)
                    st.markdown(summary)
                except RuntimeError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
