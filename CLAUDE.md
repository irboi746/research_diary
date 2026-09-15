# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

A Hugo site using the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme, deployed to
GitHub Pages via `.github/workflows/pages.yml`. It publishes a technical research diary covering
security and CS work — arXiv, USENIX, DEF CON, Black Hat, Off-by-One, and implementation docs.

Content is **written by Google Jules**, driven from the Jules web console (no API, no orchestration
in this repo). Jules reads `AGENTS.md`; that file is the pipeline specification. GitHub Actions only
validates the pull request Jules opens and deploys after merge.

## Read these first

Before changing site configuration, styling, or the deploy pipeline, read:

1. **`REFERENCE_caa20260903_153422.md`** — the configuration reference. Documents every PaperMod
   param (site-wide, per-page, and both), the CSS-variable colour/layout system, what **cannot**
   be configured without overriding theme templates, and which settings are dead no-ops. Written
   by inspecting the theme source, so it is more current than the PaperMod wiki.
2. **`README.md`** — setup, local development, and deploy.

`REFERENCE_*.md` files are timestamped; if several exist, read the newest.

## Hard rules

### Do not hardcode `baseURL`

CI builds with `hugo --minify --baseURL "<configure-pages base_url>/"`, which overrides
`config.toml`. The `actions/configure-pages` step resolves the real deployed URL at build time —
GitHub's equivalent of GitLab's `$CI_PAGES_URL`. This is deliberate: it survives the
`/research_diary` project subpath, repo or account renames, and a custom domain added later.

- Leave `baseURL = "/"` in `config.toml`. It affects local builds only.
- Do not set `relativeURLs = true`. Hugo's docs restrict it to filesystem-navigable sites; it
  leaves RSS `<link>` and `og:url` non-absolute, breaking feeds and link previews.
- Do not remove the `--baseURL` flag from the build job in `.github/workflows/pages.yml`.

See §4 of the reference for the full rationale and the verified failure modes.

### Generated content is confined to an allowlist

The pipeline's entire input is untrusted — paper text, conference slides, arbitrary web pages — fed
to an agent with write access to this repo. A poisoned document that talks the agent into editing a
workflow would otherwise be merged automatically.

`automation/scripts/pathguard.py` therefore restricts generated changes to:

- `content/news/*.md`
- `content/research/*.md`
- `automation/state/*`

Content is Markdown-only on purpose: Hugo serves a `.html` file in `content/` verbatim, without
Goldmark, and `validate.py` only globs `*.md` — so any-extension patterns would hand the agent a raw
HTML publishing primitive that nothing inspects.

Anything else fails the check and blocks auto-merge. **Do not widen that allowlist**, and do not add
a path to it so that a failing run goes green. If a pipeline change genuinely needs to touch another
file, a human makes that change in a separate commit.

This has already gone wrong once. In `a79aa37` the agent hit the guard and added `.github/workflows/*`,
`config.toml` and `pathguard.py` to it; in `990b2d8` it moved those same paths out of the test's DENY
list into ALLOW so CI went green. The guard then permitted precisely what it existed to stop, for
three commits. `test_pathguard.py` now pins the whole `ALLOWED` tuple against a literal, so widening
it fails the suite rather than being ratified by an edited expectation list. Keep that pin.

#### The guard must run from `main`, never from the pull request

For a same-repo branch, `on: pull_request` runs the workflow file **and the scripts** from the PR
head. A pull request that edits `pathguard.py` is therefore checked by its own edited copy. That is
why `validate-content.yml` is explicitly *not* the trust boundary, and why the merge lives in
`.github/workflows/auto-merge.yml` under `on: workflow_run` — that trigger always runs the default
branch's copy. It re-runs `main`'s guard against the PR's diff via `--head`, and only then merges.

Two invariants to preserve there: `auto-merge.yml` must never check out or execute anything from the
pull request, and the path check must come before the content checkout.

The guard also inspects blob modes and both sides of a rename. Neither is cosmetic: `--name-only`
prints only the destination of a rename, so `git mv .github/workflows/pages.yml content/news/x.md`
used to read as a single allowed path while the workflow silently vanished.

### TOML tables swallow every key below them

This bit the repo twice. In `config.toml`, seven top-level settings — `buildFuture` among them — sat
below `[pagination]` and were silently scoped into it, so Hugo never applied them. The same mistake
put `tags` inside `[discovery]` in `automation/config/topics.toml`.

When adding a key to any `.toml` here, check it lands where you think:

```shell
python3 -c "import tomllib;print(sorted(tomllib.load(open('config.toml','rb'))))"
```

