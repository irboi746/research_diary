# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

A **boilerplate** Hugo site using the [PaperMod](https://github.com/adityatelange/hugo-PaperMod)
theme, deployed to GitHub Pages via `.github/workflows/pages.yml`. Site title is `test-hugo` — rename it per
project. Content under `content/` is placeholder text meant to be replaced.

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

Do not add files to `themes/` — the theme is a Hugo module. The directory holds only `.gitkeep`.

## Verifying changes

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
