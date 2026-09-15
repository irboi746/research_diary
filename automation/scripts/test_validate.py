#!/usr/bin/env python3
"""Tests for the generated-content validator.

Run: python3 automation/scripts/test_validate.py

Each case asserts that a specific kind of breakage is caught with a specific
message. The date cases matter most: buildFuture=false means Hugo drops a
future-dated page silently, so a bad timestamp is invisible until someone notices
the site stopped updating.
"""

import datetime as dt
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import validate as V  # noqa: E402

FAILURES: list[str] = []
VOCAB = V.load_vocabulary()

PAST = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
FUTURE = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

GOOD_NEWS = f'''+++
title = "Daily Brief"
date = {PAST}
type = "news"
tags = ["cs.CR", "fuzzing"]
+++

## A Paper About Things

- It does a thing.

Source: https://arxiv.org/abs/2509.12345
'''

GOOD_RESEARCH = f'''+++
title = "Fuzzing"
date = {PAST}
type = "research"
tags = ["fuzzing"]
slug = "fuzzing-state-of-the-art"
+++

## Background
Some background.

## Current State
Where things stand. See https://arxiv.org/abs/2509.12345

## Future Outlook
Where it is going.

## References
1. Lovelace, A. "A Paper." USENIX Security 2025. https://arxiv.org/abs/2509.12345
'''


def run(name: str, filename: str, body: str, expect: str | None) -> None:
    """expect=None means it must pass; otherwise the substring required in an error."""
    section = "news" if "daily-brief" in filename or "news" in filename else "research"
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        target = root / "content" / section
        target.mkdir(parents=True)
        path = target / filename
        path.write_text(body, encoding="utf-8")

        saved_root, saved_sections = V.ROOT, V.SECTIONS
        V.ROOT = root
        V.SECTIONS = {"news": root / "content" / "news", "research": root / "content" / "research"}
        try:
            errors = V.validate_file(path, VOCAB)
        finally:
            V.ROOT, V.SECTIONS = saved_root, saved_sections

    if expect is None:
        if errors:
            FAILURES.append(f"{name}: expected to pass, got {errors}")
    else:
        if not any(expect in e for e in errors):
            FAILURES.append(f"{name}: expected an error containing {expect!r}, got {errors}")


run("valid daily brief", "2026-09-15-daily-brief.md", GOOD_NEWS, None)
run("valid deep dive", "2026-09-15-fuzzing.md", GOOD_RESEARCH, None)

# --- the A8 trap: future dates are dropped silently by Hugo -------------------
run(
    "future date is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace(PAST, FUTURE),
    "future",
)
run(
    "non-UTC offset is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace(PAST, "2026-09-15T06:00:00+08:00"),
    "must be UTC",
)
run(
    "naive timestamp is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace(f"date = {PAST}", 'date = "2026-09-15T06:00:00"'),
    "explicit UTC offset",
)
run(
    "missing date is reported",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace(f"date = {PAST}\n", ""),
    "missing required key: date",
)
run(
    "quoted RFC3339 string is accepted",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace(f"date = {PAST}", f'date = "{PAST}"'),
    None,
)

# --- taxonomy ----------------------------------------------------------------
run(
    "out-of-vocabulary tag is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace('["cs.CR", "fuzzing"]', '["Artificial Intelligence"]'),
    "controlled vocabulary",
)
run(
    "empty tag list is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace('["cs.CR", "fuzzing"]', "[]"),
    "must not be empty",
)

# --- structure ---------------------------------------------------------------
run(
    "missing source URL is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace("Source: https://arxiv.org/abs/2509.12345", "Source: withheld"),
    "no source URL",
)
run(
    "deep dive without References is rejected",
    "2026-09-15-fuzzing.md",
    GOOD_RESEARCH.split("## References")[0],
    "References",
)
run(
    "deep dive without Background is rejected",
    "2026-09-15-fuzzing.md",
    GOOD_RESEARCH.replace("## Background", "## Preamble"),
    "Background",
)
run(
    "wrong type for the directory is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace('type = "news"', 'type = "research"'),
    "type must be 'news'",
)
run(
    "missing title is reported",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace('title = "Daily Brief"\n', ""),
    "missing required key: title",
)
run(
    "bad filename is rejected",
    "brief.md",
    GOOD_NEWS,
    "filename must match",
)
run(
    "bad slug is rejected",
    "2026-09-15-fuzzing.md",
    GOOD_RESEARCH.replace('slug = "fuzzing-state-of-the-art"', 'slug = "Fuzzing State!"'),
    "slug must be lowercase",
)

# --- frontmatter format ------------------------------------------------------
run(
    "YAML frontmatter is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace("+++", "---"),
    "TOML delimited by +++",
)
run(
    "malformed TOML is reported",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace('title = "Daily Brief"', "title = Daily Brief"),
    "not valid TOML",
)
run(
    "empty body is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.split("+++")[1].join(["+++", "+++\n\n"]),
    "body is empty",
)

# --- markup injection --------------------------------------------------------
# Briefs quote untrusted abstracts near-verbatim, so this is the realistic path
# for hostile markup: it arrives inside the source material, not hand-written.
for name, payload, expect in (
    ("script tag", "<script>alert(1)</script>", "a raw HTML tag"),
    ("iframe", '<iframe src="https://evil.tld"></iframe>', "a raw HTML tag"),
    ("svg", "<svg onload=alert(1)>", "a raw HTML tag"),
    ("event handler", '<img src=x onerror="alert(1)">', "an HTML event handler"),
    ("javascript URL", "[click](javascript:alert(1))", "a javascript: URL"),
    ("data URL", "[click](data:text/html;base64,PHM+)", "a data:text/html URL"),
    ("angle shortcode", "{{< instagram abc >}}", "a Hugo shortcode"),
    ("percent shortcode", "{{% x %}}", "a Hugo shortcode"),
):
    run(
        f"{name} in body is rejected",
        "2026-09-15-daily-brief.md",
        GOOD_NEWS.replace("- It does a thing.", f"- It does a thing. {payload}"),
        expect,
    )

# Prose that merely mentions markup must still pass: a security diary writes
# about <script> tags constantly, and fenced code is escaped, not executed.
run(
    "inline code mentioning a tag still passes",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace("- It does a thing.", "- Escapes `&lt;script&gt;` in output."),
    None,
)

# --- frontmatter keys --------------------------------------------------------
# PaperMod renders these straight into src/href attributes, so they are an
# injection surface that never touches the body.
run(
    "unknown frontmatter key is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace("type = ", 'canonicalURL = "javascript:alert(1)"\ntype = '),
    "unknown frontmatter key",
)
run(
    "cover image is rejected",
    "2026-09-15-daily-brief.md",
    GOOD_NEWS.replace("type = ", 'cover = { image = "https://evil.tld/x.png" }\ntype = '),
    "unknown frontmatter key",
)

# --- the shipped format examples must satisfy the contract they demonstrate ---
# AGENTS.md points Jules at these files as the format reference. If they drift
# from the validator, Jules copies a format that then fails in CI.
EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"
for example, target_name in (
    ("news-example.md", "2026-09-10-daily-brief.md"),
    ("research-example.md", "2026-09-10-directed-fuzzing.md"),
):
    src = EXAMPLES / example
    if not src.exists():
        FAILURES.append(f"missing format example: {src}")
        continue
    run(f"shipped example {example}", target_name, src.read_text(encoding="utf-8"), None)


if FAILURES:
    print(f"FAILED ({len(FAILURES)}):\n")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("validate: all checks passed")
