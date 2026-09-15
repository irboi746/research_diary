#!/usr/bin/env python3
"""Rank candidates against the `interests` and `reject` lists in topics.toml.

What this is, precisely: a triage ordering, not a judgement. It is term overlap
between a paper's title and abstract and the phrases in topics.toml. It cannot
tell a real mitigation bypass from a paper that merely says "mitigation bypass",
and it has no idea whether a result is any good.

So it never drops anything. It attaches a score and the reasons for that score,
and the items come out in order; Jules still reads them and still decides.

The `reject` list needs saying plainly, because most of it is not mechanisable
from a title and an abstract:

  - "withdrawn or superseded by a newer version already covered" is enforced for
    real, upstream, by arxiv.py's announce_type filter.
  - "already covered under a different URL or venue" is enforced for real by
    idstate.py's dedup.
  - The other six are editorial judgements. Measured against 400 live feed items,
    their wording shares almost no vocabulary with abstracts -- every entry had a
    median term overlap of 0.00 -- so scoring them as prose fires never, and any
    threshold low enough to fire is low enough to reject good work silently.

What this does instead is flag, and only down-weight: an entry is flagged when at
least two of its *discriminating* terms co-occur -- terms that appear in the
reject list and in none of the interests, so they are the vocabulary that
actually separates the two. That is sparse in practice (0-8 hits per entry across
those 400 items) and it is visible in the output. It is a hint for Jules, not a
verdict, and the full reject list stays Jules' to apply.

Stdlib only: this runs in the Jules VM, in CI, and in the tests, and none of
those should need an install for something this simple.

Usage:
    arxiv.py --json | rank.py
    arxiv.py --json | rank.py --top 8 --json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tomllib

CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config" / "topics.toml"

# Words carrying no topical signal. Without this every paper scores for "and",
# and the security vocabulary itself ("security", "attack") is so universal on
# cs.CR that it orders nothing -- 129 of 129 items match it.
STOPWORDS = frozenset("""
a an and are as at be been between by for from in into is it its of on onto or over
that the their them then there these this through to under up upon use used using
via with within without where whether which while who whom whose new newer already
just not no nor but can could may might must shall should will would do does did
than more most other others such same own very each any all both few some only
attack attacks attacking security secure paper work results result approach method
methods system systems model models based novel we our us they
""".split())

WORD = re.compile(r"[a-z0-9][a-z0-9+#.\-]*")
# Phrases worth matching whole. Splitting an interest on commas and colons gives
# back the concept list it was written as; a phrase hit is stronger evidence than
# the same words scattered across an abstract.
SPLIT = re.compile(r"[,;:—–\-]{1,2}\s|\s[—–]\s|[,;:]")

TITLE_WEIGHT = 3.0
PHRASE_WEIGHT = 4.0
TERM_WEIGHT = 1.0
REJECT_WEIGHT = 2.5
# How many discriminating terms must co-occur before an item is flagged. One is
# far too eager: "detection" alone appears in a large share of cs.CR abstracts.
REJECT_MIN_TERMS = 2


def load_config(path: pathlib.Path | None = None) -> dict:
    with (path or CONFIG).open("rb") as fh:
        return tomllib.load(fh)


def terms(text: str) -> set[str]:
    """Content words, lowercased, stopwords and one-character tokens removed."""
    return {
        w for w in WORD.findall(text.lower())
        if len(w) > 2 and w not in STOPWORDS
    }


def phrases(entry: str) -> list[str]:
    """Multi-word concepts inside one interest line, normalised for matching."""
    out = []
    for chunk in SPLIT.split(entry.lower()):
        words = [w for w in WORD.findall(chunk) if w not in STOPWORDS and len(w) > 2]
        if len(words) >= 2:
            out.append(" ".join(words))
    return out


def compile_profile(cfg: dict) -> dict:
    """Pre-compute the term and phrase sets once, rather than per candidate.

    Reject entries keep only their *discriminating* terms: the ones that appear
    nowhere in `interests`. Shared vocabulary ("attack", "vulnerability") would
    otherwise make every in-scope paper look like a rejection.
    """
    interests = [
        {"text": entry, "terms": terms(entry), "phrases": phrases(entry)}
        for entry in cfg.get("interests", [])
    ]
    interest_vocab: set[str] = set()
    for entry in interests:
        interest_vocab |= entry["terms"]

    rejects = []
    for entry in cfg.get("reject", []):
        discriminating = terms(entry) - interest_vocab
        if discriminating:
            rejects.append({"text": entry, "terms": discriminating})
    return {"interests": interests, "rejects": rejects}


def _hits(haystack_terms: set[str], normalised_text: str, entry: dict) -> tuple[float, list[str]]:
    score = 0.0
    why: list[str] = []
    for phrase in entry["phrases"]:
        if phrase in normalised_text:
            score += PHRASE_WEIGHT
            why.append(phrase)
    overlap = haystack_terms & entry["terms"]
    score += TERM_WEIGHT * len(overlap)
    return score, why


def _normalise(text: str) -> str:
    return " ".join(WORD.findall(text.lower()))


def score(record: dict, profile: dict) -> dict:
    """Return the record with `score`, `matched` and `flagged` attached.

    Title and abstract are scored separately so that a paper *about* the topic
    outranks one that mentions it once in related work.
    """
    title = record.get("title", "") or ""
    summary = record.get("summary", "") or ""
    title_terms, body_terms = terms(title), terms(summary)
    title_norm, body_norm = _normalise(title), _normalise(summary)

    total = 0.0
    matched: list[str] = []
    for entry in profile["interests"]:
        t_score, t_why = _hits(title_terms, title_norm, entry)
        b_score, b_why = _hits(body_terms, body_norm, entry)
        entry_score = TITLE_WEIGHT * t_score + b_score
        if entry_score > 0:
            total += entry_score
            matched.append(entry["text"])
        del t_why, b_why

    flagged: list[str] = []
    seen_terms = title_terms | body_terms
    for entry in profile["rejects"]:
        overlap = seen_terms & entry["terms"]
        if len(overlap) >= REJECT_MIN_TERMS:
            flagged.append(entry["text"])
            # Down-weight, never drop. A wrong rejection that happens quietly is
            # worse than a wrong ordering, which is visible in the output.
            total -= REJECT_WEIGHT * len(overlap)

    out = dict(record)
    out["score"] = round(total, 2)
    out["matched"] = matched
    out["flagged"] = flagged
    return out


def rank(records: list[dict], profile: dict) -> list[dict]:
    """Highest score first; ties broken by id so the order is reproducible."""
    scored = [score(r, profile) for r in records]
    scored.sort(key=lambda r: (-r["score"], r.get("id", "")))
    return scored


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--top", type=int, help="print only the highest scoring N")
    ap.add_argument("--json", action="store_true", help="emit JSON lines instead of TSV")
    args = ap.parse_args(argv)

    records = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warning: skipping unparseable line: {line[:80]!r}", file=sys.stderr)

    ordered = rank(records, compile_profile(load_config()))
    if args.top:
        ordered = ordered[: args.top]

    for r in ordered:
        if args.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            flag = f"  [flagged: {len(r['flagged'])}]" if r["flagged"] else ""
            print(f"{r['score']:8.2f}  {r['id']}  {r['title'][:88]}{flag}")

    print(f"# {len(ordered)} ranked", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
