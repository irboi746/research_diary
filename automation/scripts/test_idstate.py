#!/usr/bin/env python3
"""Tests for canonical identity extraction.

Run: python3 automation/scripts/test_idstate.py

Deliberately dependency-free — plain asserts, no pytest — so the same command
works locally, in CI, and in the Jules VM without an install step.

The cases below are the ones that actually break deduplication in practice: the
same paper arriving from the arXiv API, from a mirror surfaced by web search, and
from a citation inside a blog post.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from idstate import canonical, normalize_url  # noqa: E402

FAILURES: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{name}\n     got:  {got!r}\n     want: {want!r}")


def check_true(name: str, cond: bool) -> None:
    if not cond:
        FAILURES.append(name)


ARXIV_SAME = [
    "https://arxiv.org/abs/2509.12345",
    "https://arxiv.org/abs/2509.12345v1",
    "https://arxiv.org/abs/2509.12345v3",
    "https://arxiv.org/pdf/2509.12345",
    "https://arxiv.org/pdf/2509.12345v2",
    "http://arxiv.org/abs/2509.12345/",
    "https://www.arxiv.org/abs/2509.12345",
    "https://export.arxiv.org/abs/2509.12345",
    "https://ar5iv.labs.arxiv.org/html/2509.12345",
    "https://alphaxiv.org/abs/2509.12345",
    "https://huggingface.co/papers/2509.12345",
    "https://arxiv.org/abs/2509.12345?utm_source=twitter&utm_medium=social",
    "https://arxiv.org/abs/2509.12345#section-3",
    "arXiv:2509.12345",
    "arXiv:2509.12345v2",
    "2509.12345",
]

for url in ARXIV_SAME:
    check(f"arxiv variant collapses: {url}", canonical(url), ("arxiv", "2509.12345"))

check_true(
    "distinct arxiv papers stay distinct",
    canonical("https://arxiv.org/abs/2509.12345")[1]
    != canonical("https://arxiv.org/abs/2509.12346")[1],
)

check(
    "five-digit arxiv id (the post-2015 form)",
    canonical("https://arxiv.org/abs/2509.12345"),
    ("arxiv", "2509.12345"),
)

check(
    "four-digit arxiv id (the 2007-2014 form)",
    canonical("https://arxiv.org/abs/0704.0001"),
    ("arxiv", "0704.0001"),
)

# arXiv numbers are 4 or 5 digits and never 6. Matching a longer run would
# silently truncate an unrelated identifier into a plausible-looking paper id.
check(
    "six-digit number is not mistaken for an arxiv id",
    canonical("https://arxiv.org/abs/2509.123456")[0],
    "url",
)

for u in (
    "https://arxiv.org/abs/hep-ex/0307015",
    "https://arxiv.org/abs/hep-ex/0307015v1",
    "hep-ex/0307015",
):
    check(f"legacy arxiv id: {u}", canonical(u), ("arxiv", "hep-ex/0307015"))

check(
    "legacy arxiv id with subject class",
    canonical("https://arxiv.org/abs/cond-mat/0207270"),
    ("arxiv", "cond-mat/0207270"),
)

DOI_SAME = [
    "https://doi.org/10.1145/3548606.3560664",
    "https://dx.doi.org/10.1145/3548606.3560664",
    "10.1145/3548606.3560664",
    "See DOI 10.1145/3548606.3560664.",
]

for ref in DOI_SAME:
    check(f"doi variant collapses: {ref}", canonical(ref), ("doi", "10.1145/3548606.3560664"))

check(
    "trailing punctuation is not part of the doi",
    canonical("10.1145/3548606.3560664.")[1],
    "10.1145/3548606.3560664",
)

URL_SAME = [
    "https://www.usenix.org/conference/usenixsecurity25/presentation/smith",
    "http://usenix.org/conference/usenixsecurity25/presentation/smith/",
    "https://usenix.org/conference/usenixsecurity25/presentation/smith?utm_campaign=x",
    "https://usenix.org/conference/usenixsecurity25/presentation/smith#abstract",
    "https://usenix.org/conference/usenixsecurity25/presentation/smith?fbclid=abc",
]

for url in URL_SAME:
    check(
        f"url fallback normalizes: {url}",
        canonical(url),
        ("url", "https://usenix.org/conference/usenixsecurity25/presentation/smith"),
    )

# Dropping every query parameter would merge genuinely different pages.
check_true(
    "meaningful query params are preserved",
    canonical("https://example.org/paper?id=1")[1]
    != canonical("https://example.org/paper?id=2")[1],
)

check_true(
    "amp variant collapses",
    canonical("https://example.org/post/amp")[1] == canonical("https://example.org/post")[1],
)

# huggingface.co hosts far more than arXiv mirrors; only /papers/ is one.
check(
    "huggingface non-paper url is not arxiv",
    canonical("https://huggingface.co/meta-llama/Llama-3-8B")[0],
    "url",
)

check(
    "arxiv id cited in a blog post resolves to the paper",
    canonical("https://blog.example.com/notes?ref=arxiv.org/abs/2509.12345"),
    ("arxiv", "2509.12345"),
)

check_true("normalize_url adds scheme", normalize_url("example.org/x").startswith("https://"))
check_true("normalize_url keeps non-default port", ":8080" in normalize_url("https://example.org:8080/x"))


if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("idstate: all checks passed")