### Dates must be RFC3339 UTC

`buildFuture = false`, so Hugo **silently drops** a future-dated page — green build, no warning, post
never appears. A local `+08:00` offset is enough to trigger it near the cron time.
`automation/scripts/validate.py` rejects non-UTC and future dates, and CI additionally asserts each
changed page rendered to `public/`. Both checks exist because the failure is invisible otherwise.

### The theme floats to latest

`.github/workflows/pages.yml` runs `hugo mod get -u`, so the theme tracks PaperMod master and the `go.mod` pin
is ignored at build time. Verify theme behaviour against master, not against `go.mod`.

Practical trap: the dark-mode CSS selector is `:root[data-theme="dark"]` on master; it was `.dark`
until early 2025. Snippets written for `.dark` silently do nothing.

### Revert `go.mod` / `go.sum` after local builds

`hugo mod get` rewrites both. Unless a dependency change is the actual goal:

```shell
git checkout -- go.mod go.sum
```

## Where things go

| Change | File |
|---|---|
| Site config, params, menus | `config.toml` |
| Colours, fonts, layout geometry | `assets/css/extended/custom.css` (concatenated after theme CSS) |
| Pages and posts | `content/` |
| Static files served at site root | `static/` |
| Build and deploy | `.github/workflows/pages.yml` |
| Content pipeline spec (read by Jules) | `AGENTS.md` |
| Research scope, sources, tag vocabulary | `automation/config/topics.toml` |
| Pipeline tooling and its tests | `automation/scripts/` |
| Deduplication state | `automation/state/seen.ndjson` |
| Content format references | `automation/examples/` |
| PR validation (advisory; runs PR code) | `.github/workflows/validate-content.yml` |
| Auto-merge — the trust boundary, runs from `main` | `.github/workflows/auto-merge.yml` |
| Pipeline health canary | `.github/workflows/staleness.yml` |

Do not add files to `themes/` — the theme is a Hugo module. The directory holds only `.gitkeep`.

## Verifying changes

Run the script suite first — it needs no dependencies and catches most breakage in a second:

```shell
for t in automation/scripts/test_*.py; do python3 "$t" || break; done
python3 automation/scripts/validate.py
```

Hugo is not installed locally; use a Docker image. CI pins its own Hugo version (`HUGO_VERSION` in
the workflow), so this approximates CI rather than matching it exactly. Full commands are in §7 of
the reference. Minimum bar before reporting a config or template change as done:

```shell
docker run --rm -e PAGES_URL="https://irboi746.github.io/research_diary" \
  -v "$PWD":/src -w /src hugomods/hugo:exts sh -c '
    hugo mod get -u github.com/adityatelange/hugo-PaperMod
    hugo --minify --baseURL "$PAGES_URL/" -d /tmp/ci'
git checkout -- go.mod go.sum
```

Expect no `WARN` or `ERROR` lines. For styling changes, also check the rendered output rather than
assuming a param took effect — several plausible-looking PaperMod params are no-ops (reference §4).

## Conventions

- Renaming the site means updating `title` and `[params.homeInfoParams] Title` in `config.toml`,
  and the `module` line in `go.mod`.
- `LICENSE` is MIT, Copyright (c) 2014 Spencer Lyon, inherited from the upstream GitLab Pages
  Hugo example. Do not silently rewrite or delete it.
- `AGENTS.md` is Jules' entry point; `CLAUDE.md` is Claude's. Keep the hard constraints in the two
  files consistent — if the allowlist changes in one, it must change in the other and in
  `pathguard.py`.
- Content frontmatter is **TOML** (`+++`), not YAML, so `validate.py` can parse it with stdlib
  `tomllib` instead of a hand-rolled YAML parser. The permitted key set is pinned in
  `validate.py`'s `ALLOWED_KEYS`; PaperMod renders several other params (`cover.image`,
  `canonicalURL`, `editPost.URL`) straight into HTML attributes, so adding one is a human decision.
- `goldmark.renderer.unsafe = false` and `enableInlineShortcodes = false` in `config.toml` are
  security settings, not style. Posts quote untrusted abstracts near-verbatim; `unsafe` would publish
  any markup in that material, and an inline shortcode is arbitrary Go-template execution in the
  build runner. `validate.py`'s `check_markup` rejects the same things independently.
- Actions are pinned to full commit SHAs and the Hugo `.deb` is checksum-verified (`HUGO_SHA256`).
  Bump `HUGO_VERSION` and `HUGO_SHA256` together, taking the hash from the release's own
  `hugo_${HUGO_VERSION}_checksums.txt`.
