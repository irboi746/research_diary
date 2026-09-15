#!/usr/bin/env python3
"""Backlog queue: drain a conference programme a few papers at a time.

A conference drops its whole programme at once. USENIX Security publishes several
hundred papers on one day; writing them up in a single run produces either one
unreadable post or, more likely, a run that quietly covers the first handful and
loses the rest -- arxiv.py printed its results and forgot them, and nothing
recorded what had not been reached yet.

So the backlog is state. Items are enqueued once, handed out in batches of
`brief_max_summarized` (8), and marked done as they are written up. A weekly run
takes the next batch; the venue is exhausted when the queue is empty. Nothing is
lost if a run fails halfway, because leasing is not destructive -- an item only
leaves `pending` when something explicitly marks it done or skipped.

This is a SEPARATE file from seen.ndjson on purpose. idstate.load() drops any
record without a "key" and warns on lines it cannot parse, so mixing a second
schema into that file would corrupt the dedup state. The two answer different
questions: seen.ndjson is "have we ever covered this?", backlog.ndjson is "what
is still waiting?".

State lives in automation/state/backlog.ndjson, one record per line, sorted by
key -- the same discipline idstate.py uses, and for the same reason: sorted NDJSON
keeps daily diffs small and makes conflicts between concurrent pull requests
trivial. Both are already inside pathguard's `automation/state/*` allowlist, so
no allowlist change was needed to add this.

Usage:
    queue.py enqueue <url> [--title T] [--venue V]   # idempotent
    queue.py enqueue --stdin < urls.txt
    queue.py next [--limit 8] [--venue V] [--json]   # peek at the next batch
    queue.py done <url> [<url> ...]                  # written up
    queue.py skip <url> --reason "..."               # rejected, do not resurface
    queue.py stats
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import tomllib

import idstate

STATE = pathlib.Path(__file__).resolve().parents[1] / "state" / "backlog.ndjson"
CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config" / "topics.toml"

PENDING, DONE, SKIPPED = "pending", "done", "skipped"
STATUSES = (PENDING, DONE, SKIPPED)
DEFAULT_LIMIT = 8


def batch_size() -> int:
    """The batch is `brief_max_summarized`, not a second constant.

    Two numbers that must agree and are written down twice eventually disagree.
    """
    try:
        with CONFIG.open("rb") as fh:
            return int(tomllib.load(fh).get("brief_max_summarized", DEFAULT_LIMIT))
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return DEFAULT_LIMIT


def load(path: pathlib.Path | None = None) -> list[dict]:
    path = path or STATE
    if not path.exists():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(f"warning: {path.name}:{n} is not JSON, skipping", file=sys.stderr)
            continue
        if not isinstance(record, dict) or "key" not in record:
            print(f"warning: {path.name}:{n} has no key, skipping", file=sys.stderr)
            continue
        out.append(record)
    return out


def save(records: list[dict], path: pathlib.Path | None = None) -> None:
    path = path or STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, sort_keys=True)
        for r in sorted(records, key=lambda r: r["key"])
    ]
    path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def enqueue(records: list[dict], target: str, title: str = "", venue: str = "") -> tuple[list[dict], bool]:
    """Add one item. Returns (records, added). Idempotent on canonical identity.

    Identity comes from idstate.canonical, so the same paper arriving as /abs/
    and /pdf/, or as v1 and v2, is one queue entry rather than two.
    """
    kind, key = idstate.canonical(target)
    if any(r["key"] == key for r in records):
        return records, False
    records.append(
        {
            "key": key,
            "kind": kind,
            "url": target,
            "title": title,
            "venue": venue,
            "status": PENDING,
            "first_seen": _today(),
        }
    )
    return records, True


def pending(records: list[dict], venue: str = "") -> list[dict]:
    """Pending items, oldest enqueue first so a backlog drains in order."""
    items = [r for r in records if r.get("status", PENDING) == PENDING]
    if venue:
        items = [r for r in items if r.get("venue", "").lower() == venue.lower()]
    return sorted(items, key=lambda r: (r.get("first_seen", ""), r["key"]))


def mark(records: list[dict], targets: list[str], status: str, reason: str = "") -> tuple[list[dict], int]:
    keys = {idstate.canonical(t)[1] for t in targets}
    changed = 0
    for record in records:
        if record["key"] in keys and record.get("status") != status:
            record["status"] = status
            record["closed"] = _today()
            if reason:
                record["reason"] = reason
            changed += 1
    return records, changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("enqueue", help="add an item to the backlog")
    p_add.add_argument("target", nargs="?", help="URL or identifier")
    p_add.add_argument("--stdin", action="store_true", help="read one URL per line")
    p_add.add_argument("--title", default="")
    p_add.add_argument("--venue", default="")

    p_next = sub.add_parser("next", help="show the next batch without changing state")
    p_next.add_argument("--limit", type=int, default=None, help="default: brief_max_summarized")
    p_next.add_argument("--venue", default="")
    p_next.add_argument("--json", action="store_true")

    p_done = sub.add_parser("done", help="mark items as written up")
    p_done.add_argument("targets", nargs="+")

    p_skip = sub.add_parser("skip", help="mark items as rejected")
    p_skip.add_argument("targets", nargs="+")
    p_skip.add_argument("--reason", default="")

    sub.add_parser("stats", help="counts by status and venue")
    args = ap.parse_args(argv)

    records = load()

    if args.cmd == "enqueue":
        targets = []
        if args.stdin:
            targets = [ln.strip() for ln in sys.stdin if ln.strip() and not ln.startswith("#")]
        elif args.target:
            targets = [args.target]
        else:
            print("error: give a target or --stdin", file=sys.stderr)
            return 2
        added = 0
        for target in targets:
            records, was_added = enqueue(records, target, args.title, args.venue)
            added += was_added
        save(records)
        print(f"enqueued {added} new, {len(targets) - added} already queued")
        return 0

    if args.cmd == "next":
        limit = args.limit if args.limit is not None else batch_size()
        items = pending(records, args.venue)[:limit]
        for item in items:
            if args.json:
                print(json.dumps(item, ensure_ascii=False, sort_keys=True))
            else:
                print(f"{item['key']}\t{item.get('venue','')}\t{item.get('title','')}\t{item['url']}")
        remaining = len(pending(records, args.venue))
        print(
            f"# {len(items)} of {remaining} pending"
            f"{' for ' + args.venue if args.venue else ''}"
            f"; {max(0, remaining - len(items))} left after this batch",
            file=sys.stderr,
        )
        return 0

    if args.cmd in ("done", "skip"):
        status = DONE if args.cmd == "done" else SKIPPED
        records, changed = mark(records, args.targets, status, getattr(args, "reason", ""))
        save(records)
        print(f"marked {changed} item(s) {status}")
        return 0

    counts: dict[str, int] = {}
    venues: dict[str, int] = {}
    for record in records:
        status = record.get("status", PENDING)
        counts[status] = counts.get(status, 0) + 1
        if status == PENDING:
            venues[record.get("venue", "?")] = venues.get(record.get("venue", "?"), 0) + 1
    print(f"backlog: {len(records)} item(s) in {STATE}")
    for status in STATUSES:
        print(f"  {status:<8} {counts.get(status, 0)}")
    if venues:
        print("pending by venue:")
        for venue, n in sorted(venues.items(), key=lambda kv: -kv[1]):
            print(f"  {venue or '?':<40} {n}")
    print(f"batch size: {batch_size()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
