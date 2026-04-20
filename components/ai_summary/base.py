"""
Core interfaces for AI summary generation.

Defines the data contract (ImpactContext) and the abstract provider
interface (AIProvider) that any LLM backend must implement.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import re
import pandas as pd

@dataclass
class ImpactContext:
    """Structured representation of AURIN research data for summarisation."""
    main_data: pd.DataFrame
    affiliations_data: Optional[pd.DataFrame] = None
    policies_data: Optional[pd.DataFrame] = None
    patents_data: Optional[pd.DataFrame] = None
    grants_data: Optional[pd.DataFrame] = None
    date_from: Optional[str] = None  # YYYY-MM-DD or None
    date_to: Optional[str] = None    # YYYY-MM-DD or None

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _trends_text(self) -> list[str]:
        lines = []
        if "date" not in self.main_data.columns:
            return lines
        df = self.main_data.copy()
        df["_year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
        df = df.dropna(subset=["_year"])
        df = df[df["_year"] >= 2009]
        if df.empty:
            return lines
        yearly = df.groupby("_year").size().sort_index()
        lines.append("\n## Publication Trends (from 2009)")
        for year, count in yearly.items():
            lines.append(f"  {int(year)}: {count} papers")
        if "times_cited" in df.columns:
            yearly_cit = df.groupby("_year")["times_cited"].sum().sort_index()
            lines.append("- Citations per year:")
            for year, cit in yearly_cit.items():
                lines.append(f"  {int(year)}: {int(cit)} citations")
        return lines

    def _for_categories_text(self) -> list[str]:
        lines = []
        if "category_for" not in self.main_data.columns:
            return lines
        rows = []
        for cats in self.main_data["category_for"].dropna():
            if not isinstance(cats, list):
                continue
            for cat in cats:
                if isinstance(cat, dict):
                    name = cat.get("name") or cat.get("id", "")
                elif isinstance(cat, str):
                    name = cat
                else:
                    continue
                if name:
                    rows.append(name)
        if not rows:
            return lines
        counts = pd.Series(rows).value_counts()
        lines.append("\n## Field of Research (FOR) Categories")
        lines.append(f"- Total distinct FOR categories: {len(counts)}")
        lines.append("- Top 20 categories by paper count:")
        for cat, count in counts.head(20).items():
            lines.append(f"  • {cat}: {count} papers")
        return lines

    def _sdg_categories_text(self) -> list[str]:
        _SDG_NAMES = {
            1: "No Poverty", 2: "Zero Hunger", 3: "Good Health & Well-being",
            4: "Quality Education", 5: "Gender Equality", 6: "Clean Water & Sanitation",
            7: "Affordable & Clean Energy", 8: "Decent Work & Economic Growth",
            9: "Industry, Innovation & Infrastructure", 10: "Reduced Inequalities",
            11: "Sustainable Cities & Communities", 12: "Responsible Consumption & Production",
            13: "Climate Action", 14: "Life Below Water", 15: "Life on Land",
            16: "Peace, Justice & Strong Institutions", 17: "Partnerships for the Goals",
        }
        lines = []
        if "category_sdg" not in self.main_data.columns:
            return lines
        sdg_counts: dict[int, int] = {}
        for cats in self.main_data["category_sdg"].dropna():
            if not isinstance(cats, list):
                continue
            for cat in cats:
                raw = cat.get("name", "") if isinstance(cat, dict) else (cat if isinstance(cat, str) else "")
                m = re.match(r"^(\d{1,2})\b", raw.strip()) or re.search(r"(?:SDG\s*)(\d{1,2})", raw, re.IGNORECASE)
                if m:
                    n = int(m.group(1))
                    if 1 <= n <= 17:
                        sdg_counts[n] = sdg_counts.get(n, 0) + 1
        if not sdg_counts:
            return lines
        lines.append("\n## Sustainable Development Goals (SDG)")
        lines.append(f"- SDGs covered: {len(sdg_counts)} out of 17")
        lines.append("- Paper counts per SDG:")
        for n, count in sorted(sdg_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  • SDG {n} – {_SDG_NAMES.get(n, '')}: {count} papers")
        return lines

    def _policies_text(self) -> list[str]:
        lines = []
        if self.policies_data is None or self.policies_data.empty:
            return lines
        df = self.policies_data
        lines.append("\n## Policy Documents")
        lines.append(f"- Total policy documents citing AURIN research: {len(df)}")
        if "publisher_org.country_name" in df.columns:
            lines.append(f"- Countries of publication: {df['publisher_org.country_name'].nunique()}")
            top_countries = df["publisher_org.country_name"].value_counts().head(5)
            lines.append("- Top countries:")
            for country, count in top_countries.items():
                lines.append(f"  • {country}: {count}")
        if "publisher_org.name" in df.columns:
            lines.append(f"- Distinct publishers: {df['publisher_org.name'].nunique()}")
            top_pubs = df["publisher_org.name"].value_counts().head(5)
            lines.append("- Top publishers:")
            for pub, count in top_pubs.items():
                lines.append(f"  • {pub}: {count}")
        if "year" in df.columns:
            years = df["year"].dropna()
            if not years.empty:
                lines.append(f"- Year range: {int(years.min())}–{int(years.max())}")
        return lines

    def _patents_text(self) -> list[str]:
        lines = []
        if self.patents_data is None or self.patents_data.empty:
            return lines
        df = self.patents_data
        lines.append("\n## Patents")
        lines.append(f"- Total patents citing AURIN research: {len(df)}")
        if "jurisdiction" in df.columns:
            lines.append(f"- Jurisdictions: {df['jurisdiction'].nunique()}")
            top_j = df["jurisdiction"].value_counts().head(5)
            lines.append("- Top jurisdictions:")
            for j, count in top_j.items():
                lines.append(f"  • {j}: {count}")
        assignee_col = "assignee_names" if "assignee_names" in df.columns else ("assignees" if "assignees" in df.columns else None)
        if assignee_col:
            lines.append(f"- Distinct assignees: {df[assignee_col].nunique()}")
        if "legal_status" in df.columns:
            status_counts = df["legal_status"].value_counts().head(5)
            lines.append("- Legal status breakdown:")
            for status, count in status_counts.items():
                lines.append(f"  • {status}: {count}")
        return lines

    def _grants_text(self) -> list[str]:
        lines = []
        if self.grants_data is None or self.grants_data.empty:
            return lines
        df = self.grants_data
        lines.append("\n## AURIN Fundings / Grants")
        lines.append(f"- Total grants: {len(df)}")
        if "funder_org_name" in df.columns:
            lines.append(f"- Distinct funders: {df['funder_org_name'].nunique()}")
            top_funders = df["funder_org_name"].value_counts().head(5)
            lines.append("- Top funders:")
            for funder, count in top_funders.items():
                lines.append(f"  • {funder}: {count}")
        if "funding_usd" in df.columns:
            funding_vals = pd.to_numeric(df["funding_usd"], errors="coerce").dropna()
            if not funding_vals.empty:
                lines.append(f"- Total funding (USD): ${funding_vals.sum():,.0f}")
                lines.append(f"- Average grant (USD): ${funding_vals.mean():,.0f}")
        return lines

    # ------------------------------------------------------------------ #
    # Public                                                               #
    # ------------------------------------------------------------------ #

    def to_text(self) -> str:
        """Compile key statistics from all datasets into a plain-text context block."""
        lines = ["# AURIN Research Impact Data\n"]

        # --- Reporting period ---
        if self.date_from or self.date_to:
            period_from = self.date_from or "2010"
            period_to = self.date_to or "present"
            lines.append(f"**Reporting period: {period_from} to {period_to}**\n")
        else:
            lines.append("**Reporting period: 2010 to present (full dataset)**\n")

        # --- Research Papers (core metrics) ---
        lines.append("## Research Papers")
        lines.append(f"- Total publications: {len(self.main_data)}")
        total_citations = (
            int(self.main_data["times_cited"].sum())
            if "times_cited" in self.main_data.columns
            else 0
        )
        lines.append(f"- Total citations: {total_citations:,}")

        if "date" in self.main_data.columns:
            years = pd.to_datetime(self.main_data["date"], errors="coerce").dt.year.dropna()
            if not years.empty:
                lines.append(f"- Publication years range: {int(years.min())}–{int(years.max())}")
                recent = self.main_data[
                    pd.to_datetime(self.main_data["date"], errors="coerce").dt.year >= years.max() - 2
                ]
                lines.append(f"- Publications in last 3 years: {len(recent)}")

        if "times_cited" in self.main_data.columns:
            top5 = self.main_data.nlargest(5, "times_cited")[["title", "times_cited"]]
            lines.append("- Top 5 cited papers:")
            for _, row in top5.iterrows():
                lines.append(f"  • {row['title']} ({int(row['times_cited'])} citations)")

        if "type" in self.main_data.columns:
            type_counts = self.main_data["type"].value_counts()
            lines.append("- Publication types:")
            for ptype, count in type_counts.items():
                lines.append(f"  • {ptype}: {count}")

        # --- Affiliated Organisations ---
        if self.affiliations_data is not None and not self.affiliations_data.empty:
            lines.append("\n## Research Organisations")
            if "aff_name" in self.affiliations_data.columns:
                lines.append(f"- Unique affiliated organisations: {self.affiliations_data['aff_name'].nunique()}")
                top_orgs = self.affiliations_data["aff_name"].value_counts().head(5)
                lines.append("- Top organisations by publication count:")
                for org, count in top_orgs.items():
                    lines.append(f"  • {org}: {count}")
            if "aff_country" in self.affiliations_data.columns:
                lines.append(f"- Countries represented: {self.affiliations_data['aff_country'].nunique()}")
                top_countries = self.affiliations_data["aff_country"].value_counts().head(5)
                lines.append("- Top countries:")
                for country, count in top_countries.items():
                    lines.append(f"  • {country}: {count}")

        # --- Trends ---
        lines.extend(self._trends_text())

        # --- FOR Categories ---
        lines.extend(self._for_categories_text())

        # --- SDG Categories ---
        lines.extend(self._sdg_categories_text())

        # --- Policy Documents ---
        lines.extend(self._policies_text())

        # --- Patents ---
        lines.extend(self._patents_text())

        # --- Grants ---
        lines.extend(self._grants_text())

        return "\n".join(lines)


SUMMARY_PROMPT_TEMPLATE = """\
You are a senior research impact strategist preparing a board-level executive \
summary for AURIN (Australian Urban Research Infrastructure Network).

