"""
Media capture module: fetches AURIN mentions from Google News RSS.

No API key required. Queries Google News for AURIN-related search terms and
stores results in the media_mentions SQLite table via AurinDatabase.
"""
import hashlib
import html
import re
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Generator, List, Optional, Tuple

import feedparser
import pandas as pd

from data.database import AurinDatabase

_SEARCH_TERMS = [
    '"AURIN" "NCRIS"',
    '"Australian Urban Research Infrastructure Network"',
    '"Australia\'s Spatial Intelligence Network"',
    'AURIN "Australia" data',
    'AURIN "Australia" research',
    'AURIN "Australia" impact',
    'AURIN "Australia" University',
]

_RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en"

# Seconds to wait between RSS requests to avoid rate-limiting.
_REQUEST_DELAY = 1.5


def _monthly_windows(start_year: int = 2010) -> Generator[Tuple[str, str], None, None]:
    """Yield (after, before) ISO date string pairs for each quarter from start_year to today."""
    today = date.today()
    cur = date(start_year, 1, 1)
    while cur <= today:
        month = cur.month + 3
        year = cur.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        nxt = date(year, month, 1)
        before = min(nxt, today + timedelta(days=1))
        yield cur.strftime("%Y-%m-%d"), before.strftime("%Y-%m-%d")
        cur = nxt


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(clean).strip()


def _url_to_id(url: str) -> str:
    """SHA256 of URL path (query params stripped) for stable cross-term deduplication."""
    path = urllib.parse.urlparse(url).path
    return hashlib.sha256(path.encode()).hexdigest()


def _parse_date(date_str: str) -> str:
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


class MediaCaptureError(Exception):
    """Raised when media capture fails with a user-actionable message."""


class MediaCapture:
    """
    Fetches AURIN mentions from Google News RSS and persists them to SQLite.

    Queries each search term across monthly windows from 2010 to today to work
    around Google News RSS's ~10-result limit per query.

    Usage::

        capture = MediaCapture()
        new_count = capture.capture_all(db, progress_callback=lambda f, lbl: print(f, lbl))
    """

    def capture_all(
        self,
        db: AurinDatabase,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> int:
        """
        Fetch all search terms across monthly date windows and upsert into media_mentions.
        Returns the total row count stored after the operation.
        """
        if progress_callback is None:
            progress_callback = lambda f, l: None

        windows = list(_monthly_windows())
        total_steps = len(_SEARCH_TERMS) * len(windows)
        step = 0
        all_rows: List[dict] = []

        progress_callback(0.0, f"Starting media capture — {total_steps} queries across {len(windows)} quarters…")

        for term in _SEARCH_TERMS:
            for after, before in windows:
                progress_callback(step / total_steps, f"[{after[:7]}] {term}…")
                try:
                    rows = self._fetch_term(term, after=after, before=before)
                    all_rows.extend(rows)
                    unique_so_far = len({r["id"] for r in all_rows})
                    if rows:
                        print(f"[media] {after[:7]} '{term}': {len(rows)} new  |  {unique_so_far} total captured")
                except Exception as e:
                    print(f"[media] {after[:7]} '{term}' failed: {e}")
                step += 1
                time.sleep(_REQUEST_DELAY)

        if not all_rows:
            progress_callback(1.0, "No new media mentions found.")
            return 0

        df = pd.DataFrame(all_rows).drop_duplicates(subset="id")
        db.upsert_dataframe(df, "media_mentions", id_column="id")
        total = len(db.read_table("media_mentions"))
        db.record_fetch("media_mentions", "", "", total)

        progress_callback(1.0, f"Media capture complete — {total} total mentions stored.")
        return total

    def _fetch_term(self, term: str, after: str = "", before: str = "") -> List[dict]:
        query_str = term
        if after:
            query_str += f" after:{after}"
        if before:
            query_str += f" before:{before}"

        url = _RSS_BASE.format(query=urllib.parse.quote(query_str))
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            # XML parse errors mean Google returned an HTML error/empty page — no data for this window.
            # Only re-raise for real network/connection failures.
            exc = feed.bozo_exception
            if not hasattr(exc, "getLineNumber"):
                raise MediaCaptureError(f"RSS fetch error: {exc}")
            return []

        fetched_at = datetime.now(timezone.utc).isoformat()
        rows = []
        for entry in feed.entries:
            link = getattr(entry, "link", "") or ""
            source_obj = getattr(entry, "source", None)
            rows.append({
                "id": _url_to_id(link),
                "title": getattr(entry, "title", "") or "",
                "url": link,
                "source": getattr(source_obj, "title", "") or "" if source_obj else "",
                "published_at": _parse_date(getattr(entry, "published", "") or ""),
                "snippet": _strip_html(getattr(entry, "summary", "") or ""),
                "search_term": term,
                "fetched_at": fetched_at,
            })
        return rows
