# site-build

One generator, one source of truth. Adding a research article used to mean
hand-editing seven places (the article, the research index card + count, the
homepage featured rows, `feed.xml`, `sitemap.xml`, the command palette, and the
prev/next nav on two articles). Every one of those was a chance to desync. This
removes that whole class of mistake.

It reads two manifests: `research/articles.json` for the articles, and the ATT&CK
coverage table in `tools/sigma-pack/README.md` for the sigma pack.

## How publishing works now

1. Write the article HTML in `research/<slug>.html` (copy an existing one; keep
   the standard footer nav block so the generator can find it).
2. Add one entry to `research/articles.json`, at the **top** of the `articles`
   array (newest first).
3. Run the generator:

   ```sh
   python3 tools/site-build/build_indexes.py
   ```

4. Commit. The `.githooks/pre-commit` hook runs `--check`. On drift it
   regenerates and stages the files it rewrote into the same commit, so a
   forgotten step can't ship. It stops first if one of those files, or
   `articles.json`, the sigma-pack README or the generator, has unstaged edits,
   so unrelated work never rides along: stage or stash them and commit again. It blocks the commit if regeneration fails, or for what it
   cannot fix: a research page missing from `research/articles.json`, or a
   sigma-pack rule file and the
   ATT&CK table in `tools/sigma-pack/README.md` that disagree (a file missing from
   the table, or a row with no file). It also scans the staged changes with
   gitleaks and refuses to commit if gitleaks is not installed. Enable it once per
   clone with `git config core.hooksPath .githooks` (needs python3 and gitleaks).

## What the generator owns

It rewrites only the regions fenced by `AUTO:*` markers, plus each article's
footer nav (located by its container class). Everything else - article bodies,
hand-written prose, channel boilerplate, the guide and tooling sitemap entries -
is never touched.

| File | Region | Marker |
| --- | --- | --- |
| `index.html` | hero "Read the latest research" button (latest 1) | `<!-- AUTO:hero ... -->` |
| `index.html` | homepage featured trio (latest 3) | `<!-- AUTO:featured ... -->` |
| `research/index.html` | category filter chips (only categories with articles) | `<!-- AUTO:filters ... -->` |
| `research/index.html` | article card grid | `<!-- AUTO:cards ... -->` |
| `research/index.html` | "N published so far" count | `<!-- AUTO:count ... -->` |
| `feed.xml` | `<lastBuildDate>` + every `<item>` | `<!-- AUTO:builddate ... -->`, `<!-- AUTO:items ... -->` |
| `sitemap.xml` | per-article research `<url>` entries | `<!-- AUTO:research ... -->` |
| `assets/umbra.js` | command-palette "Articles" entries | `/* AUTO:articles ... */` |
| `tools/sigma-pack/index.html` | ATT&CK coverage table (from the table in `tools/sigma-pack/README.md`) | `<!-- AUTO:sigmapack ... -->` |
| `research/<slug>.html` | prev/next footer nav | located structurally (no marker) |
| `research/<slug>.html` | JSON-LD `dateModified` + `article:modified_time` meta, only when `updated` is set | the line after `datePublished` / `article:published_time` |
| standard site pages (see below) | shared site footer (depth-aware links) | the whole `<footer>` element is replaced (no marker) |

The count is computed, so "Three/Six published so far" can never go stale again.
Articles are sorted by date (newest first); equal dates keep manifest order.

The shared footer is defined once in `render_footer()` and written into every
standard site page (`index.html`, `about.html`, `tools/index.html`,
`tools/sigma-pack/index.html`, `guide/*.html` and `research/*.html`; `404.html`
keeps its own footer), with relative links adjusted for page depth. New pages just
need any `<footer>...</footer>` placeholder - the generator replaces it wholesale -
which you get for free by copying an existing page.

## Links

Internal links use the URLs Pages actually serves: `about`, `research/<slug>`,
`guide/`, `tools/sigma-pack/` and `./` for the home page from a root page.
Pages 308-redirects `x.html` to `x` and `dir/index.html` to `dir/`, so a `.html`
link still works but costs every visitor and crawler a redirect. The generator
emits the extensionless form; write hand-made links the same way. Preview with
`npx wrangler pages dev .`, which follows the same rules (a plain static file
server or `file://` does not). The feed `<guid>` keeps its `.html` form on
purpose (see `render_feed_items`).

## Manifest fields (`research/articles.json`)

Per article: `slug`, `title`, `nav_title` (short label for prev/next), `category`
(`threat` | `detection` | `ai` | `tooling`), `date` (`YYYY-MM-DD`), `read_min`,
`home_blurb` (homepage row), `card_blurb` (research index card), `feed_desc` (RSS),
and a `palette` object (`label`, `hint`, `icon`, `keywords`).

Optional: `updated` (`YYYY-MM-DD`), the date of the article's latest dated
"Updated" note. The sitemap `<lastmod>` uses it instead of `date`, so search
engines recrawl changed articles, and the article gets a JSON-LD `dateModified` and an
`article:modified_time` meta with the same date (both are removed again if the field
goes). Set it whenever you add such a note; the feed
and the sort order still use `date`. The hand-written sitemap entries (home,
guide, research index, tools, about) are bumped by hand when those pages change
in substance; footer-only regenerations do not count.

Use **raw** text: literal `&` and `"`. The generator escapes per output format
(HTML/XML entity-escaping for the pages and feed, JS-string escaping for the
palette). Do not pre-escape.

## Commands

```sh
python3 tools/site-build/build_indexes.py          # regenerate (writes changes)
python3 tools/site-build/build_indexes.py --check   # hook guard: exit 1 on drift, writes nothing
python3 tools/site-build/build_indexes.py --list-drift  # print the files a regen would rewrite
```

`--check` also exits 1, even with no drift, when a `research/*.html` page is
missing from `articles.json`, when a site page lacks the "Skip to content" link
or the `<main id="main">` landmark, when a page has an internal link written as
`.html` (outside `<pre>` blocks), when a page does not have exactly one
`<meta name="description">` or its decoded text is over 160 characters (search
engines cut the snippet there; aim for about 155, and `og:description` and
`twitter:description` are not checked), when the sha256 of an inline script in
`404.html` is missing from the Content-Security-Policy lines in `_headers` (it
prints the new hash), when a sigma-pack `rules/**/*.yml` or
`queries/**/*.kql` file has no row in the ATT&CK table, or when a table row
points at a file that doesn't exist.
