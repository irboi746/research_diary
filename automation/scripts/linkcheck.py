#!/usr/bin/env python3
"""Resolve the things a post claims to cite.

validate.py checks that every item has a locator. This checks that the locator
points at something, and at the right something. Both failures have shipped:

    10.1109/SP46214.2021.9833751   a published DOI that 404s -- the example
                                   file's DOI with the year changed by one
    arXiv:2605.12345               a real arXiv paper, on QLoRA PEFT modules,
                                   cited as Kubernetes RBAC work

Only doi.org and arxiv.org are treated as gates. They are unauthenticated, they
have no WAF, and they answer honestly: an unregistered DOI is a 404 and a
registered one is a 302, with no redirect followed. Everything else is reported
and not enforced -- measured against the published posts, dl.acm.org,
blackhat.com and cisa.gov all return 403 to a datacenter IP and usenix.org times
out intermittently, so gating on them would fail good pull requests often enough
that nobody would trust the check.

Usage:
    linkcheck.py --changed              # what this branch touched (default base: main)
    linkcheck.py --files a.md b.md
    linkcheck.py --changed --base origin/main
"""

from __future__ import annotations

import argparse
import difflib
import html
import ipaddress
import pathlib
import re
import socket
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import postparse  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
UA = "research_diary-linkcheck/1.0"
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"

# Hosts whose answers are trustworthy enough to block a merge on.
GATED_HOSTS = ("doi.org", "dx.doi.org", "arxiv.org")

PER_HOST_DELAY = 1.0
_last_hit: dict[str, float] = {}


class Finding:
    def __init__(self, path: str, gating: bool, message: str) -> None:
        self.path, self.gating, self.message = path, gating, message


