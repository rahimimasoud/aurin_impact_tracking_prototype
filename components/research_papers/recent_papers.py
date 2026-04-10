"""
Recent papers component for displaying most recent publications.
"""
from components.base_component import BaseComponent
from components.utils import get_first_author_name
import streamlit as st
import pandas as pd


class RecentPapersComponent(BaseComponent):
    """Component for displaying most recent papers."""
    
    def __init__(self, data: pd.DataFrame = None, top_n: int = 5, **kwargs):
        """
        Initialize the recent papers component.
        
        Args:
            data: Main publications DataFrame
            top_n: Number of recent papers to display
        """
        super().__init__(data=data, **kwargs)
        self.top_n = top_n
    
    def render(self) -> None:
        """Render the recent papers component."""
        if not self.validate_data():
            st.warning("No data available to display recent papers.")
            return
        
        st.markdown('<div class="section-header">📚 Top 5 Most Recent Papers Citing AURIN</div>', unsafe_allow_html=True)
        
        # Work with a copy to avoid mutating original data
        data_copy = self.data.copy()
        
        # Convert date column to datetime if not already
        if 'date' in data_copy.columns:
            data_copy['date'] = pd.to_datetime(data_copy['date'], errors='coerce')
        
        # Calculate top most recent papers
        top_recent_papers = data_copy.sort_values(by='date', ascending=False).head(self.top_n)
        
        if not top_recent_papers.empty:
            # Create base display dataframe
            recent_display_df = top_recent_papers[['title', 'date', 'journal.title', 'times_cited']].copy()
            
            # Extract first author's name from authors column if available
            if 'authors' in top_recent_papers.columns:
                # Apply function to extract author names
                author_names = top_recent_papers['authors'].apply(get_first_author_name)
                recent_display_df['first_author_name'] = author_names.apply(lambda x: x[0]+" "+x[1] if x[0] and x[1] else '')
                # Reorder columns: Title, First Author Name, Publication Date, Journal, Citations
                recent_display_df = recent_display_df[['title', 'first_author_name', 'date', 'journal.title', 'times_cited']]
                recent_display_df.columns = ['Title', 'First Author', 'Publication Date', 'Journal', 'Citations']
            else:
                recent_display_df.columns = ['Title', 'Publication Date', 'Journal', 'Citations']
            
            recent_display_df['Publication Date'] = pd.to_datetime(recent_display_df['Publication Date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                recent_display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent papers found.")

