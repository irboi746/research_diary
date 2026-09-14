#!/usr/bin/env python3
"""Validate generated content against the contract in AGENTS.md.

Runs twice, deliberately: Jules runs it in its VM before finishing a task (fast
feedback), and CI runs it again on the pull request (the trust boundary — the VM
result is not evidence, since the agent could have skipped the step).

Frontmatter is TOML (+++ delimiters, which Hugo supports natively) so it parses
with stdlib tomllib. Hand-rolled YAML parsing is a well-known source of quoting
bugs, and this file is the thing standing between a malformed post and a silently
broken site.

Usage:
    validate.py                    # every file under content/news and content/research
    validate.py path/to/post.md    # specific files
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.toml"
SECTIONS = {"news": ROOT / "content" / "news", "research": ROOT / "content" / "research"}

FM = re.compile(r"\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n(.*)\Z", re.DOTALL)
SLUG = re.compile(r"\A[a-z0-9]+(?:-[a-z0-9]+)*\Z")
URL = re.compile(r"https?://[^\s<>()\[\]]+")

NEWS_NAME = re.compile(r"\A\d{4}-\d{2}-\d{2}-daily-brief\.md\Z")
RESEARCH_NAME = re.compile(r"\A\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md\Z")

MAX_SLUG_LEN = 60


class Problem(Exception):
    pass


def load_vocabulary() -> set[str]:
    with CONFIG.open("rb") as fh:
        return set(tomllib.load(fh).get("tags", []))


def split_frontmatter(text: str, errors: list[str]) -> tuple[dict, str] | None:
    m = FM.match(text)
    if not m:
        errors.append(
            "frontmatter must be TOML delimited by +++ on the first line and again after the keys"
        )
        return None
    try:
        meta = tomllib.loads(m.group(1))
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"frontmatter is not valid TOML: {exc}")
        return None
    return meta, m.group(2)


def check_date(meta: dict, errors: list[str]) -> None:
    """The A8 trap: buildFuture=false means a future date is dropped with no error.

    Hugo would build green and simply omit the page, so a bad timestamp here is
    invisible until someone notices the site has stopped updating.
    """
    raw = meta.get("date")
    if raw is None:
        errors.append("missing required key: date")
        return

    if isinstance(raw, dt.datetime):
        when = raw
        rendered = raw.isoformat()
    elif isinstance(raw, str):
        rendered = raw
        try:
            when = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"date is not RFC3339: {raw!r}")
            return
    else:
        errors.append(f"date must be an RFC3339 timestamp, got {type(raw).__name__}")
        return

    if when.tzinfo is None:
        errors.append(f"date must carry an explicit UTC offset, got {rendered!r}")
        return
    if when.utcoffset() != dt.timedelta(0):
        errors.append(
            f"date must be UTC (offset +00:00 or a trailing Z), got {rendered!r}. "
            "A local offset can place the post in Hugo's future and buildFuture=false "
            "will silently drop it."
        )
        return

    # Allow a little slack for clock skew between the agent's VM and the runner.
    now = dt.datetime.now(dt.timezone.utc)
    if when > now + dt.timedelta(minutes=10):
        errors.append(
            f"date is in the future ({rendered}); buildFuture=false means Hugo will "
            "omit this page without reporting an error"
        )


def check_tags(meta: dict, vocab: set[str], errors: list[str]) -> None:
    tags = meta.get("tags")
    if tags is None:
        errors.append("missing required key: tags")
        return
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        errors.append("tags must be an array of strings")
        return
    if not tags:
        errors.append("tags must not be empty")
        return
    unknown = [t for t in tags if t not in vocab]
    if unknown:
        errors.append(
            f"tags not in the controlled vocabulary: {unknown}. "
            "Add them to automation/config/topics.toml deliberately, or pick existing ones."
        )


def check_body(section: str, body: str, errors: list[str]) -> None:
    if not body.strip():
        errors.append("body is empty")
        return

    if not URL.search(body):
        errors.append("body contains no source URL; every item must cite where it came from")

    if section == "research":
        if not re.search(r"^#{1,3}\s+References\s*$", body, re.MULTILINE):
            errors.append("deep dives require a '## References' section")
        for heading in ("Background", "Current State", "Future Outlook"):
            if not re.search(rf"^#{{1,3}}\s+{heading}\b", body, re.MULTILINE):
                errors.append(f"deep dives require a '## {heading}' section")


def validate_file(path: pathlib.Path, vocab: set[str]) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT)

    section = None
    for name, directory in SECTIONS.items():
        if directory in path.parents:
            section = name
            break
    if section is None:
        return [f"{rel}: not under content/news or content/research"]

    if path.name == "_index.md":
        return []

    pattern = NEWS_NAME if section == "news" else RESEARCH_NAME
    if not pattern.match(path.name):
        errors.append(
            f"filename must match {'YYYY-MM-DD-daily-brief.md' if section == 'news' else 'YYYY-MM-DD-<topic-slug>.md'}"
        )

    parsed = split_frontmatter(path.read_text(encoding="utf-8"), errors)
    if parsed is None:
        return [f"{rel}: {e}" for e in errors]
    meta, body = parsed

    if not str(meta.get("title", "")).strip():
        errors.append("missing required key: title")

    declared = meta.get("type")
    if declared != section:
        errors.append(f"type must be {section!r} for a file in content/{section}/, got {declared!r}")

    slug = meta.get("slug")
    if slug is not None:
        if not isinstance(slug, str) or not SLUG.match(slug):
            errors.append(f"slug must be lowercase alphanumeric words joined by hyphens, got {slug!r}")
        elif len(slug) > MAX_SLUG_LEN:
            errors.append(f"slug is longer than {MAX_SLUG_LEN} characters")

    check_date(meta, errors)
    check_tags(meta, vocab, errors)
    check_body(section, body, errors)

    return [f"{rel}: {e}" for e in errors]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    args = ap.parse_args(argv)

    if args.paths:
        targets = [p.resolve() for p in args.paths]
    else:
        targets = sorted(
            p for d in SECTIONS.values() if d.exists() for p in d.rglob("*.md")
        )

    if not targets:
        print("validate: nothing to check")
        return 0

    vocab = load_vocabulary()
    all_errors: list[str] = []
    checked = 0
    for path in targets:
        if path.name == "_index.md":
            continue
        checked += 1
        all_errors.extend(validate_file(path, vocab))

    if all_errors:
        print(f"validate: FAILED ({len(all_errors)} problem(s) in {checked} file(s))\n")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"validate: {checked} file(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
