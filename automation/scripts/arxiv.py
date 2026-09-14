#!/usr/bin/env python3
"""Tier 1 retrieval: query the arXiv API for recent submissions.

arXiv is the only compulsory source with a real API, so it is the one source
whose daily coverage can actually be guaranteed rather than hoped for. Everything
here is stdlib (urllib + xml.etree), so no install step is needed.

Usage:
    arxiv.py --since 48h                       # categories from topics.toml
    arxiv.py --since 7d --category cs.CR
    arxiv.py --since 48h --json

Output is one candidate per line: ID <tab> published <tab> title <tab> URL.

Rate limiting: arXiv asks for a 3 second delay between consecutive calls, which
this enforces between pages. Their index only refreshes once a day, so running
this more than daily gains nothing.
https://info.arxiv.org/help/api/user-manual.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
PAGE_SIZE = 200
RATE_LIMIT_SECONDS = 3
CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config" / "topics.toml"


def load_config() -> dict:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)


def parse_since(s: str) -> dt.timedelta:
    m = re.fullmatch(r"(\d+)\s*([hd])", s.strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(f"--since must look like '48h' or '7d', got {s!r}")
    n, unit = int(m.group(1)), m.group(2)
    return dt.timedelta(hours=n) if unit == "h" else dt.timedelta(days=n)


def arxiv_categories(cfg: dict) -> list[str]:
    for src in cfg.get("sources", []):
        if src.get("retrieval") == "api" and src.get("name", "").lower() == "arxiv":
            return list(src.get("categories", []))
    return []


def build_query(categories: list[str], start: dt.datetime, end: dt.datetime) -> str:
    """arXiv wants submittedDate as [YYYYMMDDHHMM TO YYYYMMDDHHMM] in GMT."""
    cats = " OR ".join(f"cat:{c}" for c in categories)
    lo = start.strftime("%Y%m%d%H%M")
    hi = end.strftime("%Y%m%d%H%M")
    return f"({cats}) AND submittedDate:[{lo} TO {hi}]"


def fetch(query: str, start: int, max_results: int, attempts: int = 4) -> bytes:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    req = urllib.request.Request(
        f"{API}?{params}",
        headers={"User-Agent": "research_diary/1.0 (+https://github.com/irboi746/research_diary)"},
    )
    # arXiv returns 429 readily from shared addresses such as CI runners, so back
    # off and retry rather than dropping the day's compulsory source on the floor.
    delay = RATE_LIMIT_SECONDS
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if not retryable or attempt == attempts:
                raise
            wait = int(exc.headers.get("Retry-After") or delay)
            print(
                f"# HTTP {exc.code}, retrying in {wait}s ({attempt}/{attempts - 1})",
                file=sys.stderr,
            )
            time.sleep(wait)
            delay = min(delay * 2, 60)
    raise RuntimeError("unreachable")


def parse(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    out = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = (entry.findtext(f"{ATOM}id") or "").strip()
        # e.g. http://arxiv.org/abs/2509.12345v1 -> 2509.12345
        ident = re.sub(r"^https?://arxiv\.org/abs/", "", raw_id)
        ident = re.sub(r"v\d+$", "", ident)
        out.append(
            {
                "id": ident,
                "published": (entry.findtext(f"{ATOM}published") or "").strip(),
                "updated": (entry.findtext(f"{ATOM}updated") or "").strip(),
                "title": " ".join((entry.findtext(f"{ATOM}title") or "").split()),
                "summary": " ".join((entry.findtext(f"{ATOM}summary") or "").split()),
                "authors": [
                    (a.findtext(f"{ATOM}name") or "").strip()
                    for a in entry.findall(f"{ATOM}author")
                ],
                "categories": [
                    c.get("term", "") for c in entry.findall(f"{ATOM}category")
                ],
                "url": f"https://arxiv.org/abs/{ident}",
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--since", type=parse_since, default=parse_since("48h"))
    ap.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="override the categories in topics.toml (repeatable)",
    )
    ap.add_argument("--max", type=int, default=400, help="stop after this many results")
    ap.add_argument("--json", action="store_true", help="emit JSON lines instead of TSV")
    args = ap.parse_args(argv)

    categories = args.categories or arxiv_categories(load_config())
    if not categories:
        print("error: no arXiv categories configured in topics.toml", file=sys.stderr)
        return 2

    end = dt.datetime.now(dt.timezone.utc)
    start = end - args.since
    query = build_query(categories, start, end)
    print(f"# query: {query}", file=sys.stderr)

    results: list[dict] = []
    offset = 0
    while len(results) < args.max:
        if offset:
            time.sleep(RATE_LIMIT_SECONDS)
        try:
            batch = parse(fetch(query, offset, min(PAGE_SIZE, args.max - len(results))))
        except Exception as exc:  # noqa: BLE001 - surface the cause, do not mask it
            print(f"error: arXiv query failed: {exc}", file=sys.stderr)
            return 2
        if not batch:
            break
        results.extend(batch)
        offset += len(batch)
        if len(batch) < PAGE_SIZE:
            break

    for r in results:
        if args.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(f"{r['id']}\t{r['published']}\t{r['title']}\t{r['url']}")

    print(f"# {len(results)} results", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
