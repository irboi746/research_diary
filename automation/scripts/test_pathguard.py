#!/usr/bin/env python3
"""Tests for the content path allowlist.

Run: python3 automation/scripts/test_pathguard.py

This is the injection defence: it is what stops a poisoned paper from talking the
agent into editing a workflow file and having it auto-merged. Test it before
trusting it.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from pathguard import allowed  # noqa: E402

FAILURES: list[str] = []

ALLOW = [
    "content/news/2026-09-15-daily-brief.md",
    "content/news/nested/thing.md",
    "content/research/2026-09-15-some-topic.md",
    "automation/state/seen.ndjson",
    "./content/news/2026-09-15-daily-brief.md",
]

DENY = [
    # Workflow and config tampering — the thing this exists to stop.
    ".github/workflows/pages.yml",
    ".github/workflows/validate-content.yml",
    "config.toml",
    "go.mod",
    "AGENTS.md",
    "CLAUDE.md",
    # The guard and its inputs must not be editable by the thing it guards.
    "automation/scripts/pathguard.py",
    "automation/scripts/validate.py",
    "automation/config/topics.toml",
    # Traversal.
    "../../etc/passwd",
    "content/news/../../../etc/passwd",
    "/etc/passwd",
    # Near-misses that must not be confused for the allowed prefixes.
    "content/newsletter/x.md",
    "content/about.md",
    "automation/statecraft/x",
    "",
]

for p in ALLOW:
    if not allowed(p):
        FAILURES.append(f"should be ALLOWED but was denied: {p!r}")

for p in DENY:
    if allowed(p):
        FAILURES.append(f"should be DENIED but was allowed: {p!r}")

if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print(f"pathguard: all {len(ALLOW) + len(DENY)} checks passed")
