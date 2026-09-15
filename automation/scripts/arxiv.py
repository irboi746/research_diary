#!/usr/bin/env python3
"""Tier 1 retrieval: today's arXiv announcements, over RSS by default.

arXiv is the only compulsory source with machine-readable retrieval, so it is the
one source whose daily coverage can be guaranteed rather than hoped for.

Two mechanisms, same output shape:

  RSS (default)   One request per category against rss.arxiv.org, which serves
                  the day's announcement list as a single document. This is the
                  normal path. export.arxiv.org rate-limits hard and answers a
                  burst of paged queries with HTTP 429; the feed does not, and a
                  daily run only ever needs today's announcements anyway.

  API (--api)     The Atom query at export.arxiv.org, paged and throttled. A feed
                  is only ever "today", so this is the only way to ask for a
                  historical window -- backfilling a missed day, or --since 7d.

Feed items carry an announce_type: new, cross, replace or replace-cross. The
replace* pair is a new version of something already announced, which is the
`reject` rule about superseded work, so by default only new and cross are kept.

Usage:
    arxiv.py                                   # today, categories from topics.toml
    arxiv.py --json
    arxiv.py --category cs.CR
    arxiv.py --announce-type new --announce-type cross --announce-type replace
    arxiv.py --api --since 7d                  # historical window, Atom API

Output is one candidate per line: ID <tab> published <tab> title <tab> URL.

Rate limiting: arXiv asks for a 3 second delay between consecutive calls, which
this enforces between requests on both paths. The index refreshes once a day, so
running this more than daily gains nothing.
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
FEED = "https://rss.arxiv.org/rss/{category}"
ATOM = "{http://www.w3.org/2005/Atom}"
# rss.arxiv.org is RSS 2.0 with two extension namespaces rather than Atom.
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
PAGE_SIZE = 200
RATE_LIMIT_SECONDS = 3
USER_AGENT = "research_diary/1.0 (+https://github.com/irboi746/research_diary)"
# new: first announcement. cross: announced in another primary category.
# replace / replace-cross: a new version of something already announced.
DEFAULT_ANNOUNCE_TYPES = ("new", "cross")
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


def arxiv_source(cfg: dict) -> dict:
    """The arXiv source block, whichever retrieval tier it currently declares.

    This used to key on `retrieval == "api"`, so flipping topics.toml to "rss"
    silently returned no categories and the day's compulsory source vanished
    without an error. Match on the name and let `retrieval` be whatever it is.
    """
    for src in cfg.get("sources", []):
        if src.get("name", "").lower() == "arxiv":
            return src
    return {}


def arxiv_categories(cfg: dict) -> list[str]:
    return list(arxiv_source(cfg).get("categories", []))


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
        headers={"User-Agent": USER_AGENT},
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


def _get(url: str, attempts: int = 4) -> bytes:
    """GET with the same 429/Retry-After backoff the API path uses."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
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


def fetch_feed(category: str, attempts: int = 4) -> bytes:
    return _get(FEED.format(category=category), attempts=attempts)


# "arXiv:2609.13353v1 Announce Type: new \n\nAbstract: ..." -- the id, the
# version and the announce type all live in <description>, and the id is
# repeated in <guid> as "oai:arXiv.org:2609.13353v1".
_DESC_ID = re.compile(r"arXiv:\s*(\S+?)(?:v\d+)?\s+Announce\s+Type", re.I)
_GUID_ID = re.compile(r"oai:arXiv\.org:(\S+?)(?:v\d+)?\Z", re.I)
_ABS_ID = re.compile(r"^https?://arxiv\.org/abs/(\S+?)(?:v\d+)?/?\Z", re.I)
_ABSTRACT = re.compile(r"Abstract:\s*(.*)\Z", re.S | re.I)


def _feed_identifier(item: ET.Element) -> str:
    """The bare arXiv id, version stripped, from whichever field carries it.

    Three sources in priority order because none is guaranteed: a malformed
    description must not cost the item, and the id has to agree with
    idstate.canonical() or the same paper dedups as two.
    """
    for text, pattern in (
        (item.findtext("description") or "", _DESC_ID),
        (item.findtext("guid") or "", _GUID_ID),
        ((item.findtext("link") or "").strip(), _ABS_ID),
    ):
        m = pattern.search(text.strip())
        if m:
            return m.group(1)
    return ""


