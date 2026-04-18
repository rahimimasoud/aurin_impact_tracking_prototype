"""
AURIN Web Policy Agent

Searches the open web for policy documents mentioning AURIN, extracts relevant
text, summarises each mention with AI, and stores results in the local
SQLite database (web_policy_documents table).

Usage:
    uv run python "data/AI agents/aurin_policy_agent.py" \
        [--openrouter-key KEY] \
        [--search-engine {serpapi,duckduckgo}] \
        [--serpapi-key KEY]

Reads OPENROUTER_API_KEY and SERPAPI_KEY from .env if not passed directly.
Default search engine: SerpAPI when SERPAPI_KEY is set, else DuckDuckGo.
"""
import argparse
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

# Allow importing from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.database import AurinDatabase
from components.search_engine import SearchProvider, get_provider

load_dotenv()

QUERIES = [
    '"AURIN" site:gov.au filetype:pdf',
    '"Australian Urban Research Infrastructure Network" site:gov.au filetype:pdf',
    '"Australian Urban Research Infrastructure Network" site:gov.au filetype:docx',
    '"AURIN" "NCRIS" policy report filetype:pdf',
    '"Australian Urban Research Infrastructure Network" policy filetype:pdf',
    '"AURIN" research infrastructure strategy filetype:pdf',
]

_OR_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_OR_MODEL = "google/gemini-2.5-flash" #"nvidia/nemotron-3-super-120b-a12b:free"
_SNIPPET_WINDOW = 150   # chars on each side of an AURIN mention
_MAX_SNIPPETS = 5       # max snippets sent to the model per document
_PREAMBLE_CHARS = 600   # chars from document opening sent as document-type context
_MAX_RESULTS = 100      # DuckDuckGo results per query
_QUERY_SLEEP = 2        # seconds between DuckDuckGo queries
_OR_RETRIES = 3
_OR_SLEEP = 1           # seconds between OpenRouter calls


# ── Text fetching ────────────────────────────────────────────────────────────

# def _url_is_pdf(url: str) -> bool:
#     return urlparse(url).path.lower().endswith(".pdf")


def _response_is_pdf(response: requests.Response) -> bool:
    return "pdf" in response.headers.get("Content-Type", "").lower()


def fetch_pdf_text(url: str) -> str | None:
    try:
        import pdfplumber
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        if not (_response_is_pdf(resp)):
            print(f"  [skip] not a PDF (Content-Type): {url}")
            return None
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages)
    except Exception as exc:
        print(f"  [skip] fetch error for {url}: {exc}")
        return None


# ── Snippet extraction ───────────────────────────────────────────────────────

def extract_snippets(text: str) -> list[str]:
    snippets = []
    seen = set()
    for m in re.finditer(r"aurin", text, re.IGNORECASE):
        start = max(0, m.start() - _SNIPPET_WINDOW)
        end = min(len(text), m.end() + _SNIPPET_WINDOW)
        snippet = text[start:end].strip()
        key = snippet[:80]
        if key not in seen:
            seen.add(key)
            snippets.append(snippet)
    return snippets


# ── OpenRouter call ──────────────────────────────────────────────────────────

