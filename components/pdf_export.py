"""PDF export utilities for the AURIN Impact Tracking Dashboard."""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from fpdf import FPDF

_UNICODE_REPLACEMENTS = str.maketrans({
    "\u2018": "'", "\u2019": "'",   # curly single quotes
    "\u201c": '"', "\u201d": '"',   # curly double quotes
    "\u2013": "-", "\u2014": "--",  # en-dash, em-dash
    "\u2026": "...",                # ellipsis
    "\u00b7": "*",                  # middle dot
    "\u2022": "*",                  # bullet
    "\u00a0": " ",                  # non-breaking space
})


def _safe(text: str) -> str:
    """Sanitize text to Latin-1 safe characters for Helvetica."""
    text = text.translate(_UNICODE_REPLACEMENTS)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _PDF(FPDF):
    _subtitle: str = ""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 9, "AURIN Impact Tracking Dashboard", border=0, align="C")
        self.ln()
        if self._subtitle:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(31, 119, 180)
            self.cell(0, 6, self._subtitle, border=0, align="C")
            self.ln()
            self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Generated {date.today().strftime('%d %B %Y')}", border=0, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_draw_color(31, 119, 180)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y() + 2, self.w - self.r_margin, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f"AURIN Impact Tracking  |  Page {self.page_no()}", align="C")


def _new_pdf(subtitle: str) -> _PDF:
    pdf = _PDF()
    pdf._subtitle = subtitle
    pdf.set_margins(15, 22, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    return pdf


def _section_title(pdf: _PDF, text: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 119, 180)
    pdf.cell(0, 7, _safe(text), border=0)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(200, 210, 220)
    pdf.set_line_width(0.2)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)


def _metrics_block(pdf: _PDF, metrics: list[tuple[str, str]]) -> None:
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = usable_w / len(metrics)
    for _, value in metrics:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(240, 244, 248)
        pdf.cell(col_w, 10, _safe(str(value)), border=0, fill=True, align="C")
    pdf.ln()
    for label, _ in metrics:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(col_w, 5, _safe(label), border=0, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)


def _data_table(
    pdf: _PDF,
    df: pd.DataFrame,
    cols: list[str],
    max_rows: int = 50,
    col_widths: Optional[list[float]] = None,
) -> None:
    available = [c for c in cols if c in df.columns]
    if not available:
        available = list(df.columns[: min(5, len(df.columns))])

    subset = df[available].head(max_rows).copy()
    max_len = 40
    for col in available:
        subset[col] = (
            subset[col]
            .fillna("")
            .astype(str)
            .apply(lambda v: v[:max_len] + "..." if len(v) > max_len else v)
        )

    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    if col_widths is None:
        col_widths = [usable_w / len(available)] * len(available)

    # Header row
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(31, 119, 180)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(available, col_widths):
        pdf.cell(w, 6, _safe(col), border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(0, 0, 0)
    for i, (_, row) in enumerate(subset.iterrows()):
        if pdf.get_y() > pdf.h - 22:
            pdf.add_page()
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        for col, w in zip(available, col_widths):
            pdf.cell(w, 5, _safe(str(row[col])), border=1, fill=fill)
        pdf.ln()
    pdf.ln(4)


def _date_range_label(from_date: Optional[str], to_date: Optional[str]) -> str:
    if from_date and to_date:
        return f"Date range: {from_date} to {to_date}"
    if from_date:
        return f"From: {from_date}"
    if to_date:
        return f"To: {to_date}"
    return "Date range: All time"


def _caption(pdf: _PDF, from_date: Optional[str], to_date: Optional[str]) -> None:
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, _safe(_date_range_label(from_date, to_date)), border=0)
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)


# ── Per-tab generators ─────────────────────────────────────────────────────────

