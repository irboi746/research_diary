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

from pathguard import ALLOWED, _parse_raw, allowed  # noqa: E402

FAILURES: list[str] = []

# The allowlist itself is pinned, not just sampled. Asserting on example paths is
# not enough: an agent that widens ALLOWED can also add the new path to the ALLOW
# list below and leave the suite green. That is exactly what happened in a79aa37
# and 990b2d8. Changing this tuple has to be a deliberate edit to this line.
EXPECTED_ALLOWLIST = (
    "content/arxiv/*.md",
    "content/news/*.md",
    "content/research/*.md",
    "automation/state/*",
)
if ALLOWED != EXPECTED_ALLOWLIST:
    FAILURES.append(
        f"pathguard.ALLOWED has been changed.\n"
        f"      expected: {EXPECTED_ALLOWLIST}\n"
        f"      found:    {ALLOWED}\n"
        "      Widening the allowlist is a human decision made in its own commit."
    )

ALLOW = [
    "content/arxiv/2026-09-15-arxiv-brief.md",
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
    ".github/workflows/auto-merge.yml",
    "config.toml",
    # General files that should remain blocked
    "go.mod",
    "AGENTS.md",
    "CLAUDE.md",
    # The guard, its test and its inputs must not be editable by the thing it
    # guards. A guard that can rewrite its own test is not a guard.
    "automation/scripts/pathguard.py",
    "automation/scripts/test_pathguard.py",
    "automation/scripts/validate.py",
    "automation/scripts/sources.py",
    "automation/scripts/linkcheck.py",
    "automation/scripts/postparse.py",
    "automation/config/topics.toml",
    # Traversal.
    "../../etc/passwd",
    "content/news/../../../etc/passwd",
    "/etc/passwd",
    # Backslash traversal: split("/") alone does not see the "..".
    "content/news/..\\..\\go.mod",
    # Near-misses that must not be confused for the allowed prefixes.
    "content/newsletter/x.md",
    "content/arxivfoo/x.md",
    "content/arxiv.md",
    "content/about.md",
    "automation/statecraft/x",
    "",
    # Non-Markdown under content/. Hugo publishes a .html content file verbatim,
    # bypassing Goldmark, and validate.py only ever globs *.md — so these would
    # be raw, unvalidated output on the live site.
    "content/news/evil.html",
    "content/news/evil.js",
    "content/news/.gitattributes",
    "content/research/x.xml",
    "content/arxiv/evil.html",
    "content/arxiv/x.xml",
    # Whitespace must not be normalised away: a file really named "config.toml "
    # is a different path from "config.toml", and judging the stripped string
    # would let the real one through under the wrong verdict.
    " config.toml",
    "config.toml ",
]

for p in ALLOW:
    if not allowed(p):
        FAILURES.append(f"should be ALLOWED but was denied: {p!r}")

for p in DENY:
    if allowed(p):
        FAILURES.append(f"should be DENIED but was allowed: {p!r}")


def check_raw(label: str, raw: str, must_deny: str) -> None:
    """Assert that parsing `git diff --raw -z` output surfaces a denied path."""
    paths = _parse_raw(raw)
    if not any(must_deny in p for p in paths):
        FAILURES.append(f"{label}: {must_deny!r} not surfaced; got {paths!r}")
    if all(allowed(p) for p in paths):
        FAILURES.append(f"{label}: every path passed the guard; got {paths!r}")


# A rename out of a protected path. --name-only would have printed only the
# destination, so the workflow's disappearance was invisible to the guard.
check_raw(
    "rename hides the source",
    ":100644 100644 aaaa bbbb R100\0.github/workflows/pages.yml\0"
    "content/news/2026-09-15-daily-brief.md\0",
    ".github/workflows/pages.yml",
)

# A symlink committed under an allowed path. The path alone is fine; the mode is
# what makes it an escape.
check_raw(
    "symlink mode is refused",
    ":000000 120000 0000 cccc A\0content/news/2026-09-15-daily-brief.md\0",
    "<mode 120000>",
)

# A submodule gitlink dropped into the content tree.
check_raw(
    "gitlink mode is refused",
    ":000000 160000 0000 dddd A\0content/news/sub\0",
    "<mode 160000>",
)

# chmod +x on a file CI executes.
check_raw(
    "exec bit is refused",
    ":100644 100755 eeee eeee M\0automation/scripts/validate.py\0",
    "<mode 100755>",
)

# An ordinary content edit must still come through clean.
plain = _parse_raw(":100644 100644 aaaa bbbb M\0content/news/2026-09-15-daily-brief.md\0")
if plain != ["content/news/2026-09-15-daily-brief.md"]:
    FAILURES.append(f"plain edit mis-parsed: {plain!r}")
if not all(allowed(p) for p in plain):
    FAILURES.append(f"plain content edit was denied: {plain!r}")

# A path containing a newline stays one path. Under --name-only this split into
# two fragments that were each judged separately.
nl = _parse_raw(":000000 100644 0000 ffff A\0content/news/a\nb.md\0")
if nl != ["content/news/a\nb.md"]:
    FAILURES.append(f"newline in path mis-parsed: {nl!r}")

if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print(
    f"pathguard: all {len(ALLOW) + len(DENY)} path checks "
    "plus the allowlist pin and 6 diff-parsing checks passed"
)
