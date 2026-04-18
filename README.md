# AURIN Impact Tracking Dashboard

A Streamlit-based dashboard for tracking and visualizing the research impact of the Australian Urban Research Infrastructure Network (AURIN) using data from the Dimensions API.

## Overview

This dashboard provides comprehensive insights into AURIN's research publications, including:
- Key metrics and statistics
- Top cited articles
- Affiliated organisations and countries
- Recent publications
- Publication trends over time
- Citation distribution

## Features

- **Key Metrics**: Overview of total publications, citations, and collaboration statistics
- **Top Cited Articles**: Display of the most impactful publications
- **Affiliated Organisations**: Visualization of research collaborations
- **Affiliated Countries**: Geographic distribution of research partnerships
- **Recent Papers**: Latest publications from the last 6 months
- **Publication Trends**: Time-based analysis of research output
- **Interactive Visualizations**: Dynamic charts and graphs powered by Plotly

## Requirements

- Python 3.8 or higher
- Dimensions API key (required for data access)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/aurin_impact_tracking_prototype.git
cd aurin_impact_tracking_prototype
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run main.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically `http://localhost:8501`)

3. Enter your Dimensions API key in the sidebar

4. The dashboard will automatically load and display the AURIN research impact data

## Project Structure

```
aurin_impact_tracking_prototype/
├── main.py                    # Main Streamlit application entry point
├── data_loader.py             # Data loading module for Dimensions API
├── requirements.txt           # Python dependencies
├── components/                # Dashboard components
│   ├── __init__.py
│   ├── base_component.py     # Base class for all components
│   ├── header.py             # Dashboard header component
│   ├── sidebar.py            # Sidebar with API key input
│   ├── key_metrics.py        # Key metrics display
│   ├── top_cited_articles.py # Top cited articles component
│   ├── affiliated_organisations.py # Organisation affiliations
│   ├── affiliated_countries.py    # Country affiliations
│   ├── recent_papers.py      # Recent publications component
│   ├── papers_last_6_months.py # 6-month publication trends
│   ├── citation_distribution.py # Citation distribution visualization
│   └── utils.py              # Utility functions
└── assets/                   # Static assets (if any)
```

## Configuration

### Dimensions API Key

You'll need a valid Dimensions API key to access the data. The API key can be entered directly in the dashboard sidebar when running the application.

For more information about obtaining a Dimensions API key, visit: https://www.dimensions.ai/

### Customizing the Query

The default query searches for publications containing "Australian Urban Research Infrastructure Network". You can modify the query in `data_loader.py` to customize the search criteria.

## Dependencies

- `streamlit` - Web framework for the dashboard
- `requests` - HTTP library for API calls
- `dimcli` - Dimensions API client library
- `pandas` - Data manipulation and analysis
- `plotly` - Interactive visualizations
- `numpy` - Numerical computing
- `pycountry` - Country data for geographic visualizations

## License

This project is a prototype. Please check with AURIN for licensing and usage terms.

## Contributing

This is a prototype project. For contributions or suggestions, please open an issue or contact the project maintainers.

## Acknowledgments

- AURIN (Australian Urban Research Infrastructure Network)
- Dimensions API for research data access

