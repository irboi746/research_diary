# research_diary

![research_diary](/assets/research_diary_logo.jpg)

A technical research diary: daily briefs on newly published security and CS work, plus long-form
deep dives. Content is researched and written by [Google Jules](https://jules.google/), built with
[Hugo](https://gohugo.io) and [PaperMod](https://github.com/adityatelange/hugo-PaperMod), and
published to [GitHub Pages](https://docs.github.com/en/pages).

Sources: arXiv, USENIX Security, USENIX WOOT, IEEE S&P, NDSS, ACM CCS, DEF CON, Black Hat and
[un]prompted — plus open web search, so the diary is not
limited to those.

## How it works

```
Jules web console  ──>  Jules VM reads AGENTS.md  ──>  pull request
                                                          │
                              validate-content.yml  <─────┘
                              path guard, schema, Hugo build
                                                          │
                                           auto-merge ────┴──>  pages.yml  ──>  GitHub Pages
```

Nothing in this repository calls Jules. The schedule and the prompts live in the Jules console; the
repository carries the specification Jules reads (`AGENTS.md`), the tooling it runs
(`automation/scripts/`), and the checks that gate its output.

| Layer | Owns |
|---|---|
| Jules console | Repo connection, Initial Setup, the daily scheduled task, manual deep dives |
| This repo | `AGENTS.md`, research scope, helper scripts, dedup state, Hugo layout |
| GitHub Actions | PR validation, auto-merge, deploy |

## Quick start

1. Clone the repo.
1. Install [Hugo](https://gohugo.io/installation/) (extended) and [Go](https://go.dev/doc/install)
   — Go is needed because the theme is a Hugo module.
1. Fetch the theme:

   ```shell
   hugo mod get -u github.com/adityatelange/hugo-PaperMod
   ```

1. Preview at <http://localhost:1313/>:

   ```shell
   hugo server
   ```

1. Run the pipeline's own tests. They need no dependencies — the tests covering `fulltext.py`'s
   HTML and PDF extraction skip themselves when the packages are absent, and report that they did:

   ```shell
   for t in automation/scripts/test_*.py; do python3 "$t" || break; done
   ```

   To run those skipped checks too, install the ingestion dependencies. A virtualenv is the usual
   way; on a PEP 668 system without `python3-venv` available, install to a directory instead:

   ```shell
   python3 -m pip install --target .pylibs -r requirements.txt
   PYTHONPATH=.pylibs python3 automation/scripts/test_fulltext.py
   ```

   `.pylibs/` is gitignored.

No local Hugo install? Use a Docker image (CI pins its own Hugo version, so this approximates CI
rather than matching it exactly):

```shell
docker run --rm -p 1313:1313 -v "$PWD":/src -w /src hugomods/hugo:exts \
  sh -c 'hugo mod get -u github.com/adityatelange/hugo-PaperMod && hugo server --bind 0.0.0.0'
git checkout -- go.mod go.sum   # hugo mod get rewrites these
```

## Configuration

See **[`REFERENCE_caa20260903_153422.md`](REFERENCE_caa20260903_153422.md)** for the full
configuration reference: every PaperMod param, the CSS-variable colour and layout system, what
cannot be configured without overriding theme templates, and which settings are dead no-ops.

Short version:

| Change | Where |
|---|---|
| What gets researched (interests, sources, tags) | `automation/config/topics.toml` |
| How Jules behaves | `AGENTS.md` |
| Site title, menus, params | `config.toml` |
| Colours, fonts, layout geometry | `assets/css/extended/custom.css` |
| Pages and posts | `content/` |
| Files served at site root | `static/` |

## The content pipeline

### One-time setup in the Jules console

1. Connect `irboi746/research_diary` (installs the Jules GitHub App).
2. Configure the environment and snapshot it — see below. `fulltext.py` needs three packages;
   without them every paper falls back to abstract-only.
3. Create the scheduled task — but only after a manual run has produced output you trust.

### Jules console environment

**Jules → Configure repo → Environment → run and snapshot.**

Python 3.12 is preinstalled. Most of the tooling is stdlib, but the ingestion tools need three
packages, so the environment setup script is:

```shell
pip install -r requirements.txt
```

Run it, and once it succeeds **take the snapshot**. Jules reuses that snapshot for every later task
started from this repository, so the install cost is paid once instead of on every run — which
matters here, because the arXiv brief runs daily.

Three things worth knowing, because each one fails quietly:

- **Re-run and re-snapshot whenever `requirements.txt` changes.** A stale snapshot keeps the old
  packages, and the failure looks like a content problem rather than an environment one:
  `fulltext.py` cannot import `bs4`, falls back to the abstract, and the brief is thinner than it
  should be. `AGENTS.md` tells Jules to report an import failure rather than work around it.
- **This replaces the old "leave Initial Setup empty" instruction.** That was true while everything
  was stdlib-only; it is not any more.
- **CI installs none of this.** The checks that gate a merge — `pathguard.py`, `validate.py`,
  `postparse.py`, `linkcheck.py` — are deliberately stdlib-only, so no third-party package sits
  between an untrusted pull request and a write token. A broken snapshot therefore shows up as a
  failed Jules run, never as a bad merge.

### The console prompts

These live only in the Jules UI, which is not version controlled and cannot be restored from git.
They are recorded here so they can be recreated:

**arXiv brief** — Scheduled Task, Daily:

```
Run the arXiv brief pipeline exactly as specified in AGENTS.md.
```

**Conference brief** — Scheduled Task, Weekly:

```
Run the conference brief pipeline exactly as specified in AGENTS.md.
```

**Deep dive** — a normal task, run by hand:

```
Run the deep research pipeline as specified in AGENTS.md. Topic: <your topic>
```

The pipeline names must match the headings in `AGENTS.md` exactly — with a one-line prompt, those
words are the only thing selecting which procedure runs.

Weekly for the conference brief because every tier-2 source is `window = "unseen"` with
`check = "weekly"`: they publish in one annual burst and then drain, so a daily run would find
nothing most days. That is a valid outcome — it opens no pull request — but it spends a Jules run to
discover it. The backlog queue is what makes the burst manageable: a programme is enqueued once and
`queue.py` hands out eight papers per run, so a 200-paper conference becomes a couple of dozen
ordinary weekly briefs instead of one unusable post.

They are one line on purpose. Everything else lives in `AGENTS.md` and `automation/config/topics.toml`,
where it is reviewable and diffable — and because a Jules scheduled task **cannot be edited** once
created, only deleted and recreated. Keeping the prompt stable means iterating on behaviour is a
pull request, not a UI round trip.

### What guards the output

`validate-content.yml` runs on every pull request Jules opens:

1. **Path guard** — the diff may only touch `content/arxiv/**`, `content/conferences/**`,
   `content/deep-dives/**` and `automation/state/**`. The pipeline's input is untrusted web content
   fed to an agent with repo write access, so this is the boundary that stops a poisoned paper from
   editing a workflow.
2. **Schema** — TOML frontmatter, RFC3339 UTC date, tags from the controlled vocabulary, required
   sections, and grounding: a source URL on *each* item rather than somewhere in the file, every
   citation matched to a reference and back, no conference index page standing in for a named paper,
   no two references sharing one URL, no placeholder identifiers.
3. **Link check** — the DOIs and arXiv IDs cited must resolve, and an arXiv ID must be the paper the
   post says it is. Only `doi.org` and `arxiv.org` are gating; everything else is reported and not
   enforced, because publishers such as ACM, Black Hat and CISA return 403 to a datacenter IP and
   gating on them would fail good pull requests.
4. **Build** — Hugo must actually render each changed page. `buildFuture = false` means a
   future-dated page is dropped *silently*, so a green build is not by itself evidence.

Passing all four auto-merges and triggers the deploy. Failing leaves the pull request open.

The schema and link checks exist because the earlier contract was prose. `AGENTS.md` has always said
"every item must carry a source URL", and the validator implemented it as one regular expression over
the whole file — so a 4,000-word deep dive with 33 references passed on the strength of one working
link. Ten of those 33 turned out not to support what they were attached to.

### Health

**There is no monitoring.** A weekly `staleness.yml` canary used to open an issue when a feed went
quiet; it was removed to cut workflow noise. Nothing in this repo observes the pipeline, so a
deleted scheduled task, a revoked repo connection, a stale environment snapshot and a genuinely
quiet week all look identical from here: no new posts.

Check by hand, in rough order of likelihood, if briefs stop appearing:

- the scheduled tasks in the Jules console — are they still there, and when did each last run?
- the repository connection and the Jules GitHub App installation;
- any open pull request from Jules sitting unmerged because validation failed;
- `queue.py stats` — pending items with no briefs being written means runs are failing, not that
  there is nothing to cover;
- whether `automation/config/topics.toml` has been narrowed until it matches nothing.

## Deployment

One-time repo setup: under **Settings > Pages > Build and deployment**, set **Source** to
**GitHub Actions**. The workflow cannot do this for you, and the deploy job fails without it.

`.github/workflows/pages.yml` defines two jobs:

- **`build`** — runs on every push and pull request. Off the default branch it only builds, which
  catches template and config errors without deploying anything.
- **`deploy`** — publishes the built artifact to Pages, from the default branch only.

The build runs `hugo --minify --baseURL "<the real Pages URL>/"`.

### Do not hardcode `baseURL`

The `configure-pages` action resolves the real deployed Pages URL at build time and exposes it as
`steps.pages.outputs.base_url`; the `--baseURL` flag then overrides `config.toml`. This one setup
handles all of:

- the standard project URL, `https://<user>.github.io/<repo>/` — note the **subpath**, which every
  asset and link must be prefixed with
- renaming the repo or the account
- a custom domain added later in repo settings

`config.toml` keeps `baseURL = "/"`, which affects **local builds only** and lets `hugo server`
serve from the root.

Do not set `relativeURLs = true` to try to make paths portable. Hugo restricts it to
filesystem-navigable sites, and it leaves RSS `<link>` elements and `og:url` non-absolute, which
breaks feed readers and link previews. Reference §4 covers this in detail.

### Using a custom domain or a user site

No config change needed — set the domain under **Settings > Pages > Custom domain** (GitHub writes
a `CNAME` file into the repo), or rename the repo to `<user>.github.io` for a root-level user site.
`base_url` follows either way.

## Theme

The theme is a Hugo module, not a submodule; `themes/` is intentionally empty.

The workflow runs `hugo mod get -u`, so **the theme floats to PaperMod master on every build** and
the commit pinned in `go.mod` is ignored at build time. New params arrive automatically, but so do
upstream breaking changes. To pin instead, drop `-u` from the workflow's `Fetch theme` step and
commit an exact version in `go.mod`.

To swap themes, change `THEME_URL` in the workflow's `env:` block and `theme` in `config.toml`,
then re-run `hugo mod get -u <new theme>`.

## Working with Claude Code

`CLAUDE.md` points Claude at this README and the reference document, and records the hard rules
(notably the `baseURL` handling).

## License

MIT — see [`LICENSE`](LICENSE). Copyright (c) 2014 Spencer Lyon; inherited from the upstream
[GitLab Pages Hugo example](https://gitlab.com/pages/hugo) this repo derives from. Replace it
deliberately if that is no longer accurate.
