#!/usr/bin/env python3
"""Offline checks for fulltext.py.

Two halves. The first needs no third-party packages and always runs: the SSRF
guard, the fallback chain, and the de-hyphenation. The second parses a real
arXiv HTML skeleton and is SKIPPED when beautifulsoup4/html2text are absent --
this must not fail, because the merge-path CI job installs nothing on purpose
and would otherwise go red for a tool it never runs.

Nothing here touches the network: the fetch is stubbed, so a run is fast and
cannot be broken by arXiv being slow.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import fulltext as F  # noqa: E402

FAILURES: list[str] = []
SKIPPED: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}\n      got:  {got!r}\n      want: {want!r}")


def check_true(label: str, got) -> None:
    if not got:
        FAILURES.append(label)


# --- the SSRF guard ----------------------------------------------------------
# These identifiers came out of untrusted pages, and the fetch runs next to a
# token, so the same guard linkcheck.py uses applies here.
for bad in (
    "file:///etc/passwd",
    "ftp://example.tld/x",
    "http://127.0.0.1/x",
    "http://localhost/x",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/x",
    "http://[::1]/x",
):
    check_true(f"refuses {bad}", F._safe(bad) is not None)

check("allows a normal public https URL", F._safe("https://arxiv.org/html/2609.13353"), None)
check_true("a URL with no host is refused", F._safe("https:///x") is not None)


# --- the fallback chain ------------------------------------------------------
# The order is html -> pdf -> abstract, and the caller must be able to tell which
# happened: only the first two justify writing as though the paper was read.
def stub(html=None, pdf=None):
    def _fetch(url: str) -> bytes:
        if "/html/" in url:
            if html is None:
                raise F.Unavailable("HTTP 404 for " + url)
            return html
        if pdf is None:
            raise F.Unavailable("HTTP 404 for " + url)
        return pdf
    return _fetch


real_fetch, real_html, real_pdf = F.fetch, F.html_to_text, F.pdf_to_text
try:
    F.html_to_text = lambda doc: "HTML BODY"
    F.pdf_to_text = lambda data: "PDF BODY"

    F.fetch = stub(html=b"<html/>", pdf=b"%PDF")
    r = F.retrieve("2609.13353", abstract="ABS")
    check("html wins when it is available", (r["source"], r["text"]), ("html", "HTML BODY"))

    F.fetch = stub(html=None, pdf=b"%PDF")
    r = F.retrieve("2609.13353", abstract="ABS")
    check("falls back to pdf when there is no html", (r["source"], r["text"]), ("pdf", "PDF BODY"))
    check_true("the html failure is reported", any("html:" in n for n in r["notes"]))

    F.fetch = stub(html=None, pdf=None)
    r = F.retrieve("2609.13353", abstract="ABS")
    check("falls back to the abstract when neither renders", (r["source"], r["text"]), ("abstract", "ABS"))
    check_true(
        "the abstract fallback says to mark the post",
        any("Abstract only" in n for n in r["notes"]),
    )

    # An empty parse is a failure, not a success with no text -- otherwise a post
    # would be written from nothing while reporting source=html.
    F.fetch = stub(html=b"<html/>", pdf=b"%PDF")
    F.html_to_text = lambda doc: "   \n  "
    r = F.retrieve("2609.13353", abstract="ABS")
    check("html that parses to whitespace falls through", r["source"], "pdf")

    # A malformed paper must cost that paper, not abort the run.
    F.html_to_text = lambda doc: (_ for _ in ()).throw(ValueError("broken"))
    r = F.retrieve("2609.13353", abstract="ABS")
    check("a parser exception is caught and recorded", r["source"], "pdf")
    check_true("the parser failure is reported", any("ValueError" in n for n in r["notes"]))

    F.html_to_text = lambda doc: "x" * 100
    F.fetch = stub(html=b"<html/>")
    r = F.retrieve("2609.13353", max_chars=40)
    check_true("max_chars truncates", r["chars"] <= 60 and r["text"].endswith("[truncated]"))
finally:
    F.fetch, F.html_to_text, F.pdf_to_text = real_fetch, real_html, real_pdf


# --- text tidying ------------------------------------------------------------
check("collapses runs of blank lines", F._tidy("a\n\n\n\n\nb"), "a\n\nb")
check("collapses horizontal whitespace", F._tidy("a     b"), "a b")
check("strips non-breaking spaces", F._tidy("a\xa0b"), "a b")

# Justified two-column PDFs break words at the line end. Its own function so this
# needs no PDF, and so it runs even where pypdf is not installed.
check("rejoins a word broken across a line", F.dehyphenate("evalua-\ntions"), "evaluations")
check("leaves a hyphen that is not at a line end", F.dehyphenate("side-channel"), "side-channel")
check("leaves a hyphen before a blank line", F.dehyphenate("foo-\n\nbar"), "foo-\n\nbar")
check("handles several breaks", F.dehyphenate("aaa-\nbbb ccc-\nddd"), "aaabbb cccddd")


# --- the library-backed half -------------------------------------------------
try:
    import bs4  # noqa: F401
    import html2text  # noqa: F401
except ImportError as exc:
    SKIPPED.append(f"HTML extraction checks: {exc}. Install requirements.txt to run them.")
else:
    # The shape arXiv's LaTeXML renderer actually emits: an ltx_document article,
    # class-tagged sections, and a bibliography that must not reach the output.
    PAGE = """<!DOCTYPE html><html><head><title>t</title></head><body>
    <nav class="ltx_TOC"><a href="#S1">Table of contents junk</a></nav>
    <div class="ltx_page_content">
      <article class="ltx_document">
        <h1 class="ltx_title">A Practical Attack</h1>
        <div class="ltx_authors">Ada Lovelace</div>
        <div class="ltx_abstract"><h6>Abstract</h6><p>We broke the thing.</p></div>
        <section class="ltx_section"><h2>1 Introduction</h2>
          <p class="ltx_para">The introduction body text.</p>
          <math alttext="x^2"><mi>x</mi></math>
        </section>
        <script>var tracking = 1;</script>
        <section class="ltx_bibliography"><h2>References</h2>
          <li class="ltx_bibitem">Someone. A cited work. 1999.</li>
        </section>
      </article>
    </div></body></html>"""

    text = F.html_to_text(PAGE)
    check_true("the abstract survives", "We broke the thing." in text)
    check_true("body prose survives", "The introduction body text." in text)
    check_true("the bibliography is removed", "A cited work" not in text)
    check_true("the table of contents is removed", "Table of contents junk" not in text)
    check_true("the author block is removed", "Ada Lovelace" not in text)
    check_true("scripts are removed", "tracking" not in text)

    # An abs landing page has no ltx_document article. This is the ar5iv trap:
    # ar5iv now redirects to /abs/, which is HTTP 200 with no full text, so a
    # parser that returned "" here would report success having read nothing.
    try:
        F.html_to_text("<html><body><p>Just an abstract page.</p></body></html>")
        FAILURES.append("a page with no ltx_document article must raise Unavailable")
    except F.Unavailable:
        pass

for note in SKIPPED:
    print(f"skipped: {note}")

if FAILURES:
    print(f"fulltext: FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print(f"fulltext: all checks passed{f' ({len(SKIPPED)} skipped)' if SKIPPED else ''}")
