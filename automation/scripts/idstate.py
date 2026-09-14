#!/usr/bin/env python3
"""Canonical identity extraction and deduplication state.

Work reaches this pipeline by three routes — the arXiv API, enumerated conference
pages, and open web search — so the same paper routinely arrives under different
URLs on different days. Keying dedup on the URL therefore fails: `/abs/` vs
`/pdf/`, `v1` vs `v2`, and the ar5iv / alphaxiv / HuggingFace mirrors are all the
same work.

So identity, not URL, is the key. Priority: arXiv ID (version stripped) > DOI >
normalized URL.

State lives in automation/state/seen.ndjson, one record per line, sorted by key.
Sorted NDJSON keeps daily diffs to a few lines and makes conflicts between
concurrent pull requests rare and trivial to resolve.

Usage:
    idstate.py check  <url-or-id>    exit 0 = new, 1 = already covered
    idstate.py record <url-or-id> [--title T] [--venue V]
    idstate.py canon  <url-or-id>    print the canonical key (debugging)
    idstate.py stats
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse

STATE = pathlib.Path(__file__).resolve().parents[1] / "state" / "seen.ndjson"

# arXiv's modern identifier: 4-digit YYMM, dot, 4-or-5 digit number, optional
# version suffix. The version is deliberately dropped — v1 in September and v2 in
# November are the same paper.
ARXIV_NEW = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")

# Pre-2007 style: archive[.subject]/YYMMNNN, e.g. hep-ex/0307015, cond-mat/0207270.
ARXIV_OLD = re.compile(r"\b([a-z][a-z-]+(?:\.[A-Za-z]{2})?/\d{7})(?:v\d+)?\b")

DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>&]+)", re.IGNORECASE)

# Hosts that mirror arXiv. Listed so a mirror URL is recognised as arXiv content
# even when the ID pattern alone would be ambiguous.
ARXIV_HOSTS = {
    "arxiv.org",
    "export.arxiv.org",
    "ar5iv.org",
    "ar5iv.labs.arxiv.org",
    "alphaxiv.org",
    "www.alphaxiv.org",
    "browse.arxiv.org",
    "huggingface.co",
    "papers.cool",
}

TRACKING_PREFIXES = ("utm_", "mc_", "pk_", "hsa_", "_hs")
TRACKING_EXACT = {
    "fbclid", "gclid", "dclid", "msclkid", "igshid", "mkt_tok",
    "ref", "referrer", "source", "spm", "at_medium", "at_campaign",
}


def _strip_doi_punctuation(doi: str) -> str:
    """DOIs are greedy to match; trailing sentence punctuation is not part of them."""
    return doi.rstrip(".,;:)]}>\"'")


def normalize_url(raw: str) -> str:
    """Collapse the cosmetic variations that make identical URLs compare unequal."""
    raw = raw.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw

    parts = urllib.parse.urlsplit(raw)
    host = parts.hostname or ""
    if host.startswith("www."):
        host = host[4:]

    # Keep a non-default port; drop :80/:443 which are noise.
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"

    path = parts.path
    # AMP variants serve the same document.
    path = re.sub(r"/amp(?:/|\.html?)?$", "", path)
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    if path in ("", "/"):
        path = "/"

    kept = [
        (k, v)
        for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower() in TRACKING_EXACT or k.lower().startswith(TRACKING_PREFIXES))
    ]
    query = urllib.parse.urlencode(sorted(kept))

    # The fragment never identifies a distinct document here.
    return urllib.parse.urlunsplit(("https", host, path, query, ""))


def canonical(raw: str) -> tuple[str, str]:
    """Return (kind, key) for a URL or bare identifier.

    kind is one of "arxiv", "doi", "url"; key is stable across the mirrors and
    versions of the same work.
    """
    s = raw.strip()

    # A bare identifier typed directly, e.g. "arXiv:2509.12345v2" or a DOI.
    # fullmatch, so this only fires when the whole string *is* the identifier.
    bare = re.sub(r"^arxiv:\s*", "", s, flags=re.IGNORECASE).strip()
    m = ARXIV_NEW.fullmatch(bare) or ARXIV_OLD.fullmatch(bare)
    if m:
        return "arxiv", m.group(1).lower()
    m = DOI.fullmatch(bare)
    if m:
        return "doi", _strip_doi_punctuation(m.group(1)).lower()

    host = (urllib.parse.urlsplit(normalize_url(s)).hostname or "").lower()
    path_and_query = s

    # HuggingFace and papers.cool host far more than arXiv mirrors, so only treat
    # them as arXiv when the path actually says so.
    is_arxiv_host = host in ARXIV_HOSTS
    if host in ("huggingface.co", "papers.cool") and "/papers/" not in s:
        is_arxiv_host = False

    if is_arxiv_host:
        m = ARXIV_NEW.search(path_and_query) or ARXIV_OLD.search(path_and_query)
        if m:
            return "arxiv", m.group(1).lower()

    # An arXiv ID cited in a non-arXiv URL (a DOI landing page, a blog post) is
    # still the same paper.
    m = ARXIV_NEW.search(path_and_query)
    if m and ("arxiv" in s.lower() or is_arxiv_host):
        return "arxiv", m.group(1).lower()

    m = DOI.search(s)
    if m:
        return "doi", _strip_doi_punctuation(m.group(1)).lower()

    return "url", normalize_url(s)


def load() -> dict[str, dict]:
    if not STATE.exists():
        return {}
    out: dict[str, dict] = {}
    for line in STATE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            print(f"warning: skipping malformed state line: {line[:80]}", file=sys.stderr)
            continue
        if "key" in rec:
            out[rec["key"]] = rec
    return out


def save(records: dict[str, dict]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(records[k], sort_keys=True, ensure_ascii=False)
        for k in sorted(records)
    ]
    STATE.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="exit 0 if new, 1 if already covered")
    p.add_argument("target")

    p = sub.add_parser("record", help="add to state")
    p.add_argument("target")
    p.add_argument("--title", default="")
    p.add_argument("--venue", default="")

    p = sub.add_parser("canon", help="print the canonical key")
    p.add_argument("target")

    sub.add_parser("stats", help="summarise the state file")

    args = ap.parse_args(argv)

    if args.cmd == "canon":
        kind, key = canonical(args.target)
        print(f"{kind}\t{key}")
        return 0

    if args.cmd == "stats":
        recs = load()
        by_kind: dict[str, int] = {}
        for r in recs.values():
            by_kind[r.get("kind", "?")] = by_kind.get(r.get("kind", "?"), 0) + 1
        print(f"{len(recs)} records")
        for k in sorted(by_kind):
            print(f"  {k}: {by_kind[k]}")
        return 0

    kind, key = canonical(args.target)
    records = load()

    if args.cmd == "check":
        if key in records:
            print(f"seen ({kind}) {key}", file=sys.stderr)
            return 1
        print(f"new ({kind}) {key}", file=sys.stderr)
        return 0

    # record
    if key in records:
        print(f"already recorded ({kind}) {key}", file=sys.stderr)
        return 0
    records[key] = {
        "key": key,
        "kind": kind,
        "url": args.target.strip(),
        "title": args.title,
        "venue": args.venue,
        "first_seen": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
    }
    save(records)
    print(f"recorded ({kind}) {key}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
