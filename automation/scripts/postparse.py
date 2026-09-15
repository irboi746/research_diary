#!/usr/bin/env python3
"""Parsing helpers shared by validate.py and linkcheck.py.

These exist because every grounding check needs the same three things first, and
getting any of them wrong produces false failures on content that is perfectly
fine:

  * Code must be stripped. A security diary writes `##` inside a YAML block and
    prints URLs in shell snippets; neither is a heading or a citation.
  * Continuation lines must be folded. The shipped format examples wrap both
    Also-published bullets and reference entries across two lines, putting the
    title on one and the URL on the next. A per-line rule reports those as items
    with no source.
  * Citations come in more shapes than `[1]`. The published posts use grouped
    markers (`[9, 10]`), two different reference-entry styles, and prose that
    mentions `argv[1]`.
"""

from __future__ import annotations

import pathlib
import re
import tomllib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.toml"

FENCE = re.compile(r"(?ms)^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$")
INLINE_CODE = re.compile(r"`[^`\n]*`")

# Trailing punctuation is excluded so a URL at the end of a sentence does not
# absorb the full stop and then 404.
URL = re.compile(r"https?://[^\s<>()\[\]]+[^\s<>()\[\].,;:!?'\"]")

# Reference entries appear as "1. ..." (the examples, the Kubernetes post) and
# as "[1] ..." (the trends post). Both are accepted; neither is canonical.
ENTRY = re.compile(r"^(?:\[(?P<b>\d+)\]|(?P<n>\d+)[.)])\s+(?P<text>.*)$")

# A citation marker, including groups like "[9, 10]" and ranges like "[1-3]".
# The lookbehind rejects argv[1] and foo)[2]; the lookahead rejects the markdown
# link [1](url) and the link definition [1]: url.
CITATION = re.compile(r"(?<![\w\])])\[(\d+(?:\s*[-,;–]\s*\d+)*)\](?![(:])")

DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+[a-zA-Z0-9]")
ARXIV_ID = re.compile(r"\b(?:arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?\b", re.I)

HEADING = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline spans, keeping line count intact."""
    def blank(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")

    return INLINE_CODE.sub("", FENCE.sub(blank, text))


def logical_lines(text: str) -> list[str]:
    """Fold continuation lines into the list item or reference entry above them.

    A line continues the previous one when it is indented or simply runs on, and
    is not itself a bullet, an entry, a heading or a blank.
    """
    out: list[str] = []
    for raw in text.splitlines():
        is_new = (
            not raw.strip()
            or re.match(r"^\s*[-*+]\s", raw)
            or re.match(r"^\s*(?:\[\d+\]|\d+[.)])\s", raw)
            or raw.lstrip().startswith("#")
        )
        if is_new or not out or not out[-1].strip():
            out.append(raw)
        else:
            out[-1] = out[-1].rstrip() + " " + raw.strip()
    return out


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split a post body on its `##` headings into (heading, text) pairs."""
    parts = re.split(r"(?m)^##[ \t]+(.+?)[ \t]*#*[ \t]*$", strip_code(body))
    # parts[0] is whatever preceded the first heading.
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def split_references(body: str) -> tuple[str, str | None]:
    """Return (prose, references) — references is None when there is no such section."""
    m = re.search(r"(?m)^#{1,3}[ \t]+References[ \t]*$", strip_code(body))
    if not m:
        return strip_code(body), None
    return strip_code(body)[: m.start()], strip_code(body)[m.end():]


def parse_references(refs: str) -> dict[str, str]:
    """Map reference number -> entry text, with continuations folded in."""
    out: dict[str, str] = {}
    for line in logical_lines(refs):
        m = ENTRY.match(line.strip())
        if m:
            out[m.group("b") or m.group("n")] = m.group("text")
    return out


def cited_numbers(prose: str) -> set[str]:
    """Every reference number referred to in prose, groups and ranges expanded."""
    out: set[str] = set()
    for m in CITATION.finditer(prose):
        inner = m.group(1)
        if re.fullmatch(r"\d+\s*[-–]\s*\d+", inner):
            lo, hi = (int(x) for x in re.split(r"[-–]", inner))
            if hi - lo < 50:  # a range, not two numbers that happen to be hyphenated
                out.update(str(n) for n in range(lo, hi + 1))
                continue
        out.update(p.strip() for p in re.split(r"[,;]", inner) if p.strip().isdigit())
    return out


def urls(text: str) -> list[str]:
    return URL.findall(text)


def normalize_url(u: str) -> str:
    """Collapse the spellings of one page to a single key.

    Percent-decoding matters: the DEF CON templates contain %20, and a citation
    that writes the space differently is still the same index page.
    """
    p = urllib.parse.urlsplit(u.strip().rstrip(".,;:)\"'"))
    host = p.netloc.lower().split("@")[-1]
    host = host.removeprefix("www.")
    for port in (":80", ":443"):
        host = host.removesuffix(port)
    path = urllib.parse.unquote(p.path).rstrip("/")
    path = re.sub(r"/index\.html?$", "", path)
    return f"{host}{path}"


def index_urls() -> set[str]:
    """Every conference index page the pipeline enumerates, normalized.

    Built from the same url_templates sources.py hands the agent, so the set
    tracks the config instead of drifting from it.
    """
    import datetime as dt

    with CONFIG.open("rb") as fh:
        cfg = tomllib.load(fh)

    this_year = dt.datetime.now(dt.timezone.utc).year
    out = set()
    for src in cfg.get("sources", []):
        if src.get("retrieval") != "urls":
            continue
        for template in src.get("url_templates", []):
            # A wide but bounded window: {yy} collides across centuries and the
            # DEF CON edition goes negative before 1993.
            for year in range(2010, this_year + 2):
                try:
                    expanded = template.format(
                        yy=f"{year % 100:02d}", yyyy=year, dc=year - 1992
                    )
                except (KeyError, IndexError, ValueError):
                    continue
                out.add(normalize_url(expanded))
    return out


def identifiers(text: str) -> set[str]:
    """Every DOI, arXiv ID and URL in the text, for cross-file comparison."""
    clean = strip_code(text)
    out = {m.group(0) for m in DOI.finditer(clean)}
    out |= {m.group(1) for m in ARXIV_ID.finditer(clean)}
    out |= {normalize_url(u) for u in urls(clean)}
    return out