def _safe(url: str) -> str | None:
    """Reject anything that is not a plain public http(s) fetch.

    The URLs here came out of pages the agent was reading, so this is a request
    forger's input, not ours. CI runs it next to a token.
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
        return None  # unresolvable is a link problem, not a safety problem
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


def status(url: str, follow: bool) -> tuple[int | None, str]:
    """Return (http status, note). A None status means we could not tell."""
    _throttle(urllib.parse.urlsplit(url).hostname or "")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):  # noqa: ANN002, ANN003
            return None

    opener = urllib.request.build_opener(
        *([] if follow else [NoRedirect]),
    )
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with opener.open(req, timeout=25) as resp:
                return resp.status, method
        except urllib.error.HTTPError as exc:
            # A redirect is the success case when we asked not to follow one.
            if not follow and exc.code in (301, 302, 303, 307, 308):
                return exc.code, method
            # Some hosts refuse HEAD with something other than 405; confirm with
            # a GET before calling a live page dead.
            if method == "HEAD":
                continue
            return exc.code, method
        except Exception as exc:  # noqa: BLE001
            if method == "HEAD":
                continue
            return None, str(exc)[:60]
    return None, "no response"


def _norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKD", html.unescape(s)).casefold()
    s = re.sub(r"\$[^$]*\$", " ", s)          # inline LaTeX
    s = re.sub(r"\\[a-z]+\{([^}]*)\}", r"\1", s)  # \emph{...}
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def titles_match(cited: str, real: str) -> bool:
    """Loose on purpose: catch 'unrelated paper', not 'retitled in v2'."""
    a, b = _norm_title(cited), _norm_title(real)
    if not a or not b:
        return True
    ta, tb = set(a.split()), set(b.split())
    jaccard = len(ta & tb) / len(ta | tb)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return jaccard >= 0.3 or ratio >= 0.5


def arxiv_titles(ids: list[str]) -> dict[str, str]:
    """Real titles for a batch of arXiv IDs. Empty dict when arXiv will not talk."""
    if not ids:
        return {}
    query = urllib.parse.urlencode({"id_list": ",".join(sorted(set(ids))), "max_results": 200})
    req = urllib.request.Request(f"{ARXIV_API}?{query}", headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1))
                continue
            return {}
        except Exception:  # noqa: BLE001
            return {}
    else:
        return {}

    out: dict[str, str] = {}
    for entry in ET.fromstring(raw).findall(f"{ATOM}entry"):
        ident = (entry.findtext(f"{ATOM}id") or "").rsplit("/", 1)[-1]
        title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
        # A bad ID comes back as an entry titled "Error", not as an empty feed.
        if not ident or title == "Error" or "api/errors" in (entry.findtext(f"{ATOM}id") or ""):
            continue
        out[re.sub(r"v\d+$", "", ident)] = title
    return out


def check_file(path: pathlib.Path) -> list[Finding]:
    rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    text = path.read_text(encoding="utf-8")
    body = text.split("+++", 2)[-1]
    findings: list[Finding] = []

    # --- URLs ---------------------------------------------------------------
    for url in sorted(set(postparse.urls(body))):
        host = (urllib.parse.urlsplit(url).hostname or "").lower().removeprefix("www.")
        gated = host in GATED_HOSTS
        unsafe = _safe(url)
        if unsafe:
            findings.append(Finding(rel, gated, unsafe))
            continue
        # doi.org answers registered/unregistered without following the redirect,
        # which sidesteps the publisher WAF behind it.
        follow = host not in ("doi.org", "dx.doi.org")
        code, note = status(url, follow=follow)
        if code in (404, 410):
            findings.append(Finding(rel, gated, f"{code} {url}"))
        elif code is None:
            findings.append(Finding(rel, False, f"unreachable ({note}) {url}"))
        elif code >= 400:
            findings.append(Finding(rel, False, f"{code} {url}"))

    # --- arXiv titles -------------------------------------------------------
    entries: dict[str, str] = {}
    prose, refs = postparse.split_references(body)
    if refs:
        entries = postparse.parse_references(refs)
    if not entries:
        entries = {
            str(i): t for i, (_, t) in enumerate(postparse.split_sections(body))
        }

    wanted: dict[str, list[str]] = {}
    for label, entry in entries.items():
        for m in postparse.ARXIV_ID.finditer(entry):
            wanted.setdefault(m.group(1), []).append(entry)

    real = arxiv_titles(list(wanted))
    if wanted and not real:
        # arXiv rate-limits hard and intermittently. Treating "the API would not
        # answer" as "none of these papers exist" would fail every pull request
        # citing a preprint on a bad arXiv day, so skip rather than guess.
        return findings + [
            Finding(rel, False, "arXiv metadata unavailable; titles not verified")
        ]
    for ident, contexts in sorted(wanted.items()):
        if ident not in real:
            findings.append(Finding(rel, True, f"arXiv:{ident} is not a known arXiv paper"))
            continue
        quoted = [q for c in contexts for q in re.findall(r'"([^"]{8,})"', c)]
        # Also accept a nearby "## Heading" title, which is how briefs name items.
        quoted += [h for h, t in postparse.split_sections(body) if ident in t]
        if quoted and not any(titles_match(q.rstrip("."), real[ident]) for q in quoted):
            findings.append(
                Finding(
                    rel,
                    True,
                    f'arXiv:{ident} is "{real[ident]}", not {quoted[0][:60]!r}',
                )
            )
    return findings


def changed_files(base: str, head: str = "HEAD") -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=d", f"{base}...{head}", "--",
         "content/arxiv", "content/conferences", "content/deep-dives"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if out.returncode != 0:
        print(f"linkcheck: git diff failed: {out.stderr.strip()}", file=sys.stderr)
        return []
    return [ROOT / line for line in out.stdout.split() if line.endswith(".md")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--changed", action="store_true", help="files this branch touched")
    src.add_argument("--files", nargs="+", type=pathlib.Path)
    ap.add_argument("--base", default="main", help="ref to diff against (default main)")
    ap.add_argument(
        "--head",
        default="HEAD",
        help=(
            "ref to diff up to (default HEAD). auto-merge.yml runs this from a main "
            "checkout with the pull request's content files laid into the tree, so it "
            "needs to name a head other than the one on disk."
        ),
    )
    args = ap.parse_args(argv)

    targets = (
        changed_files(args.base, args.head)
        if args.changed
        else [p.resolve() for p in args.files]
    )
    targets = [p for p in targets if p.name != "_index.md" and p.exists()]
    if not targets:
        print("linkcheck: nothing to check")
        return 0

    findings: list[Finding] = []
    for path in targets:
        findings.extend(check_file(path))

    gating = [f for f in findings if f.gating]
    advisory = [f for f in findings if not f.gating]

    for f in advisory:
        print(f"  warn  {f.path}: {f.message}")
    for f in gating:
        print(f"  FAIL  {f.path}: {f.message}", file=sys.stderr)

    print(f"\nlinkcheck: {len(targets)} file(s), {len(gating)} failure(s), "
          f"{len(advisory)} warning(s)")
    if gating:
        print(
            "A gating failure means a DOI or arXiv ID does not resolve, or resolves to "
            "a different paper than the one cited. Find the real identifier or drop the "
            "reference; do not adjust it until it looks right.",
            file=sys.stderr,
        )
    return 1 if gating else 0


if __name__ == "__main__":
    sys.exit(main())