def parse_feed(xml_bytes: bytes, announce_types: tuple[str, ...] | None = None) -> list[dict]:
    """Parse an rss.arxiv.org feed into the same records parse() returns.

    Keeping the shape identical is what lets ranking, dedup and the callers stay
    ignorant of which retrieval path produced a record.
    """
    allowed = DEFAULT_ANNOUNCE_TYPES if announce_types is None else tuple(announce_types)
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []
    feed_date = (channel.findtext("pubDate") or "").strip()

    out = []
    for item in channel.findall("item"):
        announce = (item.findtext(f"{ARXIV_NS}announce_type") or "").strip().lower()
        # An allowlist of what to keep, not a denylist of what to drop. The feed
        # emits four values -- new, cross, replace, replace-cross -- and a
        # denylist that enumerated only "replace" would let "replace-cross"
        # through as if it were a first announcement.
        if allowed and announce not in allowed:
            continue
        ident = _feed_identifier(item)
        if not ident:
            continue
        description = item.findtext("description") or ""
        m = _ABSTRACT.search(description)
        summary = " ".join((m.group(1) if m else description).split())
        creators = item.findtext(f"{DC_NS}creator") or ""
        published = (item.findtext("pubDate") or "").strip() or feed_date
        out.append(
            {
                "id": ident,
                "published": published,
                "updated": published,
                "title": " ".join((item.findtext("title") or "").split()),
                "summary": summary,
                "authors": [a.strip() for a in creators.split(",") if a.strip()],
                "categories": [
                    (c.text or "").strip() for c in item.findall("category") if (c.text or "").strip()
                ],
                "url": f"https://arxiv.org/abs/{ident}",
                "announce_type": announce,
            }
        )
    return out


def collect_rss(categories: list[str], announce_types: tuple[str, ...] | None = None) -> list[dict]:
    """One request per category, deduplicated by arXiv id.

    Categories overlap heavily -- a cs.CR paper cross-listed to cs.AI appears in
    both feeds -- so first occurrence wins and the rest are dropped here rather
    than becoming two entries in the brief.
    """
    seen: dict[str, dict] = {}
    for i, category in enumerate(categories):
        if i:
            time.sleep(RATE_LIMIT_SECONDS)
        for record in parse_feed(fetch_feed(category), announce_types):
            seen.setdefault(record["id"], record)
    return list(seen.values())


def emit(results: list[dict], as_json: bool) -> None:
    for r in results:
        if as_json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(f"{r['id']}\t{r['published']}\t{r['title']}\t{r['url']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--since", type=parse_since, default=parse_since("48h"),
                    help="window for --api; ignored on the RSS path, which is always today")
    ap.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="override the categories in topics.toml (repeatable)",
    )
    ap.add_argument(
        "--announce-type",
        action="append",
        dest="announce_types",
        choices=["new", "cross", "replace", "replace-cross"],
        help="RSS only: announce types to keep (repeatable, default: new and cross)",
    )
    ap.add_argument("--api", action="store_true",
                    help="use the Atom API instead of RSS (needed for a historical --since)")
    ap.add_argument("--max", type=int, default=400, help="stop after this many results")
    ap.add_argument("--json", action="store_true", help="emit JSON lines instead of TSV")
    args = ap.parse_args(argv)

    cfg = load_config()
    categories = args.categories or arxiv_categories(cfg)
    if not categories:
        print("error: no arXiv categories configured in topics.toml", file=sys.stderr)
        return 2

    if not args.api:
        announce = tuple(args.announce_types) if args.announce_types else tuple(
            arxiv_source(cfg).get("announce_types", DEFAULT_ANNOUNCE_TYPES)
        )
        print(f"# rss: {', '.join(categories)} (announce types: {', '.join(announce)})",
              file=sys.stderr)
        try:
            results = collect_rss(categories, announce)
        except Exception as exc:  # noqa: BLE001 - surface the cause, do not mask it
            print(f"error: arXiv feed fetch failed: {exc}", file=sys.stderr)
            return 2
        results = results[: args.max]
        emit(results, args.json)
        print(f"# {len(results)} results", file=sys.stderr)
        return 0

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

    emit(results, args.json)
    print(f"# {len(results)} results", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
