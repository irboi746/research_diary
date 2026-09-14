#!/usr/bin/env python3
"""Tier 2 retrieval: enumerate the conference pages worth reading.

None of USENIX, DEF CON, Black Hat or Off-by-One offers an API, but all are
open-access with predictable URLs. So this script computes *which pages to visit*
and prints them — Jules then reads those pages itself.

That split is deliberate. HTML scrapers against four conference sites would rot
every time one is redesigned, and would fail silently when they did. A URL
builder is string formatting: it cannot rot, and a wrong URL shows up immediately
as a 404 that `--check` will catch.

Usage:
    sources.py urls                 # current and previous edition of each venue
    sources.py urls --years 3
    sources.py urls --source "DEF CON"
    sources.py urls --check         # HEAD each URL and report status

Placeholders in url_templates (automation/config/topics.toml):
    {yy}    two-digit year, e.g. 26
    {yyyy}  four-digit year, e.g. 2026
    {dc}    DEF CON edition number (DEF CON N took place in 1992 + N)
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys
import tomllib
import urllib.error
import urllib.request

CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config" / "topics.toml"

# DEF CON 1 was held in 1993, so edition N maps to year 1992 + N.
# Cross-check: DEF CON 32 was 2024, and 2024 - 1992 = 32.
DEFCON_EPOCH = 1992


def load_config() -> dict:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)


def expand(template: str, year: int) -> str:
    return template.format(
        yy=f"{year % 100:02d}",
        yyyy=year,
        dc=year - DEFCON_EPOCH,
    )


def build(cfg: dict, years: int, only: str | None) -> list[tuple[str, int, str]]:
    """Return (source_name, year, url) for each page worth visiting."""
    this_year = dt.datetime.now(dt.timezone.utc).year
    out: list[tuple[str, int, str]] = []
    for src in cfg.get("sources", []):
        if src.get("retrieval") != "urls":
            continue
        name = src.get("name", "?")
        if only and only.lower() not in name.lower():
            continue
        templates = src.get("url_templates", [])
        for year in range(this_year, this_year - years, -1):
            for t in templates:
                # A template with no year placeholder is a single standing page;
                # emit it once rather than once per year.
                url = expand(t, year)
                if url == t and any(u == url for _, _, u in out):
                    continue
                out.append((name, year, url))
    return out


def head(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "research_diary/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as exc:
        # Some sites reject HEAD but serve GET; retry before calling it dead.
        if exc.code in (403, 405):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "research_diary/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return str(resp.status)
            except Exception as exc2:  # noqa: BLE001
                return f"ERR {exc2}"
        return str(exc.code)
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("urls", help="print the pages to read")
    p.add_argument("--years", type=int, default=2, help="how many editions back (default 2)")
    p.add_argument("--source", default=None, help="limit to sources matching this substring")
    p.add_argument("--check", action="store_true", help="HEAD each URL and report status")
    args = ap.parse_args(argv)

    rows = build(load_config(), args.years, args.source)
    if not rows:
        print("error: no tier-2 sources matched", file=sys.stderr)
        return 2

    this_year = dt.datetime.now(dt.timezone.utc).year
    failures = 0
    for name, year, url in rows:
        if args.check:
            status = head(url)
            ok = status.startswith("2") or status.startswith("3")
            # The current edition's archive page does not exist until after the
            # conference runs, so a 404 there is expected for most of the year.
            # Only a past edition going missing means a template has gone stale.
            expected = not ok and year >= this_year
            if not ok and not expected:
                failures += 1
            label = "ok " if ok else ("-- " if expected else "BAD")
            note = "  (not published yet)" if expected else ""
            print(f"{label} {status:<6} {name} {year}\t{url}{note}")
        else:
            print(f"{name}\t{year}\t{url}")

    if args.check:
        print(f"\n{failures} stale template(s) out of {len(rows)} URLs", file=sys.stderr)
        # A stale template 404s silently and drops a compulsory source, so make
        # that a non-zero exit rather than a line of output nobody reads.
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
