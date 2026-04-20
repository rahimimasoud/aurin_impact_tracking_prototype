"""
CLI entry point for AURIN data capture.

Usage:
    uv run capture [options]
    python cli.py [options]

Examples:
    uv run cli.py                                          # capture all sources
    uv run cli.py --source dimensions --api-key <KEY>
    uv run cli.py --source media
    uv run cli.py --source policies --openrouter-key <KEY>
    uv run cli.py --source research_trend --api-key <KEY>
    uv run cli.py --source grant_trend --api-key <KEY>
    uv run cli.py --source all --from-date 2020-01-01 --to-date 2024-12-31
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from data import AurinDatabase, DataCapture, CaptureError, MediaCapture, MediaCaptureError


def _load_policy_agent():
    agent_path = Path(__file__).parent / "data" / "AI agents" / "aurin_policy_agent.py"
    spec = importlib.util.spec_from_file_location("aurin_policy_agent", agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _progress(fraction: float, label: str) -> None:
    pct = int(fraction * 100)
    print(f"[{pct:3d}%] {label}", flush=True)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="capture",
        description="Fetch AURIN data and store it in the local SQLite cache.",
    )
    parser.add_argument(
        "-s", "--source",
        choices=["all", "dimensions", "media", "policies", "research_trend", "grant_trend"],
        default="all",
        help=(
            "Data source to capture: 'dimensions' (publications + policy docs + trends), "
            "'media', 'policies', 'research_trend', 'grant_trend', or 'all' (default: all)"
        ),
    )
    parser.add_argument(
        "-k", "--api-key",
        default=os.getenv("DIMENSIONS_API_KEY", ""),
        help="Dimensions API key (defaults to DIMENSIONS_API_KEY env var); required for 'dimensions' and 'all'",
    )
    parser.add_argument(
        "--openrouter-key",
        default=os.getenv("OPENROUTER_API_KEY", ""),
        help="OpenRouter API key (defaults to OPENROUTER_API_KEY env var); required for 'policies' and 'all'",
    )
    parser.add_argument(
        "--search-engine",
        choices=["serpapi", "duckduckgo"],
        default="serpapi",
        dest="search_engine",
        help="Search engine for policy capture (default: auto-detect based on available keys)",
    )
    parser.add_argument(
        "--serpapi-key",
        default=os.getenv("SERPAPI_KEY", ""),
        help="SerpAPI key (defaults to SERPAPI_KEY env var)",
    )
    parser.add_argument(
        "-f", "--from-date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Only include Dimensions records on or after this date (optional)",
    )
    parser.add_argument(
        "-t", "--to-date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Only include Dimensions records on or before this date (optional)",
    )
    parser.add_argument(
        "-e", "--endpoint",
        default="https://app.dimensions.ai",
        help="Dimensions API endpoint URL",
    )

    args = parser.parse_args()

    needs_dimensions = args.source in ("dimensions", "all")
    needs_policies = args.source in ("policies", "all")
    needs_trend = args.source in ("research_trend", "grant_trend", "dimensions", "all")

    if needs_trend and not args.api_key:
        parser.error(
            "No API key supplied for Dimensions. Pass --api-key or set the DIMENSIONS_API_KEY environment variable."
        )
    if needs_policies and not args.openrouter_key:
        parser.error(
            "No API key supplied for OpenRouter. Pass --openrouter-key or set the OPENROUTER_API_KEY environment variable."
        )

    db = AurinDatabase()

    if needs_dimensions:
        capture = DataCapture(
            api_key=args.api_key,
            from_date=args.from_date,
            to_date=args.to_date,
            endpoint=args.endpoint,
            openrouter_api_key=args.openrouter_key or None,
        )
        try:
            capture.capture_all(db, progress_callback=_progress)
            _progress(1.0, "Dimensions capture complete.")
        except CaptureError as e:
            print(f"ERROR (dimensions): {e}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"UNEXPECTED ERROR (dimensions): {e}", file=sys.stderr)
            sys.exit(3)

    if args.source in ("research_trend", "grant_trend"):
        import dimcli as _dimcli
        _dimcli.login(key=args.api_key, endpoint=args.endpoint)
        _dsl = _dimcli.Dsl()
        capture = DataCapture(
            api_key=args.api_key,
            from_date=args.from_date,
            to_date=args.to_date,
            endpoint=args.endpoint,
        )
        try:
            if args.source == "research_trend":
                capture._capture_research_trend(db, _dsl, _progress)
                _progress(1.0, "Research trend capture complete.")
            else:
                capture._capture_grant_trend(db, _dsl, _progress)
                _progress(1.0, "Grant trend capture complete.")
        except Exception as e:
            print(f"UNEXPECTED ERROR ({args.source}): {e}", file=sys.stderr)
            sys.exit(3)

    if args.source in ("media", "all"):
        media_capture = MediaCapture()
        try:
            total = media_capture.capture_all(db, progress_callback=_progress)
            _progress(1.0, f"Media capture complete — {total} total mentions stored.")
        except MediaCaptureError as e:
            print(f"ERROR (media): {e}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"UNEXPECTED ERROR (media): {e}", file=sys.stderr)
            sys.exit(3)

    if needs_policies:
        agent = _load_policy_agent()
        provider = agent.get_provider(prefer=args.search_engine, serpapi_key=args.serpapi_key or None)
        print(f"[policies] using search provider: {type(provider).__name__}")
        if not provider.is_available():
            print(f"ERROR (policies): {type(provider).__name__} is not available.", file=sys.stderr)
            sys.exit(2)
        try:
            agent.run(args.openrouter_key, search_provider=provider)
        except Exception as e:
            print(f"UNEXPECTED ERROR (policies): {e}", file=sys.stderr)
            sys.exit(3)


if __name__ == "__main__":
    main()
