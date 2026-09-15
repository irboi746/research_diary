#!/usr/bin/env python3
"""Tests for the shared post-parsing helpers.

Run: python3 automation/scripts/test_postparse.py

Every case here is drawn from something in the repository: a shape the published
posts or the shipped format examples actually use. Getting these wrong does not
produce a missed fabrication, it produces a false failure on good content, which
is worse -- it trains everyone to ignore the check.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import postparse as P  # noqa: E402

FAILURES: list[str] = []


def eq(name: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def truthy(name: str, got) -> None:
    if not got:
        FAILURES.append(f"{name}: expected a truthy value, got {got!r}")


# --- code stripping ----------------------------------------------------------
eq(
    "a fenced block is removed",
    P.urls("```sh\ncurl https://evil.tld/x\n```\nSee https://example.org/a"),
    ["https://example.org/a"],
)
eq("inline code is removed", P.urls("run `curl https://evil.tld/x` now"), [])
eq(
    "a heading inside a fence does not split sections",
    [h for h, _ in P.split_sections("## Real\ntext\n\n```yaml\n## not-a-heading\n```\n")],
    ["Real"],
)

# --- continuation folding ----------------------------------------------------
# Both shipped examples wrap Also-published bullets across two lines.
WRAPPED = '- Clarke, E. "Notes." DEF CON 34 —\n  https://media.defcon.org/x\n'
eq("a wrapped bullet becomes one logical line", len(P.logical_lines(WRAPPED)), 1)
truthy("a wrapped bullet keeps its URL", P.urls(P.logical_lines(WRAPPED)[0]))

# --- reference entries -------------------------------------------------------
# "1." is used by the examples and the Kubernetes post; "[1]" by the trends post.
eq("numbered entry style", sorted(P.parse_references("1. A paper. https://a.tld/x")), ["1"])
eq("bracketed entry style", sorted(P.parse_references("[1] A paper. https://a.tld/x")), ["1"])
eq(
    "a wrapped reference entry is one entry",
    len(P.parse_references('1. Author. "Title." Venue 2024.\n   https://a.tld/x\n')),
    1,
)

# --- citation markers --------------------------------------------------------
eq("a plain marker", P.cited_numbers("as shown [4]"), {"4"})
eq("a grouped marker", P.cited_numbers("as shown [9, 10]"), {"9", "10"})
eq("a range", P.cited_numbers("as shown [1-3]"), {"1", "2", "3"})
eq("an array subscript is not a citation", P.cited_numbers("argv[1] is the path"), set())
eq("a markdown link is not a citation", P.cited_numbers("see [1](https://a.tld/x)"), set())
eq("a link definition is not a citation", P.cited_numbers("[1]: https://a.tld/x"), set())
eq("adjacent markers", P.cited_numbers("both [1][2] agree"), {"1", "2"})

# --- URL normalization -------------------------------------------------------
eq(
    "www, scheme, trailing slash and fragment collapse",
    P.normalize_url("https://www.usenix.org/conference/woot24/technical-sessions/"),
    P.normalize_url("http://usenix.org/conference/woot24/technical-sessions#x"),
)
eq(
    "percent-encoding is decoded, so the DEF CON templates match",
    P.normalize_url("https://media.defcon.org/DEF%20CON%2034/"),
    "media.defcon.org/DEF CON 34",
)
eq(
    "a trailing full stop is not part of the URL",
    P.urls("See https://a.tld/x."),
    ["https://a.tld/x"],
)

# --- the index-page set ------------------------------------------------------
INDEXES = P.index_urls()
for u in (
    "https://www.usenix.org/conference/usenixsecurity24/technical-sessions",
    "https://www.usenix.org/conference/woot24/technical-sessions",
    "https://defcon.org/html/links/dc-archives/dc-30-archive.html",
    "https://www.blackhat.com/us-24/briefings/schedule/",
    "https://www.ieee-security.org/TC/SP2026/",
    "https://www.ndss-symposium.org/ndss2026/accepted-papers/",
    "https://www.sigsac.org/ccs/CCS2026/",
    "https://www.unprompted.au/schedule",
    # Retired as a source, still blocked as a citation. The set must only grow:
    # dropping a venue is not a reason to start trusting its landing page.
    "https://offbyone.sg/",
):
    if P.normalize_url(u) not in INDEXES:
        FAILURES.append(f"index set is missing a published fabrication target: {u}")

# An individual presentation page must never be mistaken for the listing it is on.
for u in (
    "https://www.usenix.org/conference/usenixsecurity24/presentation/deng",
    "https://www.usenix.org/conference/woot26/presentation/fall",
):
    if P.normalize_url(u) in INDEXES:
        FAILURES.append(f"index set wrongly contains an individual paper page: {u}")

# --- identifiers -------------------------------------------------------------
truthy("a DOI is found", P.DOI.search("doi:10.1109/SP46214.2022.9833751"))
eq(
    "an arXiv version suffix is stripped",
    P.ARXIV_ID.search("arXiv:2609.15963v2").group(1),
    "2609.15963",
)

if FAILURES:
    print(f"postparse: FAILED ({len(FAILURES)})\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("postparse: all checks passed")
