"""
SDG categories component for displaying Sustainable Development Goals breakdown.
"""
from components.base_component import BaseComponent
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import re


# Official SDG metadata: number → (short title, hex color)
SDG_META = {
    1:  ("No Poverty",                              "#E5243B"),
    2:  ("Zero Hunger",                             "#DDA63A"),
    3:  ("Good Health\n& Well-being",               "#4C9F38"),
    4:  ("Quality Education",                        "#C5192D"),
    5:  ("Gender Equality",                          "#FF3A21"),
    6:  ("Clean Water\n& Sanitation",               "#26BDE2"),
    7:  ("Affordable &\nClean Energy",              "#FCC30B"),
    8:  ("Decent Work &\nEconomic Growth",          "#A21942"),
    9:  ("Industry,\nInnovation &\nInfrastructure", "#FD6925"),
    10: ("Reduced\nInequalities",                   "#DD1367"),
    11: ("Sustainable Cities\n& Communities",       "#FD9D24"),
    12: ("Responsible\nConsumption &\nProduction",  "#BF8B2E"),
    13: ("Climate Action",                           "#3F7E44"),
    14: ("Life Below Water",                         "#0A97D9"),
    15: ("Life on Land",                             "#56C02B"),
    16: ("Peace, Justice &\nStrong Institutions",   "#00689D"),
    17: ("Partnerships\nfor the Goals",             "#19486A"),
}


def _extract_sdg_number(name: str) -> Optional[int]:
    """Extract SDG number from strings like '3 Good Health...', 'SDG 3', 'SDG3: ...'."""
    # Match leading number, e.g. "3 Good Health and Well Being"
    m = re.match(r'^(\d{1,2})\b', name.strip())
    if not m:
        # Fall back to "SDG 3" / "SDG3" prefix style
        m = re.search(r'(?:SDG\s*)(\d{1,2})', name, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 17 else None
    return None


class SDGCategoriesComponent(BaseComponent):
    """Component for displaying paper counts by Sustainable Development Goal (SDG) category."""

    def __init__(self, data: Optional[pd.DataFrame] = None, **kwargs):
        super().__init__(data=data, **kwargs)

    def _parse_categories(self) -> dict:
        """Return dict mapping SDG number → paper count."""
        if 'category_sdg' not in self.data.columns:
            return {}

        df = self.data[['id', 'category_sdg']].dropna(subset=['category_sdg'])
        if df.empty:
            return {}

        counts: dict[int, int] = {}
        for _, row in df.iterrows():
            cats = row['category_sdg']
            if not isinstance(cats, list):
                continue
            for cat in cats:
                if isinstance(cat, dict):
                    # Try id first (e.g. "SDG 3"), then name
                    raw = cat.get('name', '')
                elif isinstance(cat, str):
                    raw = cat
                else:
                    continue
                n = _extract_sdg_number(raw)
                if n:
                    counts[n] = counts.get(n, 0) + 1

        return counts

    def render(self) -> None:
        """Render the SDG infographic."""
        if not self.validate_data():
            st.info("No SDG category data available.")
            return

        counts = self._parse_categories()

        st.markdown(
            '<div class="section-header">🌱 Sustainable Development Goals (SDG)</div>',
            unsafe_allow_html=True,
        )

        # Build HTML tile grid
        tiles_html = []
        for n in range(1, 18):
            title, color = SDG_META[n]
            count = counts.get(n, 0)
            title_html = title.replace('\n', '<br>')

            if count > 0:
                opacity = "1.0"
                badge = f'<div class="sdg-badge">{count}</div>'
            else:
                opacity = "0.35"
                badge = ""

            tile = f"""
            <div class="sdg-tile" style="background:{color};opacity:{opacity};" title="SDG {n}: {title.replace(chr(10), ' ')} — {count} papers">
                <div class="sdg-num">{n}</div>
                <div class="sdg-title">{title_html}</div>
                {badge}
            </div>"""
            tiles_html.append(tile)

        html = f"""
        <style>
        .sdg-grid {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
            margin: 12px 0 20px 0;
        }}
        @media (max-width: 800px) {{
            .sdg-grid {{ grid-template-columns: repeat(4, 1fr); }}
        }}
        .sdg-tile {{
            position: relative;
            border-radius: 6px;
            padding: 10px 8px 8px 8px;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            cursor: default;
            transition: transform 0.15s, box-shadow 0.15s;
        }}
        .sdg-tile:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            z-index: 2;
        }}
        .sdg-num {{
            font-size: 1.3rem;
            font-weight: 800;
            color: rgba(255,255,255,0.9);
            line-height: 1;
        }}
        .sdg-title {{
            font-size: 0.62rem;
            font-weight: 600;
            color: rgba(255,255,255,0.92);
            margin-top: 4px;
            line-height: 1.3;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }}
        .sdg-badge {{
            position: absolute;
            bottom: 6px;
            right: 7px;
            background: rgba(255,255,255,0.25);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 700;
            border-radius: 10px;
            padding: 1px 6px;
            line-height: 1.5;
        }}
        </style>
        <div class="sdg-grid">
            {''.join(tiles_html)}
        </div>
        <p style="font-size:0.75rem;color:#888;margin-top:-10px;">
            Tiles show paper counts. Dimmed tiles = no matching papers in current selection.
        </p>
        """

        st.html(html)

        # Bar chart in expander
        active = {n: c for n, c in counts.items() if c > 0}
        if active:
            chart_df = pd.DataFrame([
                {'SDG': f"SDG {n}: {SDG_META[n][0].replace(chr(10), ' ')}", 'Papers': c}
                for n, c in sorted(active.items())
            ])
            with st.expander(f"View breakdown ({len(active)} SDGs)"):
                fig = px.bar(
                    chart_df,
                    x='Papers',
                    y='SDG',
                    orientation='h',
                    color='Papers',
                    color_continuous_scale='Greens',
                )
                fig.update_layout(
                    height=max(300, len(active) * 32),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                )
                st.plotly_chart(fig, width='stretch')
