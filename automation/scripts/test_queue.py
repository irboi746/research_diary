#!/usr/bin/env python3
"""Offline checks for queue.py.

The cases are the ones that actually cost something when wrong: a batch larger
than the configured ceiling, an item that comes back after being written up, the
same paper queued twice under two URL spellings, and a state file whose ordering
is unstable enough to conflict on every concurrent pull request.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import queue as Q  # noqa: E402

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}\n      got:  {got!r}\n      want: {want!r}")


def check_true(label: str, got) -> None:
    if not got:
        FAILURES.append(label)


TMP = pathlib.Path(tempfile.mkdtemp(prefix="queue-test-")) / "backlog.ndjson"

WOOT = "https://www.usenix.org/conference/woot26/presentation/"

records: list[dict] = []
for i in range(20):
    records, _ = Q.enqueue(records, f"{WOOT}author{i:02d}", title=f"Paper {i:02d}", venue="USENIX WOOT")
for i in range(3):
    records, _ = Q.enqueue(records, f"https://www.ndss-symposium.org/ndss2026/paper{i}", venue="NDSS")
Q.save(records, TMP)

check("every enqueued item is stored", len(Q.load(TMP)), 23)
check("everything starts pending", len(Q.pending(Q.load(TMP))), 23)

# --- idempotency -------------------------------------------------------------
# Identity comes from idstate.canonical, so URL spelling must not create a second
# entry -- a conference page linking the same talk twice is routine.
records = Q.load(TMP)
records, again = Q.enqueue(records, f"{WOOT}author00")
check("re-enqueueing the same URL adds nothing", again, False)
records, variant = Q.enqueue(records, "https://usenix.org/conference/woot26/presentation/author00/")
check("a normalised URL variant is the same item", variant, False)
check("no duplicate was appended", len(records), 23)

# --- batching ----------------------------------------------------------------
check("batch size comes from brief_max_summarized", Q.batch_size(), 8)

records = Q.load(TMP)
sizes = []
guard = 0
while Q.pending(records) and guard < 50:
    guard += 1
    batch = Q.pending(records)[: Q.batch_size()]
    sizes.append(len(batch))
    records, _ = Q.mark(records, [b["url"] for b in batch], Q.DONE)
    Q.save(records, TMP)
    records = Q.load(TMP)

check("23 items drain in 3 runs of at most 8", sizes, [8, 8, 7])
check_true("no batch ever exceeds the ceiling", all(n <= 8 for n in sizes))
check("the queue is empty once drained", len(Q.pending(records)), 0)
check_true("a drained item does not come back", all(r["status"] == Q.DONE for r in records))
check_true("closing stamps a date", all("closed" in r for r in records))

# --- venue filtering ---------------------------------------------------------
records = []
for i in range(5):
    records, _ = Q.enqueue(records, f"{WOOT}v{i}", venue="USENIX WOOT")
for i in range(4):
    records, _ = Q.enqueue(records, f"https://www.sigsac.org/ccs/CCS2026/p{i}", venue="ACM CCS")
check("venue filter selects only that venue", len(Q.pending(records, "ACM CCS")), 4)
check("venue filter is case-insensitive", len(Q.pending(records, "acm ccs")), 4)
check("an unknown venue yields nothing", len(Q.pending(records, "NDSS")), 0)

# --- skip --------------------------------------------------------------------
records, changed = Q.mark(records, [f"{WOOT}v0"], Q.SKIPPED, reason="no technical detail")
check("skipping marks exactly one item", changed, 1)
check("a skipped item leaves the pending set", len(Q.pending(records, "USENIX WOOT")), 4)
check_true(
    "the skip reason is recorded",
    any(r.get("reason") == "no technical detail" for r in records),
)
records, changed_again = Q.mark(records, [f"{WOOT}v0"], Q.SKIPPED)
check("marking an already-skipped item changes nothing", changed_again, 0)

# --- file format -------------------------------------------------------------
# Sorted, one object per line, keys sorted: the same discipline idstate.save()
# uses, so two concurrent pull requests touching the backlog rarely conflict.
Q.save(records, TMP)
first = TMP.read_text()
Q.save(Q.load(TMP), TMP)
check("saving a loaded file reproduces it byte for byte", TMP.read_text(), first)

lines = first.strip().split("\n")
keys = [json.loads(ln)["key"] for ln in lines]
check("records are written in key order", keys, sorted(keys))
check_true("each line is one JSON object", all(ln.startswith("{") and ln.endswith("}") for ln in lines))
check_true(
    "keys within a record are sorted",
    all(list(json.loads(ln)) == sorted(json.loads(ln)) for ln in lines),
)

# --- robustness --------------------------------------------------------------
# This file is edited by an agent and lands in pull requests, so a malformed line
# must cost that line and not the whole backlog.
BAD = TMP.parent / "bad.ndjson"
BAD.write_text(
    '{"key": "a", "status": "pending", "url": "https://x.tld/a"}\n'
    "not json at all\n"
    '{"no_key": true}\n'
    "\n"
    '{"key": "b", "status": "pending", "url": "https://x.tld/b"}\n',
    encoding="utf-8",
)
check("malformed and keyless lines are skipped, the rest survive", len(Q.load(BAD)), 2)

MISSING = TMP.parent / "does-not-exist.ndjson"
check("a missing state file is an empty backlog, not an error", Q.load(MISSING), [])

# A record with no explicit status is treated as pending rather than invisible.
LEGACY = TMP.parent / "legacy.ndjson"
LEGACY.write_text('{"key": "c", "url": "https://x.tld/c"}\n', encoding="utf-8")
check("a record with no status counts as pending", len(Q.pending(Q.load(LEGACY))), 1)

if FAILURES:
    print(f"queue: FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("queue: all checks passed")
