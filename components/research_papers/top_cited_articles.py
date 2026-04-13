"""
Top cited articles component for displaying most cited publications.
"""
from components.base_component import BaseComponent
import streamlit as st
import pandas as pd


class TopCitedArticlesComponent(BaseComponent):
    """Component for displaying top cited articles."""
    
    def __init__(self, data: pd.DataFrame = None, top_n: int = 5, **kwargs):
        """
        Initialize the top cited articles component.
        
        Args:
            data: Main publications DataFrame
            top_n: Number of top articles to display
        """
        super().__init__(data=data, **kwargs)
        self.top_n = top_n
    
    def render(self) -> None:
        """Render the top cited articles component."""
        if not self.validate_data():
            st.warning("No data available to display top cited articles.")
            return
        
        st.markdown(f'<div class="section-header">🏆 Top {self.top_n} Most Cited Articles</div>', unsafe_allow_html=True)
        
        # Calculate top cited articles
        top_cited_articles = self.data.nlargest(self.top_n, 'times_cited')
        
        if not top_cited_articles.empty:
            # Create a more detailed table
            display_df = top_cited_articles[['title', 'times_cited', 'journal.title', 'date']].copy()
            display_df.columns = ['Title', 'Citations', 'Journal', 'Publication Date']
            display_df['Publication Date'] = pd.to_datetime(display_df['Publication Date']).dt.strftime('%Y-%m-%d')

            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )

            # Prepare full sorted list for download
            all_cited = self.data.sort_values('times_cited', ascending=False)
            if not all_cited.empty:
                download_df = all_cited[['title', 'times_cited', 'journal.title', 'date']].copy()
                download_df.columns = ['Title', 'Citations', 'Journal', 'Publication Date']
                download_df['Publication Date'] = pd.to_datetime(download_df['Publication Date']).dt.strftime('%Y-%m-%d')
                csv = download_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download all articles as CSV",
                    data=csv,
                    file_name="aurin_articles.csv",
                    mime="text/csv"
                )
        else:
            st.info("No cited articles found.")

