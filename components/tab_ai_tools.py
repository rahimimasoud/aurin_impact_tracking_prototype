"""
Shared AI tools rendered at the top of each dashboard tab.

Provides:
  - render_tab_ai_tools():  two-column layout (AI Summary + Q&A)
  - render_qa_only():       Q&A only (for tabs that already have a summary)
  - Context builder functions for each tab
"""
import datetime
import re
from typing import Optional

import pandas as pd
import streamlit as st
from openai import OpenAI

# ── Per-tab summary prompts ───────────────────────────────────────────────────

_SUMMARY_PROMPT_RESEARCH_PAPERS = """\
You are a research impact analyst for AURIN (Australian Urban Research \
Infrastructure Network). Based on the research papers data below, provide \
exactly 4 strategic bullets covering:

1. **Output scale** — total publications, citation volume, and date range
2. **Research focus** — top Fields of Research and SDG coverage
3. **Geographic reach** — key contributing countries and organisations
4. **Trends** — notable growth or shifts in publication activity

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

_SUMMARY_PROMPT_RESEARCH_ORGANISATIONS = """\
You are a research analyst for AURIN. Based on the research organisations \
data below, provide exactly 3 strategic bullets covering:

1. **Partnership breadth** — number of organisations and countries represented
2. **Top contributors** — leading organisations by publication count
3. **International reach** — key international collaboration countries

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

_SUMMARY_PROMPT_POLICY_DOCUMENTS = """\
You are a research impact analyst for AURIN. Based on the policy documents \
data below, provide exactly 3 strategic bullets covering:

1. **Policy reach** — total documents and unique publishers
2. **Geographic impact** — top countries citing AURIN research in policy
3. **Key publishers** — most active policy-publishing organisations

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

_SUMMARY_PROMPT_MEDIA_MONITOR = """\
You are a communications analyst for AURIN. Based on the media coverage \
data below, provide exactly 3 strategic bullets covering:

1. **Coverage volume** — total mentions, unique sources, and date range
2. **Top media outlets** — most active sources covering AURIN
3. **Coverage trends** — notable patterns or spikes over time

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

_SUMMARY_PROMPT_RESEARCH_TREND = """\
You are a research strategist for AURIN. Based on the research trend data \
below, provide exactly 4 strategic bullets covering:

1. **Fastest-growing fields** — top FOR fields by momentum score
2. **Volume leaders** — fields with the highest absolute publication counts
3. **Emerging areas** — fields showing the strongest recent acceleration
4. **Strategic opportunities** — fields AURIN should prioritise based on growth

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

_SUMMARY_PROMPT_GRANT_TREND = """\
You are a research funding strategist for AURIN. Based on the grant trend \
data below, provide exactly 4 strategic bullets covering:

1. **Fastest-growing grant fields** — top FOR fields by momentum score
2. **Volume leaders** — fields with the highest absolute grant counts
3. **Emerging funding areas** — fields showing the strongest recent acceleration
4. **Strategic priorities** — fields AURIN should target for new funding

Write each bullet in one or two sentences. Start each with the bold label.
Use only bold (**label**) for labels — no italic text.

DATA:
{context}"""

# Shared Q&A prompt
_QA_PROMPT = """\
You are an expert research analyst for AURIN (Australian Urban Research \
Infrastructure Network). Based on the following {tab_label} data, answer \
the question concisely and specifically. If the data does not contain enough \
information to answer, say so clearly.

DATA:
{context}

