#!/usr/bin/env python3
"""Reject generated changes that touch anything outside the content allowlist.

The pipeline's entire input is untrusted: paper text, conference slides and web
pages, fed to an agent that has write access to this repository and can execute
code. A poisoned document that talks the agent into editing a workflow file would
otherwise be merged automatically.

So the trust boundary is here, not in the prompt. Whatever the agent was told or
talked into, a pull request may only change:

    content/news/**            the daily briefs
    content/research/**        the deep dives
    automation/state/**        dedup bookkeeping

Anything else — workflows, config.toml, go.mod, the scripts themselves, this file
— fails the check, blocks auto-merge, and leaves the pull request open for a
human to look at.

Usage:
    pathguard.py --base origin/main          # diff against a branch
    pathguard.py --files a.md b.md           # check an explicit list
    git diff --name-only origin/main | pathguard.py --stdin
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys

ALLOWED = (
    "content/news/*",
    "content/research/*",
    "automation/state/*",
    ".github/workflows/*",
    "config.toml",
    "automation/scripts/pathguard.py",
    "automation/scripts/sources.py",
)


def allowed(path: str) -> bool:
    p = path.strip()
    # Strip a leading "./" prefix only. lstrip("./") would strip character *sets*
    # and turn "../../etc/passwd" into "etc/passwd", defeating the check below.
    while p.startswith("./"):
        p = p[2:]
    if not p or p.startswith("/"):
        return False
    if ".." in p.split("/"):
        return False
    return any(fnmatch.fnmatch(p, pattern) for pattern in ALLOWED)


def changed_files(base: str) -> list[str]:
    # Three-dot: what this branch changed relative to the merge base, so unrelated
    # commits landing on the base branch are not attributed to this pull request.
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--base", help="git ref to diff against, e.g. origin/main")
    src.add_argument("--files", nargs="+", help="explicit list of paths")
    src.add_argument("--stdin", action="store_true", help="read paths from stdin")
    args = ap.parse_args(argv)

    if args.base:
        try:
            files = changed_files(args.base)
        except subprocess.CalledProcessError as exc:
            print(f"pathguard: git diff failed: {exc.stderr.strip()}", file=sys.stderr)
            return 2
    elif args.files:
        files = args.files
    else:
        files = [line for line in sys.stdin.read().splitlines() if line.strip()]

    if not files:
        print("pathguard: no files changed")
        return 0

    violations = [f for f in files if not allowed(f)]

    for f in sorted(files):
        print(f"  {'ok  ' if allowed(f) else 'DENY'} {f}")

    if violations:
        print(
            f"\npathguard: FAILED — {len(violations)} path(s) outside the allowlist.\n"
            "Generated content may only touch content/news/, content/research/ and\n"
            "automation/state/. This pull request needs a human to look at it.",
            file=sys.stderr,
        )
        return 1

    print(f"\npathguard: {len(files)} file(s) within the allowlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