Based on the data below, write a structured executive summary with the \
following five sections. Use a bold heading for each section followed by \
one to three sentences of substantive, insight-driven prose. Do not use \
bullet points within sections. Write in authoritative, strategic language \
appropriate for a vice-chancellor, minister, or research board.

**Research Output & Scale**
Summarise the volume and trajectory of AURIN-linked research: total \
publications, citation impact, growth trends, and the breadth of Fields of \
Research and SDGs covered.

**Organisational Reach & Collaboration**
Describe the geographic and institutional spread — number of contributing \
organisations, countries engaged, and what this signals about AURIN's \
collaborative footprint.

**Policy & Societal Impact**
Assess the translation of research into policy: number of policy documents \
citing AURIN research, key publishing bodies, and the countries where AURIN \
is shaping evidence-based decision-making.

**Funding & Research Investment**
Summarise the grant landscape: total funding secured, top funders, and \
whether funding momentum is growing or plateauing. Highlight any notable \
concentration or diversification trends.

**Strategic Observations**
Identify two or three forward-looking observations: where AURIN is \
punching above its weight, where gaps or risks exist, and what the data \
signals for AURIN's positioning over the next three to five years.

DATA:
{context}"""


class AIProvider(ABC):
    """Abstract interface every LLM backend must implement."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready to use."""

    @abstractmethod
    def generate_summary(self, context: ImpactContext) -> str:
        """
        Generate a two-paragraph impact summary from the given context.

        Returns the summary text on success, or raises RuntimeError on failure.
        """