Question: {question}"""


# ── LLM helper ────────────────────────────────────────────────────────────────

def _llm_call(api_key: str, prompt: str) -> str:
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[{"role": "user", "content": prompt}],
        timeout=60,
    )
    content = response.choices[0].message.content
    content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', content)
    content = re.sub(r'`([^`\n]+)`', r'\1', content)
    content = content.replace('$', r'\$')
    return content


# ── Render functions ──────────────────────────────────────────────────────────

def render_tab_ai_tools(
    tab_name: str,
    tab_label: str,
    context_text: str,
    api_key: Optional[str],
    summary_prompt: str,
    summary_button_label: str = "Generate Summary",
    summary_spinner: str = "Generating summary...",
) -> None:
    """Render two-column AI section: Summary (left) + Q&A (right)."""
    col_summary, col_qa = st.columns(2)
    with col_summary:
        st.subheader("🤖 AI Summary")
        if not api_key:
            st.info("Enter your OpenRouter API key in Configure to enable AI features.")
        else:
            if st.button(summary_button_label, type="primary", key=f"sum_btn_{tab_name}"):
                with st.spinner(summary_spinner):
                    try:
                        result = _llm_call(api_key, summary_prompt.format(context=context_text))
                        st.session_state[f"sum_{tab_name}"] = result
                    except Exception as e:
                        st.error(f"Summary generation failed: {e}")
            if f"sum_{tab_name}" in st.session_state:
                st.markdown(st.session_state[f"sum_{tab_name}"])

    with col_qa:
        _render_qa_col(tab_name, tab_label, context_text, api_key)

    st.divider()


def render_qa_only(
    tab_name: str,
    tab_label: str,
    context_text: str,
    api_key: Optional[str],
    *,
    divider: bool = True,
) -> None:
    """Render Q&A section only (for tabs that already have their own summary)."""
    _render_qa_col(tab_name, tab_label, context_text, api_key)
    if divider:
        st.divider()


def _render_qa_col(
    tab_name: str,
    tab_label: str,
    context_text: str,
    api_key: Optional[str],
) -> None:
    st.subheader("🙋 Ask a Question")
    if not api_key:
        st.info("Enter your OpenRouter API key in Configure to enable AI Q&A.")
        return
    question = st.text_input(
        "Ask about this data:",
        key=f"qa_q_{tab_name}",
        placeholder="e.g. What are the top research fields?",
    )
    if st.button("Ask", key=f"qa_btn_{tab_name}") and question:
        with st.spinner("Thinking..."):
            try:
                answer = _llm_call(
                    api_key,
                    _QA_PROMPT.format(
                        tab_label=tab_label,
                        context=context_text,
                        question=question,
                    ),
                )
                st.session_state[f"qa_{tab_name}"] = answer
            except Exception as e:
                st.error(f"Q&A failed: {e}")
    if f"qa_{tab_name}" in st.session_state:
        st.markdown(st.session_state[f"qa_{tab_name}"])


# ── Context builders ──────────────────────────────────────────────────────────

def build_research_papers_context(
    df_main: Optional[pd.DataFrame],
    df_affiliations: Optional[pd.DataFrame] = None,
) -> str:
    if df_main is None or df_main.empty:
        return "No research papers data available."

    # Normalise citation column — components use 'times_cited'
    cit_col = "times_cited" if "times_cited" in df_main.columns else (
        "citation_count" if "citation_count" in df_main.columns else None
    )

    lines = [f"TOTAL PUBLICATIONS: {len(df_main)}"]

    if cit_col:
        total_cit = int(df_main[cit_col].sum())
        avg_cit = df_main[cit_col].mean()
        lines.append(f"TOTAL CITATIONS: {total_cit}")
        lines.append(f"AVERAGE CITATIONS PER PAPER: {avg_cit:.1f}")

    # Year range + yearly papers & citations (mirrors TrendsComponent)
    date_col = "date" if "date" in df_main.columns else ("year" if "year" in df_main.columns else None)
    if date_col:
        df_yr = df_main.copy()
        if date_col == "date":
            df_yr["_year"] = pd.to_datetime(df_yr["date"], errors="coerce").dt.year
        else:
            df_yr["_year"] = pd.to_numeric(df_yr["year"], errors="coerce")
        df_yr = df_yr.dropna(subset=["_year"])
        df_yr["_year"] = df_yr["_year"].astype(int)
        df_yr = df_yr[df_yr["_year"] >= 2009]

        if not df_yr.empty:
            lines.append(f"YEAR RANGE: {df_yr['_year'].min()} – {df_yr['_year'].max()}")

        yearly_papers = df_yr.groupby("_year").size().sort_index()
        if cit_col:
            yearly_cit = df_yr.groupby("_year")[cit_col].sum().sort_index()
        lines.append("\nYEARLY TRENDS (papers | citations):")
        for yr in yearly_papers.index:
            n_papers = yearly_papers.get(yr, 0)
            n_cit = int(yearly_cit.get(yr, 0)) if cit_col else "n/a"
            lines.append(f"  {yr}: {n_papers} papers | {n_cit} citations")

    # Top cited papers (mirrors TopCitedArticlesComponent)
    if cit_col and "title" in df_main.columns:
        top_cited = df_main.nlargest(10, cit_col)[["title", cit_col, "date"]].copy() \
            if "date" in df_main.columns else df_main.nlargest(10, cit_col)[["title", cit_col]].copy()
        lines.append("\nTOP CITED PAPERS:")
        for _, row in top_cited.iterrows():
            yr = ""
            if "date" in row.index and pd.notna(row.get("date")):
                try:
                    yr = f" ({pd.to_datetime(row['date']).year})"
                except Exception:
                    pass
            title = str(row["title"])[:100]
            lines.append(f"  \"{title}\"{yr} — {int(row[cit_col])} citations")

    # Recent papers (mirrors RecentPapersComponent)
    if "title" in df_main.columns and "date" in df_main.columns:
        df_recent = df_main.copy()
        df_recent["_date"] = pd.to_datetime(df_recent["date"], errors="coerce")
        recent = df_recent.dropna(subset=["_date"]).nlargest(5, "_date")
        lines.append("\nMOST RECENT PAPERS:")
        for _, row in recent.iterrows():
            journal = f" — {row['journal.title']}" if "journal.title" in row.index and pd.notna(row.get("journal.title")) else ""
            cit = f" | {int(row[cit_col])} citations" if cit_col else ""
            lines.append(f"  \"{str(row['title'])[:80]}\" ({row['_date'].strftime('%Y-%m-%d')}){journal}{cit}")

    # Fields of Research (mirrors ResearchCategoriesComponent)
    if "category_for" in df_main.columns:
        for_counts: dict = {}
        for val in df_main["category_for"]:
            if not isinstance(val, list):
                continue
            for item in val:
                name = item.get("name", "") if isinstance(item, dict) else str(item)
                if name:
                    for_counts[name] = for_counts.get(name, 0) + 1
        if for_counts:
            lines.append("\nTOP FIELDS OF RESEARCH (FOR):")
            for name, cnt in sorted(for_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {name}: {cnt} papers")

    # SDG categories (mirrors SDGCategoriesComponent)
    if "category_sdg" in df_main.columns:
        sdg_counts: dict = {}
        for val in df_main["category_sdg"]:
            if not isinstance(val, list):
                continue
            for item in val:
                name = item.get("name", "") if isinstance(item, dict) else str(item)
                if name:
                    sdg_counts[name] = sdg_counts.get(name, 0) + 1
        if sdg_counts:
            lines.append("\nSDG COVERAGE:")
            for name, cnt in sorted(sdg_counts.items(), key=lambda x: x[1], reverse=True)[:8]:
                lines.append(f"  {name}: {cnt} papers")

    # Top concepts (mirrors ConceptsComponent)
    if "concepts" in df_main.columns:
        concept_counts: dict = {}
        for val in df_main["concepts"]:
            if not isinstance(val, list):
                continue
            for item in val:
                name = (item.get("concept") or item.get("name") or item.get("id", "")) \
                    if isinstance(item, dict) else str(item)
                if name:
                    concept_counts[name] = concept_counts.get(name, 0) + 1
        if concept_counts:
            lines.append("\nTOP RESEARCH CONCEPTS:")
            for name, cnt in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
                lines.append(f"  {name}: {cnt} papers")

    # Affiliated organisations & countries (mirrors KeyMetricsComponent)
    if df_affiliations is not None and not df_affiliations.empty:
        if "aff_name" in df_affiliations.columns:
            lines.append(f"\nAFFILIATED ORGANISATIONS: {df_affiliations['aff_name'].nunique()} unique")
            lines.append("TOP CONTRIBUTING ORGANISATIONS:")
            for org, cnt in df_affiliations["aff_name"].value_counts().head(10).items():
                if org:
                    lines.append(f"  {org}: {cnt}")
        if "aff_country" in df_affiliations.columns:
            lines.append(f"\nAFFILIATED COUNTRIES: {df_affiliations['aff_country'].nunique()} unique")
            lines.append("TOP COUNTRIES:")
            for country, cnt in df_affiliations["aff_country"].value_counts().head(10).items():
                if country:
                    lines.append(f"  {country}: {cnt} affiliations")

    return "\n".join(lines)


def build_research_organisations_context(
    df_main: Optional[pd.DataFrame],
    df_affiliations: Optional[pd.DataFrame],
) -> str:
    if df_affiliations is None or df_affiliations.empty:
        return "No research organisations data available."

    lines = []

    has_name = "aff_name" in df_affiliations.columns
    has_country = "aff_country" in df_affiliations.columns
    has_researcher = "researcher_id" in df_affiliations.columns
    has_cited = "times_cited" in df_affiliations.columns
    has_pub = "pub_id" in df_affiliations.columns

    if has_name:
        lines.append(f"UNIQUE ORGANISATIONS: {df_affiliations['aff_name'].nunique()}")
    if has_country:
        lines.append(f"COUNTRIES REPRESENTED: {df_affiliations['aff_country'].nunique()}")

    # Replicate AffiliatedOrganisationsComponent aggregation:
    # group by org + country, count unique researchers, sum citations
    if has_name and has_country:
        grp_cols = ["aff_name", "aff_country"]
        agg = {"researcher_id": "nunique"} if has_researcher else {}
        if agg:
            org_metrics = df_affiliations.groupby(grp_cols).agg(agg).reset_index()
            org_metrics.columns = ["aff_name", "aff_country", "researcher_count"]
        else:
            org_metrics = df_affiliations.groupby(grp_cols).size().reset_index(name="researcher_count")

        if has_cited and has_pub:
            unique_pubs = df_affiliations.groupby(grp_cols + ["pub_id"])["times_cited"].first().reset_index()
            org_cit = unique_pubs.groupby(grp_cols)["times_cited"].sum().reset_index()
            org_cit.columns = ["aff_name", "aff_country", "total_citations"]
            org_metrics = org_metrics.merge(org_cit, on=grp_cols, how="left").fillna(0)
            org_metrics["avg_citations"] = (
                org_metrics["total_citations"] / org_metrics["researcher_count"].replace(0, 1)
            ).round(1)

        org_metrics = org_metrics.sort_values("researcher_count", ascending=False)
        lines.append(f"\nAVG RESEARCHERS PER ORG: {org_metrics['researcher_count'].mean():.1f}")
        if org_metrics.shape[0]:
            lines.append(f"TOP CONTRIBUTING ORG: {org_metrics.iloc[0]['aff_name']}")

        lines.append("\nTOP ORGANISATIONS (by unique researchers):")
        for _, row in org_metrics.head(20).iterrows():
            cit_str = ""
            if "total_citations" in org_metrics.columns:
                cit_str = f" | {int(row['total_citations'])} citations | avg {row['avg_citations']}"
            lines.append(
                f"  {row['aff_name']} ({row['aff_country']}): "
                f"{int(row['researcher_count'])} researchers{cit_str}"
            )

    # Individual researchers (mirrors expandable researcher lists in the component)
    has_names = "first_name" in df_affiliations.columns and "last_name" in df_affiliations.columns
    if has_researcher and has_names:
        researcher_pubs = (
            df_affiliations[df_affiliations["researcher_id"].notna() & (df_affiliations["researcher_id"] != "")]
            ["researcher_id"].value_counts()
        )
        # Build name lookup
        name_lookup = (
            df_affiliations.dropna(subset=["researcher_id"])
            .drop_duplicates(subset=["researcher_id"])
            .set_index("researcher_id")[["first_name", "last_name"]]
        )
        lines.append("\nTOP RESEARCHERS BY PUBLICATION COUNT:")
        for rid, pub_count in researcher_pubs.head(20).items():
            if rid in name_lookup.index:
                fn = name_lookup.at[rid, "first_name"] or ""
                ln = name_lookup.at[rid, "last_name"] or ""
                org = ""
                if has_name:
                    row = df_affiliations[df_affiliations["researcher_id"] == rid].iloc[0]
                    org = f" ({row['aff_name']})" if pd.notna(row.get("aff_name")) else ""
                lines.append(f"  {fn} {ln}{org}: {pub_count} publications")

        # Top researchers by citations
        if has_cited and has_pub:
            researcher_cit = (
                df_affiliations[df_affiliations["researcher_id"].notna()]
                .drop_duplicates(subset=["researcher_id", "pub_id"])
                .groupby("researcher_id")["times_cited"].sum()
                .sort_values(ascending=False)
            )
            lines.append("\nTOP RESEARCHERS BY TOTAL CITATIONS:")
            for rid, total_cit in researcher_cit.head(20).items():
                if rid in name_lookup.index:
                    fn = name_lookup.at[rid, "first_name"] or ""
                    ln = name_lookup.at[rid, "last_name"] or ""
                    lines.append(f"  {fn} {ln}: {int(total_cit)} citations")

    # Country distribution (mirrors AffiliatedCountriesComponent)
    if has_country:
        country_counts = (
            df_affiliations[df_affiliations["aff_country"].notna() & (df_affiliations["aff_country"] != "")]
            ["aff_country"].value_counts()
        )
        lines.append("\nCOUNTRIES (affiliation appearances):")
        for country, cnt in country_counts.head(15).items():
            lines.append(f"  {country}: {cnt}")

    return "\n".join(lines)


def build_policy_documents_context(
    df_policies: Optional[pd.DataFrame],
    df_web: Optional[pd.DataFrame] = None,
) -> str:
    def _normalise(df: pd.DataFrame, source_label: str) -> pd.DataFrame:
        df = df.copy()
        df["Source"] = source_label
        for src in ("publisher_org.name", "publisher_name"):
            if src in df.columns and "Publisher" not in df.columns:
                df = df.rename(columns={src: "Publisher"})
        for src in ("publisher_org.country_name", "publisher_country"):
            if src in df.columns and "Country" not in df.columns:
                df = df.rename(columns={src: "Country"})
        if "title" in df.columns:
            df = df.rename(columns={"title": "Title"})
        if "year" in df.columns:
            df = df.rename(columns={"year": "Year"})
        return df

    parts = []
    if df_policies is not None and not df_policies.empty:
        parts.append(_normalise(df_policies, "Dimensions"))
    if df_web is not None and not df_web.empty:
        parts.append(_normalise(df_web, "Web"))
    if not parts:
        return "No policy documents data available."

    combined = pd.concat(parts, ignore_index=True)

    # Deduplicate on normalised title (mirrors PolicyDocumentsComponent)
    if "Title" in combined.columns:
        combined["_key"] = combined["Title"].str.lower().str.strip()
        combined = combined.drop_duplicates(subset=["_key"]).drop(columns=["_key"])

    lines = [f"TOTAL POLICY DOCUMENTS: {len(combined)}"]

    if "Source" in combined.columns:
        src_counts = combined["Source"].value_counts()
        for src, cnt in src_counts.items():
            lines.append(f"  — {src}: {cnt}")

    if "Country" in combined.columns:
        lines.append(f"COUNTRIES: {combined['Country'].nunique()} unique")
    if "Publisher" in combined.columns:
        lines.append(f"PUBLISHERS: {combined['Publisher'].nunique()} unique")

    if "Year" in combined.columns:
        years = pd.to_numeric(combined["Year"], errors="coerce").dropna()
        if not years.empty:
            lines.append(f"YEAR RANGE: {int(years.min())} – {int(years.max())}")

    if "Publisher" in combined.columns:
        lines.append("\nTOP PUBLISHERS:")
        for pub, cnt in combined["Publisher"].value_counts().head(12).items():
            if pub:
                lines.append(f"  {pub}: {cnt} documents")

    if "Country" in combined.columns:
        lines.append("\nTOP COUNTRIES:")
        for country, cnt in combined["Country"].value_counts().head(10).items():
            if country:
                lines.append(f"  {country}: {cnt} documents")

    # Recent documents (mirrors table sorted by Year desc)
    if "Title" in combined.columns:
        recent = combined.dropna(subset=["Title"])
        if "Year" in combined.columns:
            recent = recent.sort_values("Year", ascending=False, na_position="last")
        lines.append("\nRECENT POLICY DOCUMENTS:")
        for _, row in recent.head(10).iterrows():
            yr = f" ({int(row['Year'])})" if "Year" in row.index and pd.notna(row.get("Year")) else ""
            pub = f" — {row['Publisher']}" if "Publisher" in row.index and pd.notna(row.get("Publisher")) else ""
            country = f" [{row['Country']}]" if "Country" in row.index and pd.notna(row.get("Country")) else ""
            lines.append(f"  \"{str(row['Title'])[:100]}\"{yr}{pub}{country}")

    return "\n".join(lines)


def build_media_monitor_context(df: Optional[pd.DataFrame]) -> str:
    if df is None or df.empty:
        return "No media mentions data available."

    lines = [f"TOTAL MENTIONS: {len(df)}"]

    if "source" in df.columns:
        lines.append(f"UNIQUE SOURCES: {df['source'].nunique()}")

    # Date range (mirrors _render_summary)
    if "published_at" in df.columns and df["published_at"].notna().any():
        earliest = df["published_at"].min()
        latest = df["published_at"].max()
        lines.append(
            f"DATE RANGE: {earliest.strftime('%d %b %Y')} – {latest.strftime('%d %b %Y')}"
        )

    # Search terms coverage (mirrors table filter options)
    if "search_term" in df.columns:
        term_counts = df["search_term"].value_counts()
        if not term_counts.empty:
            lines.append("\nSEARCH TERMS (mentions per term):")
            for term, cnt in term_counts.items():
                if term:
                    lines.append(f"  \"{term}\": {cnt} mentions")

    # Top 15 sources (mirrors _render_source_breakdown)
    if "source" in df.columns:
        top_sources = (
            df["source"].replace("", pd.NA).dropna().value_counts().head(15)
        )
        lines.append("\nTOP MEDIA SOURCES:")
        for src, cnt in top_sources.items():
            lines.append(f"  {src}: {cnt} mentions")

    # Quarterly timeline (mirrors _render_timeline)
    if "published_at" in df.columns and df["published_at"].notna().any():
        df_dated = df.dropna(subset=["published_at"]).copy()
        df_dated["quarter"] = df_dated["published_at"].dt.to_period("Q").astype(str)
        quarterly = df_dated.groupby("quarter").size().sort_index()
        if not quarterly.empty:
            lines.append("\nMENTIONS BY QUARTER:")
            for q, n in quarterly.items():
                lines.append(f"  {q}: {n} mentions")

    # Recent article titles + snippets (mirrors mentions table, sorted by date desc)
    title_col = "title" if "title" in df.columns else None
    snippet_col = "snippet" if "snippet" in df.columns else None
    if title_col and "published_at" in df.columns:
        recent = (
            df.dropna(subset=["published_at"])
            .sort_values("published_at", ascending=False)
            .head(15)
        )
        lines.append("\nRECENT ARTICLES (title | source | snippet):")
        for _, row in recent.iterrows():
            date_str = row["published_at"].strftime("%d %b %Y") if pd.notna(row.get("published_at")) else ""
            src = f" [{row['source']}]" if "source" in row.index and pd.notna(row.get("source")) else ""
            title = str(row[title_col])[:100]
            snippet = f" — {str(row[snippet_col])[:120]}" if snippet_col and pd.notna(row.get(snippet_col)) else ""
            lines.append(f"  {date_str}{src}: {title}{snippet}")

    return "\n".join(lines)


def build_research_trend_context(df: Optional[pd.DataFrame]) -> str:
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return "No research trend data available."
    try:
        from components.research_trend._helpers import explode_with_year, compute_momentum
        df_exploded = explode_with_year(df)
        if df_exploded.empty:
            return "No FOR classification data found in research trend dataset."
        now = datetime.datetime.now().year
        momentum_df = compute_momentum(df_exploded, now - 4, now - 8, now - 5)
        lines = [
            "RESEARCH TREND MONITOR",
            f"Current window: {now - 4}–{now - 1} | Prior window: {now - 8}–{now - 5}",
            f"TOTAL FIELDS TRACKED: {len(momentum_df)}",
            "\nTOP FIELDS BY MOMENTUM (fastest growing):",
        ]
        for _, row in momentum_df.head(10).iterrows():
            sign = "+" if row["momentum_pct"] >= 0 else ""
            lines.append(
                f"  {row['display_name']}: {sign}{row['momentum_pct']:.0f}% "
                f"({row['current_count']} current, {row['prior_count']} prior)"
            )
        lines.append("\nLARGEST BY CURRENT VOLUME:")
        for _, row in momentum_df.sort_values("current_count", ascending=False).head(8).iterrows():
            lines.append(f"  {row['display_name']}: {row['current_count']} publications")
        return "\n".join(lines)
    except Exception:
        return f"Research trend data: {len(df)} records available."


def build_grant_trend_context(df: Optional[pd.DataFrame]) -> str:
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return "No grant trend data available."
    try:
        from components.grant_trend._helpers import explode_with_year, compute_momentum
        df_exploded = explode_with_year(df)
        if df_exploded.empty:
            return "No FOR classification data found in grant trend dataset."
        now = datetime.datetime.now().year
        momentum_df = compute_momentum(df_exploded, now - 4, now - 8, now - 5)
        lines = [
            "GRANT TREND MONITOR",
            f"Current window: {now - 4}–{now - 1} | Prior window: {now - 8}–{now - 5}",
            f"TOTAL FIELDS TRACKED: {len(momentum_df)}",
            "\nTOP FIELDS BY MOMENTUM (fastest growing):",
        ]
        for _, row in momentum_df.head(10).iterrows():
            sign = "+" if row["momentum_pct"] >= 0 else ""
            lines.append(
                f"  {row['display_name']}: {sign}{row['momentum_pct']:.0f}% "
                f"({row['current_count']} current, {row['prior_count']} prior)"
            )
        lines.append("\nLARGEST BY CURRENT VOLUME:")
        for _, row in momentum_df.sort_values("current_count", ascending=False).head(8).iterrows():
            lines.append(f"  {row['display_name']}: {row['current_count']} grants")
        if "funder_org_name" in df_exploded.columns:
            top_funders = df_exploded["funder_org_name"].value_counts().head(8)
            if not top_funders.empty:
                lines.append("\nTOP FUNDERS:")
                for funder, cnt in top_funders.items():
                    if funder:
                        lines.append(f"  {funder}: {cnt} grants")
        return "\n".join(lines)
    except Exception:
        return f"Grant trend data: {len(df)} records available."
