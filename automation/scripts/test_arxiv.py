#!/usr/bin/env python3
"""Tests for arXiv query construction and Atom parsing.

Run: python3 automation/scripts/test_arxiv.py

Offline by design — it runs against a saved Atom response rather than the live
API, so it works in CI and in sandboxes whose address range arXiv rate-limits.
Live reachability is a separate, manual check (see AGENTS.md / README).
"""

import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from arxiv import build_query, parse, parse_since  # noqa: E402

FAILURES: list[str] = []


def check(name, got, want):
    if got != want:
        FAILURES.append(f"{name}\n     got:  {got!r}\n     want: {want!r}")


def check_true(name, cond):
    if not cond:
        FAILURES.append(name)


# --- query construction -----------------------------------------------------

start = dt.datetime(2026, 9, 12, 6, 0, tzinfo=dt.timezone.utc)
end = dt.datetime(2026, 9, 14, 6, 0, tzinfo=dt.timezone.utc)

check(
    "query joins categories with OR and bounds submittedDate",
    build_query(["cs.CR", "cs.AI"], start, end),
    "(cat:cs.CR OR cat:cs.AI) AND submittedDate:[202609120600 TO 202609140600]",
)

check("parse_since hours", parse_since("48h"), dt.timedelta(hours=48))
check("parse_since days", parse_since("7d"), dt.timedelta(days=7))

try:
    parse_since("banana")
    FAILURES.append("parse_since should reject a malformed window")
except Exception:
    pass

# --- Atom parsing -----------------------------------------------------------

ATOM_FIXTURE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2509.12345v2</id>
    <updated>2026-09-13T17:59:59Z</updated>
    <published>2026-09-12T08:30:00Z</published>
    <title>A Practical Attack on
      Some Deployed Protocol</title>
    <summary>  We show that the thing
      is broken.  </summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Grace Hopper</name></author>
    <category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.NI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/hep-ex/0307015v1</id>
    <published>2026-09-12T09:00:00Z</published>
    <updated>2026-09-12T09:00:00Z</updated>
    <title>A Legacy Identifier Paper</title>
    <summary>Older id scheme.</summary>
    <author><name>Alan Turing</name></author>
    <category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""

rows = parse(ATOM_FIXTURE)
check("parses both entries", len(rows), 2)

a = rows[0]
# The version suffix must be stripped here too, or the same paper reappears when
# a new version is posted.
check("strips version suffix from id", a["id"], "2509.12345")
check("builds a canonical abs url", a["url"], "https://arxiv.org/abs/2509.12345")
check(
    "collapses whitespace in multi-line titles",
    a["title"],
    "A Practical Attack on Some Deployed Protocol",
)
check("trims and collapses the summary", a["summary"], "We show that the thing is broken.")
check("extracts all authors", a["authors"], ["Ada Lovelace", "Grace Hopper"])
check("extracts all categories", a["categories"], ["cs.CR", "cs.NI"])
check("keeps published timestamp", a["published"], "2026-09-12T08:30:00Z")

check("handles legacy identifiers", rows[1]["id"], "hep-ex/0307015")

# The two scripts must agree on identity, or dedup silently fails across tiers.
from idstate import canonical  # noqa: E402

check_true(
    "arxiv.py ids agree with idstate.py canonical form",
    all(canonical(r["url"]) == ("arxiv", r["id"]) for r in rows),
)

check("empty feed parses to nothing", parse(b'<feed xmlns="http://www.w3.org/2005/Atom"/>'), [])

if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("arxiv: all checks passed")
