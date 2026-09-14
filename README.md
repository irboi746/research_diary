# test-hugo

Boilerplate [Hugo](https://gohugo.io) site using the
[PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme, deployed to
[GitHub Pages](https://docs.github.com/en/pages).

Fork or copy this repo to start a new site. Everything under `content/` is placeholder text.

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

1. Rename the site — `title` and `[params.homeInfoParams] Title` in `config.toml`, and the
   `module` line in `go.mod`.
1. Replace the placeholder pages in `content/`.

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
| Site title, menus, params | `config.toml` |
| Colours, fonts, layout geometry | `assets/css/extended/custom.css` |
| Pages and posts | `content/` |
| Files served at site root | `static/` |

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
