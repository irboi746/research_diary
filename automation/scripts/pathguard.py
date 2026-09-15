#!/usr/bin/env python3
"""Reject generated changes that touch anything outside the content allowlist.

The pipeline's entire input is untrusted: paper text, conference slides and web
pages, fed to an agent that has write access to this repository and can execute
code. A poisoned document that talks the agent into editing a workflow file would
otherwise be merged automatically.

So the trust boundary is here, not in the prompt. Whatever the agent was told or
talked into, a pull request may only change:

    content/arxiv/**           the arXiv briefs
    content/news/**            the conference briefs
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
    # Only Markdown under the three content sections. Hugo serves a .html file
    # in content/ verbatim, without Goldmark, so an allowlist that matched any
    # extension would hand the agent a raw-HTML publishing primitive that
    # validate.py never sees — it only globs *.md.
    "content/arxiv/*.md",
    "content/news/*.md",
    "content/research/*.md",
    "automation/state/*",
)

# git's blob mode for an ordinary file. Anything else is refused: 120000 is a
# symlink (content/news/post.md pointing at a workflow, so a later write escapes
# the allowlist), 160000 a submodule gitlink, 100755 an executable bit on a file
# CI runs. 000000 means the side does not exist — an add or a delete.
REGULAR = "100644"
ABSENT = "000000"


def allowed(path: str) -> bool:
    p = path
    # Strip a leading "./" prefix only. lstrip("./") would strip character *sets*
    # and turn "../../etc/passwd" into "etc/passwd", defeating the check below.
    while p.startswith("./"):
        p = p[2:]
    if not p or p.startswith("/"):
        return False
    # Backslash counts as a separator: split("/") alone sees no ".." in
    # "content/news/..\..\go.mod", which git would honour on a Windows checkout.
    if ".." in p.replace("\\", "/").split("/"):
        return False
    return any(fnmatch.fnmatch(p, pattern) for pattern in ALLOWED)


def changed_files(base: str, head: str = "HEAD") -> list[str]:
    """Every path this branch touches, plus both sides of any rename.

    --name-only prints only the *destination* of a detected rename, so
    `git mv .github/workflows/pages.yml content/news/x.md` would look like one
    allowed path while the workflow silently disappeared. --raw reports both
    names and both blob modes; -z keeps paths intact when they contain a newline
    or a quotable byte, which --name-only would have C-quoted or split.
    """
    # Three-dot: what this branch changed relative to the merge base, so unrelated
    # commits landing on the base branch are not attributed to this pull request.
    out = subprocess.run(
        ["git", "diff", "--raw", "-M", "-z", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return _parse_raw(out)


def _parse_raw(out: str) -> list[str]:
    """Parse `git diff --raw -z` into the paths to judge.

    Each record is ":<srcmode> <dstmode> <srcsha> <dstsha> <status>" then the
    path, or two paths when the status is R or C. A bad mode is reported as a
    pseudo-path so it shows up as a denial rather than passing silently.
    """
    fields = [f for f in out.split("\0") if f != ""]
    paths: list[str] = []
    i = 0
    while i < len(fields):
        meta = fields[i]
        if not meta.startswith(":"):
            # Should not happen; judge it as a path so we fail closed.
            paths.append(meta)
            i += 1
            continue
        parts = meta[1:].split()
        srcmode, dstmode, status = parts[0], parts[1], parts[4]
        npaths = 2 if status[:1] in ("R", "C") else 1
        here = fields[i + 1 : i + 1 + npaths]
        for mode in (srcmode, dstmode):
            if mode != ABSENT and mode != REGULAR:
                paths.append(f"<mode {mode}> {here[-1] if here else '?'}")
        paths.extend(here)
        i += 1 + npaths
    return paths


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--base", help="git ref to diff against, e.g. origin/main")
    src.add_argument("--files", nargs="+", help="explicit list of paths")
    src.add_argument("--stdin", action="store_true", help="read paths from stdin")
    ap.add_argument(
        "--head",
        default="HEAD",
        help=(
            "ref to diff up to (default HEAD). auto-merge.yml runs this script "
            "from a main checkout against a fetched pull-request ref, so it needs "
            "to name a head other than the one on disk."
        ),
    )
    args = ap.parse_args(argv)

    if args.base:
        try:
            files = changed_files(args.base, args.head)
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
            "Generated content may only touch content/arxiv/, content/news/,\n"
            "content/research/ and automation/state/. This pull request needs a\n"
            "human to look at it.",
            file=sys.stderr,
        )
        return 1

    print(f"\npathguard: {len(files)} file(s) within the allowlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
