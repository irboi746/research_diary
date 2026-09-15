#!/usr/bin/env python3
"""Retrieve the full text of an arXiv paper, HTML first, PDF as a fallback.

An abstract is enough to rank a paper and not enough to write about one. This
fetches the body so a brief can quote numbers and mechanisms rather than
paraphrasing the abstract back.

Order, and why:

  1. https://arxiv.org/html/<id>   arXiv's own LaTeXML rendering. Class-tagged
                                   (ltx_abstract, ltx_section, ltx_bibliography),
                                   so the parts worth keeping are identifiable
                                   rather than guessed at. Coverage is broad --
                                   papers back to 2007 render -- and it 404s
                                   cleanly when a paper has none.
  2. https://arxiv.org/pdf/<id>    Only when there is no HTML. Layout-recovered
                                   text: usable, but hyphenated across line
                                   breaks and column-order dependent.
  3. abstract                      Whatever the caller already had. The post
                                   formats carry an explicit marker for this
                                   case: "*Abstract only - full text not
                                   retrieved.*" Say so rather than implying the
                                   paper was read.

Do NOT add ar5iv as a source. ar5iv.org and ar5iv.labs.arxiv.org now redirect to
arxiv.org/abs/<id>, which returns HTTP 200 and the abstract landing page -- so a
naive "try ar5iv first" reports success while silently yielding no full text at
all. This was measured, not assumed.

Requires beautifulsoup4, html2text and pypdf (see requirements.txt). This is an
ingestion tool; it is deliberately not imported by anything on the merge path.

Usage:
    fulltext.py 2609.13353
    fulltext.py 2609.13353 --json
    fulltext.py 2609.13353 --max-chars 20000
"""

from __future__ import annotations

import argparse
import io
import ipaddress
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HTML_URL = "https://arxiv.org/html/{ident}"
PDF_URL = "https://arxiv.org/pdf/{ident}"
UA = "research_diary-fulltext/1.0 (+https://github.com/irboi746/research_diary)"
PER_HOST_DELAY = 3.0
TIMEOUT = 60
# Blocks LaTeXML marks as non-body: references, the table of contents, the author
# block, and the maths/markup that html2text would render as noise.
DROP_TAGS = ("script", "style", "math", "svg", "nav", "form", "button")
DROP_CLASSES = (
    "ltx_bibliography",
    "ltx_TOC",
    "ltx_authors",
    "ltx_page_footer",
    "ltx_page_header",
)

_last_hit: dict[str, float] = {}


class Unavailable(Exception):
    """No text could be retrieved by this route."""


def _safe(url: str) -> str | None:
    """Reject anything that is not a plain public http(s) fetch.

    Same guard as linkcheck.py, and for the same reason: these fetches are driven
    by identifiers that came out of untrusted pages.
    """
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        return f"not an http(s) URL: {url}"
    host = p.hostname
    if not host:
        return f"no host in URL: {url}"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return f"unresolvable host: {url}"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return f"resolves to a non-public address ({ip}): {url}"
    return None


def _throttle(host: str) -> None:
    last = _last_hit.get(host)
    if last is not None:
        wait = PER_HOST_DELAY - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
    _last_hit[host] = time.monotonic()


def fetch(url: str) -> bytes:
    problem = _safe(url)
    if problem:
        raise Unavailable(problem)
    _throttle(urllib.parse.urlsplit(url).hostname or "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise Unavailable(f"HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise Unavailable(f"{exc} for {url}") from exc


def html_to_text(document: str) -> str:
    """Body text of an arXiv LaTeXML page, references and furniture removed.

    Selecting the <article> and dropping blocks by class beats walking the tag
    tree and counting depth: one unclosed element inside a dropped region wedges
    a depth counter and silently returns almost nothing.
    """
    from bs4 import BeautifulSoup  # imported lazily so --help works without deps
    import html2text

    soup = BeautifulSoup(document, "html.parser")
    article = soup.find("article", class_=lambda c: c and "ltx_document" in c)
    if article is None:
        raise Unavailable("no <article class='ltx_document'> in the page")

    for tag in DROP_TAGS:
        for node in article.find_all(tag):
            node.decompose()
    for cls in DROP_CLASSES:
        for node in article.find_all(class_=lambda c, want=cls: c and want in c):
            node.decompose()

    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.body_width = 0
    return _tidy(converter.handle(str(article)))


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader  # imported lazily so --help works without deps

    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return _tidy(dehyphenate("\n".join(pages)))


def dehyphenate(text: str) -> str:
    """Rejoin words a PDF broke across a line end ("evalua-\ntions").

    Left in, every such word is unsearchable and unquotable. Joining without the
    hyphen is right for a syllable break and wrong for a compound that happens to
    land on the line end ("language-model" -> "languagemodel"); the former is far
    more common in justified two-column text and neither is distinguishable
    without a dictionary. One of several reasons HTML is tried first.

    Its own function so it can be tested without constructing a PDF.
    """
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _tidy(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def retrieve(ident: str, abstract: str = "", max_chars: int = 0) -> dict:
    """Return {"id", "source", "text", "chars", "notes"}.

    `source` is "html", "pdf" or "abstract" -- the caller needs to know which,
    because only the first two justify writing as though the paper was read.
    """
    notes: list[str] = []

    for source, url, convert in (
        ("html", HTML_URL.format(ident=ident), html_to_text),
        ("pdf", PDF_URL.format(ident=ident), pdf_to_text),
    ):
        try:
            raw = fetch(url)
            text = convert(raw.decode("utf-8", "replace") if source == "html" else raw)
        except Unavailable as exc:
            notes.append(f"{source}: {exc}")
            continue
        except ImportError as exc:
            notes.append(f"{source}: missing dependency ({exc}); see requirements.txt")
            continue
        except Exception as exc:  # noqa: BLE001 - a malformed paper must not abort the run
            notes.append(f"{source}: could not parse ({exc.__class__.__name__}: {exc})")
            continue
        if not text.strip():
            notes.append(f"{source}: parsed to empty text")
            continue
        if max_chars and len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n\n[truncated]"
        return {"id": ident, "source": source, "text": text, "chars": len(text), "notes": notes}

    text = _tidy(abstract)
    notes.append("fell back to the abstract; mark the item *Abstract only* in the post")
    return {"id": ident, "source": "abstract", "text": text, "chars": len(text), "notes": notes}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("ident", help="arXiv id, e.g. 2609.13353")
    ap.add_argument("--abstract", default="", help="fallback text if no full text is available")
    ap.add_argument("--max-chars", type=int, default=0, help="truncate the body at N characters")
    ap.add_argument("--json", action="store_true", help="emit one JSON object instead of text")
    args = ap.parse_args(argv)

    result = retrieve(args.ident, args.abstract, args.max_chars)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"# source: {result['source']}  chars: {result['chars']}", file=sys.stderr)
        for note in result["notes"]:
            print(f"# note: {note}", file=sys.stderr)
        print(result["text"])
    return 0 if result["source"] != "abstract" else 1


if __name__ == "__main__":
    sys.exit(main())
