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

# --- RSS path ----------------------------------------------------------------
# Every shape below is one rss.arxiv.org actually emits. The announce_type set is
# the important one: the live cs.CR feed carries four values, and an allowlist
# that only knew three let "replace-cross" through as a first announcement.
from arxiv import parse_feed, _feed_identifier, DEFAULT_ANNOUNCE_TYPES  # noqa: E402
import xml.etree.ElementTree as _ET  # noqa: E402

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:arxiv="http://arxiv.org/schemas/atom"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>cs.CR updates on arXiv.org</title>
  <pubDate>Tue, 15 Sep 2026 00:00:00 -0400</pubDate>
  <item>
    <title>A Practical Attack on Some Deployed Protocol</title>
    <link>https://arxiv.org/abs/2609.13353</link>
    <description>arXiv:2609.13353v1 Announce Type: new 
Abstract: We show that the thing is broken.</description>
    <guid>oai:arXiv.org:2609.13353v1</guid>
    <category>cs.CR</category>
    <category>cs.NI</category>
    <arxiv:announce_type>new</arxiv:announce_type>
    <dc:creator>Ada Lovelace, Grace Hopper</dc:creator>
  </item>
  <item>
    <title>Cross Listed Work</title>
    <link>https://arxiv.org/abs/2609.10000</link>
    <description>arXiv:2609.10000v2 Announce Type: cross 
Abstract: Cross posted.</description>
    <guid>oai:arXiv.org:2609.10000v2</guid>
    <category>cs.CR</category>
    <arxiv:announce_type>cross</arxiv:announce_type>
    <dc:creator>Solo Author</dc:creator>
  </item>
  <item>
    <title>A Revision Of Something Already Covered</title>
    <link>https://arxiv.org/abs/2609.20000</link>
    <description>arXiv:2609.20000v3 Announce Type: replace 
Abstract: Now with more.</description>
    <guid>oai:arXiv.org:2609.20000v3</guid>
    <category>cs.CR</category>
    <arxiv:announce_type>replace</arxiv:announce_type>
    <dc:creator>Someone Else</dc:creator>
  </item>
  <item>
    <title>A Revised Cross Listing</title>
    <link>https://arxiv.org/abs/2609.30000</link>
    <description>arXiv:2609.30000v2 Announce Type: replace-cross 
Abstract: Also a revision.</description>
    <guid>oai:arXiv.org:2609.30000v2</guid>
    <category>cs.CR</category>
    <arxiv:announce_type>replace-cross</arxiv:announce_type>
    <dc:creator>Another Person</dc:creator>
  </item>
  <item>
    <title>Legacy Identifier Paper</title>
    <link>https://arxiv.org/abs/hep-ex/0307015</link>
    <description>arXiv:hep-ex/0307015v1 Announce Type: new 
Abstract: Old style id.</description>
    <guid>oai:arXiv.org:hep-ex/0307015v1</guid>
    <category>hep-ex</category>
    <arxiv:announce_type>new</arxiv:announce_type>
    <dc:creator>Vintage Author</dc:creator>
  </item>
</channel>
</rss>
"""

feed_rows = parse_feed(FEED)
check("default announce types keep only new and cross", len(feed_rows), 3)
check_true(
    "replace and replace-cross are both excluded by default",
    not any(r["announce_type"].startswith("replace") for r in feed_rows),
)
check("DEFAULT_ANNOUNCE_TYPES is new and cross", DEFAULT_ANNOUNCE_TYPES, ("new", "cross"))

f = feed_rows[0]
check("rss strips the version suffix", f["id"], "2609.13353")
check("rss builds a canonical abs url", f["url"], "https://arxiv.org/abs/2609.13353")
check("rss strips the Announce Type preamble", f["summary"], "We show that the thing is broken.")
check("rss splits dc:creator into authors", f["authors"], ["Ada Lovelace", "Grace Hopper"])
check("rss keeps every category", f["categories"], ["cs.CR", "cs.NI"])
check("rss falls back to the channel pubDate", f["published"], "Tue, 15 Sep 2026 00:00:00 -0400")

check(
    "rss handles legacy identifiers",
    [r["id"] for r in parse_feed(FEED, ("new",))][-1],
    "hep-ex/0307015",
)
check(
    "an explicit announce type selection is honoured",
    sorted(r["id"] for r in parse_feed(FEED, ("replace", "replace-cross"))),
    ["2609.20000", "2609.30000"],
)
check("an empty announce filter keeps everything", len(parse_feed(FEED, ())), 5)

# Same contract the Atom path is held to: RSS ids must agree with idstate, or the
# same paper dedups as two records depending on which tier found it.
check_true(
    "rss ids agree with idstate.py canonical form",
    all(canonical(r["url"]) == ("arxiv", r["id"]) for r in parse_feed(FEED, ())),
)
check_true(
    "rss and atom produce the same key set",
    set(parse_feed(FEED, ())[0]) - {"announce_type"} == set(rows[0]),
)

# The id has to survive a missing or malformed description: the feed is the one
# compulsory source, and one bad field must not cost the item.
_items = _ET.fromstring(FEED).find("channel").findall("item")
check("id falls back to guid when description is unusable", _feed_identifier(_items[0]), "2609.13353")

_no_desc = _ET.fromstring(
    b'<item><guid>oai:arXiv.org:2609.13353v1</guid>'
    b'<link>https://arxiv.org/abs/2609.13353</link></item>'
)
check("id recovered from guid alone", _feed_identifier(_no_desc), "2609.13353")

_link_only = _ET.fromstring(b'<item><link>https://arxiv.org/abs/2609.13353v2</link></item>')
check("id recovered from link alone", _feed_identifier(_link_only), "2609.13353")

check("an item with no usable id is dropped, not crashed on",
      parse_feed(b'<rss><channel><item><title>x</title>'
                 b'<arxiv:announce_type xmlns:arxiv="http://arxiv.org/schemas/atom">new'
                 b'</arxiv:announce_type></item></channel></rss>'), [])
check("an empty rss document parses to nothing", parse_feed(b"<rss><channel/></rss>"), [])
check("a document with no channel parses to nothing", parse_feed(b"<rss/>"), [])

if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("arxiv: all checks passed")