def generate_research_papers_pdf(
    df_main: pd.DataFrame,
    df_affiliations: Optional[pd.DataFrame],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> bytes:
    pdf = _new_pdf("Research Papers")
    _caption(pdf, from_date, to_date)

    total_pubs = len(df_main)
    total_citations = int(df_main["times_cited"].sum()) if "times_cited" in df_main.columns else 0
    n_orgs = (
        df_affiliations["aff_name"].nunique()
        if df_affiliations is not None and not df_affiliations.empty and "aff_name" in df_affiliations.columns
        else 0
    )
    n_countries = (
        df_affiliations["aff_country"].nunique()
        if df_affiliations is not None and not df_affiliations.empty and "aff_country" in df_affiliations.columns
        else 0
    )

    _section_title(pdf, "Key Metrics")
    _metrics_block(pdf, [
        ("Total Publications", f"{total_pubs:,}"),
        ("Total Citations", f"{total_citations:,}"),
        ("Affiliated Organisations", str(n_orgs)),
        ("Affiliated Countries", str(n_countries)),
    ])

    if not df_main.empty and "times_cited" in df_main.columns:
        _section_title(pdf, "Top 10 Most Cited Articles")
        top = df_main.nlargest(10, "times_cited")[["title", "times_cited", "journal.title", "date"]].copy()
        top.columns = ["Title", "Citations", "Journal", "Date"]
        _data_table(pdf, top, list(top.columns), col_widths=[80, 18, 55, 27])

    if not df_main.empty and "date" in df_main.columns:
        _section_title(pdf, "Recent Publications (last 20)")
        recent = df_main.sort_values("date", ascending=False).head(20)[
            ["title", "journal.title", "date", "times_cited"]
        ].copy()
        recent.columns = ["Title", "Journal", "Date", "Citations"]
        _data_table(pdf, recent, list(recent.columns), col_widths=[80, 55, 27, 18])

    return bytes(pdf.output())


def generate_research_organisations_pdf(
    df_affiliations: Optional[pd.DataFrame],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> bytes:
    pdf = _new_pdf("Research Organisations")
    _caption(pdf, from_date, to_date)

    if df_affiliations is None or df_affiliations.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No affiliation data available.")
        pdf.ln()
        return bytes(pdf.output())

    n_orgs = df_affiliations["aff_name"].nunique() if "aff_name" in df_affiliations.columns else 0
    n_countries = df_affiliations["aff_country"].nunique() if "aff_country" in df_affiliations.columns else 0

    _section_title(pdf, "Key Metrics")
    _metrics_block(pdf, [
        ("Affiliated Organisations", str(n_orgs)),
        ("Affiliated Countries", str(n_countries)),
    ])

    if "aff_name" in df_affiliations.columns:
        _section_title(pdf, "Top Affiliated Organisations")
        top_orgs = df_affiliations["aff_name"].value_counts().head(30).reset_index()
        top_orgs.columns = ["Organisation", "Publication Count"]
        _data_table(pdf, top_orgs, list(top_orgs.columns), col_widths=[145, 35])

    if "aff_country" in df_affiliations.columns:
        _section_title(pdf, "Top Affiliated Countries")
        top_countries = df_affiliations["aff_country"].value_counts().head(20).reset_index()
        top_countries.columns = ["Country", "Count"]
        _data_table(pdf, top_countries, list(top_countries.columns), col_widths=[145, 35])

    return bytes(pdf.output())


def generate_policy_documents_pdf(
    df_policies: Optional[pd.DataFrame],
    df_web_policies: Optional[pd.DataFrame],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> bytes:
    pdf = _new_pdf("Policy Documents")
    _caption(pdf, from_date, to_date)

    parts = []
    col_map_db = {
        "title": "Title", "year": "Year",
        "publisher_org.name": "Publisher", "publisher_org.country_name": "Country",
    }
    col_map_web = {
        "title": "Title", "year": "Year",
        "publisher_name": "Publisher", "publisher_country": "Country",
    }

    if df_policies is not None and not df_policies.empty:
        avail = {k: v for k, v in col_map_db.items() if k in df_policies.columns}
        part = df_policies[list(avail.keys())].rename(columns=avail).copy()
        part["Source"] = "Dimensions"
        parts.append(part)

    if df_web_policies is not None and not df_web_policies.empty:
        avail = {k: v for k, v in col_map_web.items() if k in df_web_policies.columns}
        part = df_web_policies[list(avail.keys())].rename(columns=avail).copy()
        part["Source"] = "Web"
        parts.append(part)

    if not parts:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No policy documents available.")
        pdf.ln()
        return bytes(pdf.output())

    combined = pd.concat(parts, ignore_index=True)
    if "Title" in combined.columns:
        combined = combined.drop_duplicates(subset=["Title"], keep="first")

    total = len(combined)
    n_countries = combined["Country"].nunique() if "Country" in combined.columns else 0
    n_publishers = combined["Publisher"].nunique() if "Publisher" in combined.columns else 0

    _section_title(pdf, "Key Metrics")
    _metrics_block(pdf, [
        ("Policy Documents", str(total)),
        ("Countries", str(n_countries)),
        ("Publishers", str(n_publishers)),
    ])

    _section_title(pdf, "Policy Documents List")
    display_cols = [c for c in ["Title", "Year", "Publisher", "Country", "Source"] if c in combined.columns]
    _data_table(pdf, combined[display_cols], display_cols, max_rows=200, col_widths=[72, 15, 48, 25, 20])

    return bytes(pdf.output())


def generate_patents_pdf(
    df_patents: Optional[pd.DataFrame],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> bytes:
    pdf = _new_pdf("Patents")
    _caption(pdf, from_date, to_date)

    if df_patents is None or df_patents.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No patent data available.")
        pdf.ln()
        return bytes(pdf.output())

    _section_title(pdf, "Key Metrics")
    _metrics_block(pdf, [("Total Patents", str(len(df_patents)))])

    _section_title(pdf, "Patents")
    _data_table(pdf, df_patents, list(df_patents.columns[:6]), max_rows=100)

    return bytes(pdf.output())


def generate_grants_pdf(
    df_grants: Optional[pd.DataFrame],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> bytes:
    pdf = _new_pdf("AURIN Fundings & Grants")
    _caption(pdf, from_date, to_date)

    if df_grants is None or df_grants.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No grants data available.")
        pdf.ln()
        return bytes(pdf.output())

    _section_title(pdf, "Key Metrics")
    _metrics_block(pdf, [("Total Grants", str(len(df_grants)))])

    _section_title(pdf, "Grants & Fundings")
    _data_table(pdf, df_grants, list(df_grants.columns[:6]), max_rows=100)

    return bytes(pdf.output())


def generate_research_trend_pdf() -> bytes:
    from data.database import AurinDatabase
    df_trend = AurinDatabase().read_table("research_trend_exploded")

    pdf = _new_pdf("Research Trend Monitor")
    _caption(pdf, None, None)

    if df_trend.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No trend monitor data available.")
        pdf.ln()
        return bytes(pdf.output())

    _section_title(pdf, "Research Trends by FOR Division")
    _data_table(pdf, df_trend, ["pub_id", "year", "for_name", "for_division"], max_rows=100)

    return bytes(pdf.output())


def generate_grant_trend_pdf(
    df_grant_trend: Optional[pd.DataFrame],
) -> bytes:
    pdf = _new_pdf("Grant Trend Monitor")
    _caption(pdf, None, None)

    if df_grant_trend is None or df_grant_trend.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "No grant trend data available.")
        pdf.ln()
        return bytes(pdf.output())

    _section_title(pdf, "Grant Trends")
    _data_table(pdf, df_grant_trend, list(df_grant_trend.columns[:6]), max_rows=100)

    return bytes(pdf.output())