def call_openrouter(url: str, snippets: list[str], api_key: str, raw_title: str = "", preamble: str = "") -> dict:
    snippet_block = "\n".join(f"- {s}" for s in snippets)
    preamble_section = f"Document opening (first ~{_PREAMBLE_CHARS} chars):\n{preamble}\n\n" if preamble else ""
    prompt = (
        "You are analysing a document that mentions AURIN "
        "(Australian Urban Research Infrastructure Network).\n\n"
        f"URL: {url}\n\n"
        f"{preamble_section}"
        f"Snippets around AURIN mentions:\n{snippet_block}\n\n"
        "Respond ONLY with a valid JSON object (no markdown fences) with these keys:\n"
        '- "is_policy": true if this document is a policy document, government report, '
        "parliament submission, or strategy; false if it is an academic paper, preprint, "
        "thesis, dataset page, news article, or commercial content\n"
        '- "title": a clear, human-readable title for this document; improve the '
        f'original title if it is a filename, URL fragment, or otherwise unclear '
        f'(original: "{raw_title or url.split("/")[-1]}")'
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _OR_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(1, _OR_RETRIES + 1):
        try:
            resp = requests.post(_OR_BASE_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            return json.loads(raw)
        except Exception as exc:
            print(f"  [openrouter] attempt {attempt}/{_OR_RETRIES} failed: {exc}")
            if attempt < _OR_RETRIES:
                time.sleep(2)

    return {"is_policy": False, "title": ""}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_year(text: str) -> int | None:
    m = re.search(r"\b(20[0-9]{2}|19[0-9]{2})\b", text)
    return int(m.group()) if m else None


def _publisher_from_url(url: str) -> tuple[str, str]:
    host = urlparse(url).netloc.lower().lstrip("www.")
    country = "Australia" if host.endswith(".au") else ""
    return host, country


def _existing_urls(db: AurinDatabase) -> set[str]:
    df = db.read_table("web_policy_documents", columns=["url"])
    if df.empty or "url" not in df.columns:
        return set()
    return set(df["url"].tolist())


# ── Persistence ──────────────────────────────────────────────────────────────

def save_to_db(
    db: AurinDatabase,
    url: str,
    title: str,
    text: str,
    query: str,
) -> None:
    publisher_name, publisher_country = _publisher_from_url(url)
    year = _extract_year(text)
    row = {
        "url": url,
        "title": title,
        "year": year,
        "linkout": url,
        "publisher_name": publisher_name,
        "publisher_country": publisher_country,
        "source_query": query,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    df = pd.DataFrame([row])
    db.upsert_dataframe(df, "web_policy_documents", id_column="url")
    print(f"  [saved] {url}")


# ── Main ─────────────────────────────────────────────────────────────────────

def run(api_key: str, search_provider: SearchProvider | None = None) -> None:
    provider = search_provider or get_provider()

    db = AurinDatabase()
    existing = _existing_urls(db)
    print(f"[agent] {len(existing)} URLs already in DB — will skip duplicates.\n")

    total_saved = 0

    for i, query in enumerate(QUERIES):
        print(f"[query {i+1}/{len(QUERIES)}] {query}")
        try:
            results = provider.search(query, max_results=_MAX_RESULTS)
        except RuntimeError as exc:
            print(f"  [skip] search provider error: {exc}")
            results = []

        for r in results:
            url = r.href
            if url in existing:
                print(f"  [dup]  {url}")
                continue

            if "aurin.org.au" in urlparse(url).netloc.lower():
                print(f"  [skip] aurin.org.au (own site): {url}")
                continue

            print(f"  [fetch] {url}")
            text = fetch_pdf_text(url)
            if not text:
                continue

            snippets = extract_snippets(text)
            if not snippets:
                print(f"  [skip] no AURIN mentions in {url}")
                continue

            print(f"  [found] {len(snippets)} mention(s) — calling AI…")
            raw_title = r.title
            preamble = text[:_PREAMBLE_CHARS].strip()
            ai = call_openrouter(url, snippets[:_MAX_SNIPPETS], api_key, raw_title, preamble)
            if not ai.get("is_policy", True):
                print("  [skip] AI: not a policy document")
                continue
            save_to_db(db, url, ai.get("title") or raw_title, text, query)
            existing.add(url)
            total_saved += 1
            time.sleep(_OR_SLEEP)

        if i < len(QUERIES) - 1:
            time.sleep(_QUERY_SLEEP)

    print(f"\n[agent] done. {total_saved} new document(s) saved to web_policy_documents.")


def main() -> None:
    parser = argparse.ArgumentParser(description="AURIN Web Policy Agent")
    parser.add_argument("--openrouter-key", default=None, help="OpenRouter API key (overrides .env)")
    parser.add_argument(
        "--search-engine",
        choices=["serpapi", "duckduckgo"],
        default=None,
        dest="search_engine",
        help="Search engine to use. Default: auto-detect (SerpAPI if SERPAPI_KEY is set, else DuckDuckGo).",
    )
    parser.add_argument("--serpapi-key", default=None, help="SerpAPI key (overrides SERPAPI_KEY env var)")
    args = parser.parse_args()

    api_key = args.openrouter_key or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        sys.exit("Error: OpenRouter API key not found. Set OPENROUTER_API_KEY in .env or pass --openrouter-key.")

    provider = get_provider(prefer=args.search_engine, serpapi_key=args.serpapi_key)
    print(f"[agent] using search provider: {type(provider).__name__}")
    if not provider.is_available():
        sys.exit(
            f"Error: {type(provider).__name__} is not available. "
            "Check that the required key or package is present."
        )

    run(api_key, search_provider=provider)


if __name__ == "__main__":
    main()
