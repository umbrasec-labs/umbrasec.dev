#!/usr/bin/env python3
"""
build_indexes.py - regenerate every derived list on the UMBRASEC site from the
single source of truth at research/articles.json.

What it owns (and nothing else):
  - index.html .............. the homepage "featured" trio (latest 3 articles)
  - research/index.html ..... the article card grid + the "N published so far" count
  - feed.xml ................ <lastBuildDate> + every <item>
  - sitemap.xml ............. the per-article research <url> entries (lastmod =
                              "updated" if set, else "date")
  - assets/umbra.js ......... the command-palette "Articles" entries
  - index.html .............. the hero trace-to-rule reel (hero_reel.py), one
                              example per sigma-pack file
  - research/<slug>.html .... each article's prev/next footer nav, and its
                              JSON-LD dateModified + article:modified_time
                              (present only when "updated" is set)

Everything else in those files - hand-written prose, article bodies, the channel
boilerplate, the guide/tooling sitemap entries - is left untouched. The generator
only rewrites the regions fenced by AUTO markers, plus the nav block in each
article (located structurally by its container class).

Usage:
  python3 tools/site-build/build_indexes.py          # write changes
  python3 tools/site-build/build_indexes.py --check   # hook guard: exit 1 if drift
  python3 tools/site-build/build_indexes.py --list-drift  # files a regen would rewrite

The --check mode writes nothing; it just fails if the committed files don't match
what the manifest would produce. That's what the pre-commit hook runs. It also
fails when a site page's meta description is missing or longer than 160
characters (decoded text), when a sigma-pack rule's detection map (or one list
item of it) names the same field twice, which Chainsaw cannot load, and when
ai-agent-config-changed-by-command stops recognising agents the same way as
ai-agent-shell-risky-command. The
homepage trace-to-rule reel is generated (hero_reel.py), so a rule or claim
edit shows up as drift in index.html.
"""

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import hero_reel

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research" / "articles.json"

# category key -> (uppercase eyebrow label, title-case feed/filter label, data-cat value)
CATEGORIES = {
    "threat":    ("THREAT ANALYSIS",      "Threat Analysis",      "threat"),
    "detection": ("DETECTION ENGINEERING", "Detection Engineering", "detection"),
    "ai":        ("AI & LLM SECURITY",    "AI & LLM Security",    "ai"),
    "tooling":   ("TOOLING",              "Tooling",              "tooling"),
}

# canonical display order for the research index filter chips
CATEGORY_ORDER = ["detection", "threat", "ai", "tooling"]

_ONES = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
         "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty"]


def number_word(n: int) -> str:
    return _ONES[n] if 0 <= n < len(_ONES) else str(n)


def he(s: str) -> str:
    """HTML/XML-escape text content (ampersands and angle brackets; quotes stay literal, matching the existing markup)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def js(s: str) -> str:
    """Escape for a double-quoted JavaScript string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def parse_date(d: str) -> dt.date:
    return dt.datetime.strptime(d, "%Y-%m-%d").date()


def rfc822(d: dt.date) -> str:
    # All articles publish at a normalized 12:00:00 UTC.
    return d.strftime("%a, %d %b %Y 12:00:00 +0000")


def load_articles():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    articles = data["articles"]
    for a in articles:
        if a["category"] not in CATEGORIES:
            sys.exit(f"error: article '{a['slug']}' has unknown category '{a['category']}'")
        a["_date"] = parse_date(a["date"])
        # optional: date of the latest dated "Updated" note, for the sitemap
        if "updated" in a and parse_date(a["updated"]) < a["_date"]:
            sys.exit(f"error: article '{a['slug']}' has updated {a['updated']} before its date {a['date']}")
    # newest first; stable sort keeps manifest order among equal dates
    articles.sort(key=lambda a: a["_date"], reverse=True)
    return articles


# ---- marker-region replacement -------------------------------------------------

def replace_region(text: str, name: str, new_inner: str, path: Path) -> str:
    """Replace content between <!-- AUTO:{name} START --> and END markers.
    Markers may be HTML (<!-- -->) or JS (/* */) comments."""
    patterns = [
        (f"<!-- AUTO:{name} START -->", f"<!-- AUTO:{name} END -->"),
        (f"/* AUTO:{name} START */", f"/* AUTO:{name} END */"),
    ]
    for start, end in patterns:
        i = text.find(start)
        if i == -1:
            continue
        j = text.find(end, i)
        if j == -1:
            sys.exit(f"error: found '{start}' but no matching END in {path}")
        return text[: i + len(start)] + new_inner + text[j:]
    sys.exit(f"error: AUTO:{name} markers not found in {path}")


# ---- block renderers -----------------------------------------------------------

def _wrap(items, sep: str, end_indent: int) -> str:
    """Join rendered items and frame them so the closing AUTO marker lands at end_indent."""
    return "\n" + sep.join(items) + "\n" + " " * end_indent


def render_home_rows(articles) -> str:
    rows = []
    for a in articles[:3]:
        label = he(CATEGORIES[a["category"]][0])
        mon_year = a["_date"].strftime("%b %Y")
        rows.append(
f'''                <a href="research/{a['slug']}" class="block">
                    <div class="research-row grid grid-cols-1 md:grid-cols-12 gap-x-8 py-8 group">
                        <div class="md:col-span-5">
                            <div class="font-mono text-xs text-[#88a57d] mb-2">{label}</div>
                            <div class="font-semibold text-xl group-hover:text-[#f25623] transition-colors">
                                {he(a['title'])}
                            </div>
                        </div>
                        <div class="md:col-span-7 text-[#959c95] mt-2 md:mt-0">
                            {he(a['home_blurb'])}
                            <div class="mt-3 flex items-center gap-x-3 text-xs font-mono">
                                <span class="text-[#f25623]">{mon_year}</span>
                                <span class="text-[#7d837d]">·</span>
                                <span class="text-[#7d837d]">~{a['read_min']} min read</span>
                                <span class="row-chev ml-auto">Read →</span>
                            </div>
                        </div>
                    </div>
                </a>''')
    return _wrap(rows, "\n\n", 16)


def render_hero(articles) -> str:
    a = articles[0]
    anchor = (
f'''                        <a href="research/{a['slug']}"
                           class="btn-primary w-full sm:w-auto sm:whitespace-nowrap inline-flex items-center justify-center px-8 py-3.5 rounded-2xl bg-[#f25623] text-[#171717] font-semibold hover:bg-[#f56e0f] transition-all">
                            Read the latest research <span class="arrow ml-1.5">→</span>
                        </a>''')
    return _wrap([anchor], "\n", 24)


def render_cards(articles) -> str:
    cards = []
    for a in articles:
        label = he(CATEGORIES[a["category"]][0])
        cat = CATEGORIES[a["category"]][2]
        date_str = a["_date"].strftime("%b %d, %Y")
        cards.append(
f'''            <a href="{a['slug']}"
               class="research-card u-card block p-6 border border-[#525252] rounded-3xl bg-[#222222]" data-cat="{cat}">
                <div class="flex items-center justify-between mb-3">
                    <span class="font-mono text-xs text-[#88a57d]">{label}</span>
                    <span class="font-mono text-[10px] text-[#7d837d]">~{a['read_min']} min</span>
                </div>
                <div class="research-card-title font-semibold text-xl leading-tight mb-3">
                    {he(a['title'])}
                </div>
                <p class="text-sm text-[#959c95] mb-5">
                    {he(a['card_blurb'])}
                </p>
                <div class="flex items-center text-xs font-mono text-[#f25623]">
                    <span>{date_str}</span>
                    <span class="research-card-arrow ml-auto">Read →</span>
                </div>
            </a>''')
    return _wrap(cards, "\n\n", 12)


def render_count(articles) -> str:
    return f"{number_word(len(articles))} published so far"


def render_filters(articles) -> str:
    # "All" plus one chip per category that actually has at least one article
    present = [k for k in CATEGORY_ORDER if any(a["category"] == k for a in articles)]
    chips = ['            <button type="button" class="filter-chip active" data-filter="all" aria-pressed="true">All</button>']
    for k in present:
        label = he(CATEGORIES[k][1])
        chips.append(f'            <button type="button" class="filter-chip" data-filter="{k}" aria-pressed="false">{label}</button>')
    return _wrap(chips, "\n", 12)


def render_feed_items(articles) -> str:
    items = []
    for a in articles:
        feed_cat = he(CATEGORIES[a["category"]][1])
        # Cloudflare Pages serves the extensionless path and 308-redirects the
        # .html form, so links use the served URL. The guid keeps the original
        # .html string on purpose: readers key items by guid, and changing it
        # would re-surface every article as new.
        url = f"https://umbrasec.dev/research/{a['slug']}"
        items.append(f"""    <item>
      <title>{he(a['title'])}</title>
      <link>{url}</link>
      <guid isPermaLink="false">{url}.html</guid>
      <pubDate>{rfc822(a['_date'])}</pubDate>
      <category>{feed_cat}</category>
      <description>{he(a['feed_desc'])}</description>
    </item>""")
    return _wrap(items, "\n", 2)


def render_builddate(articles) -> str:
    return f"<lastBuildDate>{rfc822(articles[0]['_date'])}</lastBuildDate>"


def render_sitemap(articles) -> str:
    entries = []
    for a in articles:
        entries.append(f"""  <url>
    <loc>https://umbrasec.dev/research/{a['slug']}</loc>
    <lastmod>{a.get('updated') or a['date']}</lastmod>
    <priority>0.9</priority>
  </url>""")
    return _wrap(entries, "\n", 2)


def render_palette(articles) -> str:
    lines = []
    for a in articles:
        p = a["palette"]
        lines.append(
            f'    {{ group: "Articles", label: "{js(p["label"])}", '
            f'hint: "{js(p["hint"])}", icon: "{p["icon"]}", '
            f'href: "research/{a["slug"]}", keywords: "{js(p["keywords"])}" }},'
        )
    return _wrap(lines, "\n", 4)


# ---- sigma-pack index ----------------------------------------------------------
#
# The ATT&CK coverage table in tools/sigma-pack/README.md is the manifest for the
# pack, the way research/articles.json is for the writeups. It is parsed rather
# than the rule files themselves for one reason: the .kql queries carry no
# structured frontmatter, so the table is the only place their ATT&CK mapping
# lives. --check enforces both directions, so a rule cannot be added without a
# table row, and a row cannot point at a file that does not exist.

SIGMA_DIR = ROOT / "tools" / "sigma-pack"

# | [`file.yml`](rel/path.yml) | Type | [Txxxx](url) Name | Tactic | status |
# Five cells, anchored, so the 3-cell tables further down the README never match.
SIGMA_ROW_RE = re.compile(
    r"^\|\s*\[`(?P<file>[^`]+)`\]\((?P<path>[^)]+)\)\s*\|"
    r"\s*(?P<kind>[^|]*?)\s*\|"
    r"\s*(?P<attack>[^|]*?)\s*\|"
    r"\s*(?P<tactic>[^|]*?)\s*\|"
    r"\s*(?P<status>[^|]*?)\s*\|\s*$"
)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def load_sigma_rows():
    """Rows of the ATT&CK coverage table, in README order."""
    rows = [m.groupdict() for m in
            (SIGMA_ROW_RE.match(ln) for ln in
             (SIGMA_DIR / "README.md").read_text(encoding="utf-8").splitlines())
            if m]
    if not rows:
        sys.exit("error: no ATT&CK coverage rows found in tools/sigma-pack/README.md")
    return rows


def sigma_files_on_disk():
    """Every shipped rule and query, as paths relative to tools/sigma-pack/."""
    out = set()
    for pattern in ("rules/**/*.yml", "queries/**/*.kql"):
        for p in SIGMA_DIR.glob(pattern):
            out.add(str(p.relative_to(SIGMA_DIR)).replace("\\", "/"))
    return out


def find_sigma_problems(rows):
    """(files with no table row, table rows with no file) - both are errors."""
    listed = {r["path"] for r in rows}
    unlisted = sorted(sigma_files_on_disk() - listed)
    missing = sorted(p for p in listed if not (SIGMA_DIR / p).exists())
    return unlisted, missing


# Chainsaw refuses to load a rule whose detection map names one field twice
# with different modifiers (CommandLine|contains next to CommandLine|endswith in
# one selection, or in one list item of a selection): it prints "No valid
# detection rules were found". Sigma allows it, so sigma-cli does not catch it.
# The scan is line based, stdlib only (the hook runs the system python3), and
# reads only the detection: block of each YAML document in rules/**/*.yml.
# It sees block-style, unquoted keys only; quoted keys and flow-style maps
# ({a: 1, b: 2}) are not checked (none in the pack; see the README).
_DET_KEY_RE = re.compile(r"^(?P<indent> *)(?P<dash>- +)?(?P<key>[A-Za-z0-9_.-]+(?:\|[A-Za-z0-9_|]+)?)\s*:(?:\s|$)")


# ai-agent-config-changed-by-command copies how ai-agent-shell-risky-command
# recognises an agent. A new agent string has to reach both, so these selections
# must stay equal, line for line.
SHARED_RULE = "rules/cross-platform/ai-agent-shell-risky-command.yml"
SHARED_COPY = "rules/cross-platform/ai-agent-config-changed-by-command.yml"
SHARED_PREFIXES = ("agent_", "copilot_", "filter_ms_", "filter_claude_")
SHARED_CONDITION = (
    "1 of agent_* or (copilot_parent and not filter_ms_copilot_app)",
    "not (filter_claude_sandbox_wrapper and filter_claude_sandbox_runtime)",
)


def _selection_blocks(path):
    """{selection name: its lines}, comments left out, for one rule's detection block."""
    blocks, current, in_det = {}, None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith((" ", "-")) and line.strip():
            in_det = line.startswith("detection:")
            continue
        if not in_det or not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^    ([A-Za-z0-9_]+):", line)
        if m:
            current = m.group(1)
            blocks[current] = []
        blocks[current].append(line)
    return blocks


def shared_selection_drift():
    """What differs between the two rules' agent selections and condition clauses."""
    a = _selection_blocks(SIGMA_DIR / SHARED_RULE)
    b = _selection_blocks(SIGMA_DIR / SHARED_COPY)
    names = sorted(n for n in set(a) | set(b) if n.startswith(SHARED_PREFIXES))
    drift = [n for n in names if a.get(n) != b.get(n)]
    for clause in SHARED_CONDITION:
        if not all(clause in " ".join(blocks.get("condition", [])) for blocks in (a, b)):
            drift.append(f"condition clause: {clause}")
    return drift


def repeated_field_problems():
    """(rule path, line number, field) for each map that names a field twice."""
    out = []
    for path in sorted(SIGMA_DIR.glob("rules/**/*.yml")):
        rel = str(path.relative_to(SIGMA_DIR)).replace("\\", "/")
        in_det = False
        stack = []  # (key column, {field: first line})
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("---"):
                in_det, stack = False, []
                continue
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if not line.startswith((" ", "-")):
                in_det, stack = line.startswith("detection:"), []
                continue
            if not in_det:
                continue
            m = _DET_KEY_RE.match(line)
            if not m:
                continue
            col = len(m.group("indent")) + len(m.group("dash") or "")
            while stack and stack[-1][0] > col:
                stack.pop()
            if m.group("dash") or not stack or stack[-1][0] != col:
                if stack and stack[-1][0] == col:
                    stack.pop()  # a new list item starts a new map
                stack.append((col, {}))
            field = m.group("key").split("|", 1)[0]
            seen = stack[-1][1]
            if field in seen:
                out.append((rel, n, field))
            else:
                seen[field] = n
    return out


def md_cell_to_html(cell: str) -> str:
    """Markdown links to anchors, everything else escaped once.

    README cells already contain HTML entities (`&amp;`), so unescape before
    escaping or they double up into `&amp;amp;`.
    """
    parts, last = [], 0
    for m in MD_LINK_RE.finditer(cell):
        parts.append(he(html.unescape(cell[last:m.start()])))
        text, href = he(html.unescape(m.group(1))), he(html.unescape(m.group(2)))
        parts.append(f'<a href="{href}" target="_blank" rel="noopener" '
                     f'class="text-[#f25623] hover:text-[#f56e0f] underline underline-offset-2">{text}</a>')
        last = m.end()
    parts.append(he(html.unescape(cell[last:])))
    return "".join(parts).strip()


def render_sigma_rows(rows) -> str:
    out = []
    for r in rows:
        path, name = he(r["path"]), he(html.unescape(r["file"]))
        out.append(
            '                    <tr class="border-t border-[#525252]">\n'
            f'                        <td class="py-4 px-6"><a href="{path}" class="font-mono text-xs text-[#f25623] hover:text-[#f56e0f] break-all">{name}</a></td>\n'
            f'                        <td class="py-4 px-6 text-[#959c95] whitespace-nowrap">{md_cell_to_html(r["kind"])}</td>\n'
            f'                        <td class="py-4 px-6">{md_cell_to_html(r["attack"])}</td>\n'
            f'                        <td class="py-4 px-6 text-[#959c95]">{md_cell_to_html(r["tactic"])}</td>\n'
            f'                        <td class="py-4 px-6 font-mono text-xs text-[#959c95] whitespace-nowrap">{md_cell_to_html(r["status"])}</td>\n'
            '                    </tr>'
        )
    return "\n".join(out)


def render_footer(prefix: str) -> str:
    """The shared site footer. `prefix` is "" for root pages, "../" one deep, "../../" two.

    Links use the extensionless URLs Pages serves (x.html 308s to x, and
    dir/index.html to dir/), so `home` is "./" on root pages, not "".
    """
    p = prefix
    home = p or "./"
    return f'''<footer class="border-t border-[#525252] mt-8">
        <div class="max-w-[1280px] mx-auto px-8 py-14">
            <div class="grid grid-cols-2 md:grid-cols-5 gap-8 mb-10">
                <div class="col-span-2">
                    <a href="{home}" class="brand flex items-center gap-x-2.5 mb-4">
                        <div class="logo-badge w-7 h-7 rounded bg-gradient-to-br from-[#f25623] to-[#f56e0f] flex items-center justify-center">
                            <span class="font-bold text-[#171717] text-lg leading-none mt-px">U</span>
                        </div>
                        <span class="glitch font-semibold text-2xl tracking-[-0.03em]" data-text="UMBRASEC">UMBRASEC</span>
                    </a>
                    <p class="text-sm text-[#959c95] max-w-[300px] leading-relaxed">
                        Trace the technique. Forge the rule. An independent defensive security project - detection engineering, threat analysis, and open-source tools.
                    </p>
                </div>
                <div>
                    <div class="font-mono text-[10px] tracking-[1.5px] text-[#7d837d] uppercase mb-3">Guide</div>
                    <ul class="space-y-2 text-sm">
                        <li><a href="{p}guide/foundation" class="text-[#959c95] hover:text-[#f25623]">Foundation</a></li>
                        <li><a href="{p}guide/identity-and-access" class="text-[#959c95] hover:text-[#f25623]">Identity &amp; Access</a></li>
                        <li><a href="{p}guide/detection-and-response" class="text-[#959c95] hover:text-[#f25623]">Detection &amp; Response</a></li>
                        <li><a href="{p}guide/governance-and-maturity" class="text-[#959c95] hover:text-[#f25623]">Governance &amp; Maturity</a></li>
                    </ul>
                </div>
                <div>
                    <div class="font-mono text-[10px] tracking-[1.5px] text-[#7d837d] uppercase mb-3">Research</div>
                    <ul class="space-y-2 text-sm">
                        <li><a href="{p}research/" class="text-[#959c95] hover:text-[#f25623]">All writeups</a></li>
                        <li><a href="{p}feed.xml" class="text-[#959c95] hover:text-[#f25623]">RSS feed</a></li>
                    </ul>
                </div>
                <div>
                    <div class="font-mono text-[10px] tracking-[1.5px] text-[#7d837d] uppercase mb-3">Open Source</div>
                    <ul class="space-y-2 text-sm">
                        <li><a href="{p}tools/" class="text-[#959c95] hover:text-[#f25623]">All tools</a></li>
                        <li><a href="https://umbrasec-labs.github.io/BlueTeamMapper/" class="text-[#959c95] hover:text-[#f25623]">Blue Team Mapper</a></li>
                        <li><a href="https://umbrasec-labs.github.io/RedTeamMapper/" class="text-[#959c95] hover:text-[#f25623]">Red Team Mapper</a></li>
                        <li><a href="https://github.com/umbrasec-labs/umbrasec.dev" target="_blank" rel="noopener" class="text-[#959c95] hover:text-[#f25623]">GitHub</a></li>
                    </ul>
                </div>
            </div>
            <div class="border-t border-[#525252] pt-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div class="font-mono text-xs text-[#959c95]">
                    © 2026 UMBRASEC · <a href="{p}about" class="hover:text-[#f25623]">About</a> · <a href="{home}#contact" class="hover:text-[#f25623]">Contact</a>
                </div>
            </div>
        </div>
    </footer>'''


# ---- per-article footer nav ----------------------------------------------------

NAV_RE = re.compile(
    r'(<div class="flex flex-wrap items-center justify-between gap-4">\s*)'
    r'<a\b[^>]*>.*?</a>'
    r'(\s*<div class="flex items-center gap-2">.*?</div>\s*)'
    r'<a\b[^>]*>.*?</a>'
    r'(\s*</div>)',
    re.DOTALL,
)

_A = '<a href="{href}" class="text-sm text-[#f25623] hover:text-[#f56e0f]">{text}</a>'


def nav_prev(articles, i):
    if i + 1 < len(articles):  # an older article exists
        older = articles[i + 1]
        return _A.format(href=older['slug'], text=f"← {he(older['nav_title'])}")
    return _A.format(href="./", text="← All research")


def nav_next(articles, i):
    if i > 0:  # a newer article exists
        newer = articles[i - 1]
        return _A.format(href=newer['slug'], text=f"{he(newer['nav_title'])} →")
    return _A.format(href="./", text="All research →")


def rewrite_nav(text, prev_html, next_html, path):
    matches = NAV_RE.findall(text)
    if len(matches) != 1:
        sys.exit(f"error: expected exactly one footer nav block in {path}, found {len(matches)}")

    def repl(m):
        return m.group(1) + prev_html + m.group(2) + next_html + m.group(3)

    return NAV_RE.sub(repl, text, count=1)


# ---- article modified date -----------------------------------------------------

# The line after the match is left alone; a stale modified line right below the
# published one is swallowed so the rewrite is idempotent.
LD_PUBLISHED_RE = re.compile(
    r'^([ \t]*)("datePublished": "[^"]*",\n)(?:[ \t]*"dateModified": "[^"]*",\n)?', re.M)
META_PUBLISHED_RE = re.compile(
    r'^([ \t]*)(<meta property="article:published_time" content="[^"]*">\n)'
    r'(?:[ \t]*<meta property="article:modified_time" content="[^"]*">\n)?', re.M)


def rewrite_modified(text, updated, path):
    """Write dateModified / article:modified_time from the manifest's "updated"
    field, or remove them when it is unset."""
    for rx, label, line in (
            (LD_PUBLISHED_RE, "JSON-LD datePublished", '"dateModified": "{}",\n'),
            (META_PUBLISHED_RE, "article:published_time meta",
             '<meta property="article:modified_time" content="{}">\n')):
        if len(rx.findall(text)) != 1:
            sys.exit(f"error: expected exactly one {label} line in {path}")
        text = rx.sub(lambda m: m.group(1) + m.group(2)
                      + (m.group(1) + line.format(updated) if updated else ""), text, count=1)
    return text


# ---- shared footer -------------------------------------------------------------

FOOTER_RE = re.compile(r'<footer\b.*?</footer>', re.DOTALL)


def rewrite_footer(text, footer_html, path):
    n = len(FOOTER_RE.findall(text))
    if n != 1:
        sys.exit(f"error: expected exactly one <footer> in {path}, found {n}")
    return FOOTER_RE.sub(lambda m: footer_html, text, count=1)


def site_pages():
    """Every standard site page that carries the shared chrome (nav + footer)."""
    pages = ["index.html", "about.html", "tools/index.html",
             "tools/sigma-pack/index.html"]
    for sub in ("guide", "research"):
        pages += sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / sub).glob("*.html"))
    seen, out = set(), []
    for rel in pages:
        if rel not in seen and (ROOT / rel).exists():
            seen.add(rel)
            out.append(rel)
    return out


# ---- driver --------------------------------------------------------------------

def find_orphans(articles):
    """research/*.html pages on disk that no manifest entry points to.

    These are articles that were dropped into research/ but never registered in
    research/articles.json, so nothing links to them - they are unreachable from
    the homepage, grid, feed, sitemap, and palette. research/index.html is the
    generated grid, not an article, so it is excluded."""
    slugs = {a["slug"] for a in articles}
    orphans = []
    for p in sorted((ROOT / "research").glob("*.html")):
        if p.stem == "index" or p.stem in slugs:
            continue
        orphans.append(p.relative_to(ROOT))
    return orphans


def csp_hash_problems():
    """Inline scripts in 404.html whose sha256 is not allowed by the CSP in _headers.

    The CSP (Report-Only for now) allows inline script by hash, so an edit to the
    404 script that does not update _headers would be blocked once it is enforced."""
    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    page = (ROOT / "404.html").read_text(encoding="utf-8")
    missing = []
    for body in re.findall(r"<script>(.*?)</script>", page, re.DOTALL):
        token = "sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()
        if f"'{token}'" not in headers:
            missing.append(token)
    return missing


# The homepage hero's trace-to-rule reel is generated from the pack, the Claims
# Ledger and hero-reel.json (see hero_reel.py). The claims live in the
# detections repo, so the reel is rebuilt and checked only where that checkout
# sits next to this one (the workspace); a lone clone leaves it as committed.
DETECTIONS_CLAIMS = ROOT.parent / "detections" / "claims"
REEL_MANIFEST = ROOT / "tools" / "site-build" / "hero-reel.json"


PRE_RE = re.compile(r"<pre\b.*?</pre>", re.DOTALL)
# an internal href (relative, root-relative or on umbrasec.dev) that ends in .html
HTML_HREF_RE = re.compile(r'href="((?:https://umbrasec\.dev/|(?![a-z]+:|//|#))[^"#?]*\.html(?:[#?][^"]*)?)"')


def html_link_problems():
    """Internal links still written as x.html (Pages 308s them); code blocks are skipped."""
    found = []
    for rel in site_pages() + ["404.html"]:
        text = PRE_RE.sub("", (ROOT / rel).read_text(encoding="utf-8"))
        found += [(rel, h) for h in HTML_HREF_RE.findall(text)]
    return found


# Search engines cut the snippet at about 155-160 characters. Only the plain
# meta description is checked; og:description and twitter:description are
# separate, often longer texts.
DESC_MAX = 160
META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"')


def description_problems():
    """(page, decoded length) for each page whose meta description is missing,
    repeated, or longer than DESC_MAX. Length counts the decoded text, so
    &amp; is one character."""
    found = []
    for rel in site_pages() + ["404.html"]:
        descs = META_DESC_RE.findall((ROOT / rel).read_text(encoding="utf-8"))
        if len(descs) != 1:
            found.append((rel, f"{len(descs)} meta descriptions, expected 1"))
            continue
        n = len(html.unescape(descs[0]))
        if n > DESC_MAX:
            found.append((rel, f"{n} characters"))
    return found


def build(check: bool, list_drift: bool = False) -> int:
    articles = load_articles()
    transforms = {}  # rel path -> list of text->text callables, applied in order

    def add(rel, fn):
        transforms.setdefault(rel, []).append(fn)

    # homepage: hero CTA + featured trio
    add("index.html", lambda t: replace_region(t, "hero", render_hero(articles), ROOT / "index.html"))
    add("index.html", lambda t: replace_region(t, "featured", render_home_rows(articles), ROOT / "index.html"))

    # research index: filter chips + card grid + count
    add("research/index.html", lambda t: replace_region(t, "filters", render_filters(articles), ROOT / "research/index.html"))
    add("research/index.html", lambda t: replace_region(t, "cards", render_cards(articles), ROOT / "research/index.html"))
    add("research/index.html", lambda t: replace_region(t, "count", render_count(articles), ROOT / "research/index.html"))

    # feed + sitemap + command palette
    add("feed.xml", lambda t: replace_region(t, "builddate", render_builddate(articles), ROOT / "feed.xml"))
    add("feed.xml", lambda t: replace_region(t, "items", render_feed_items(articles), ROOT / "feed.xml"))
    add("sitemap.xml", lambda t: replace_region(t, "research", render_sitemap(articles), ROOT / "sitemap.xml"))
    add("assets/umbra.js", lambda t: replace_region(t, "articles", render_palette(articles), ROOT / "assets/umbra.js"))

    # sigma-pack index table, from the README's ATT&CK coverage table
    sigma_rows = load_sigma_rows()
    add("tools/sigma-pack/index.html",
        lambda t: replace_region(t, "sigmapack",
                                 "\n" + render_sigma_rows(sigma_rows) + "\n                    ",
                                 ROOT / "tools/sigma-pack/index.html"))

    # homepage trace-to-rule reel, from the pack and the detections claims
    reel_digest = hero_reel.source_digest(REEL_MANIFEST, SIGMA_DIR)
    reel_stale = False
    if DETECTIONS_CLAIMS.is_dir():
        exs = hero_reel.render_reel(REEL_MANIFEST, sigma_rows, sigma_files_on_disk(), SIGMA_DIR, DETECTIONS_CLAIMS)
        add("index.html", lambda t: replace_region(t, "reel", hero_reel.render_reel_html(exs, reel_digest), ROOT / "index.html"))
        add("index.html", lambda t: replace_region(t, "reelhead", hero_reel.render_reel_head(exs), ROOT / "index.html"))
    else:
        # no claims here: the reel cannot be rebuilt, but a pack edit since it
        # was built still shows as a changed source hash
        m = hero_reel.DIGEST_RE.search((ROOT / "index.html").read_text(encoding="utf-8"))
        reel_stale = not m or m.group(1) != reel_digest
        if not list_drift:
            print("site-build: note - ../detections/claims not found; the hero reel was not rebuilt.", file=sys.stderr)

    # per-article prev/next nav
    for i, a in enumerate(articles):
        rel = f"research/{a['slug']}.html"
        if not (ROOT / rel).exists():
            sys.exit(f"error: manifest references {rel} but the file does not exist")
        add(rel, lambda t, i=i, rel=rel: rewrite_nav(t, nav_prev(articles, i), nav_next(articles, i), ROOT / rel))
        add(rel, lambda t, a=a, rel=rel: rewrite_modified(t, a.get("updated"), ROOT / rel))

    # shared footer on every site page (depth-aware relative links)
    for rel in site_pages():
        prefix = "../" * rel.count("/")
        add(rel, lambda t, pre=prefix, rel=rel: rewrite_footer(t, render_footer(pre), ROOT / rel))

    changes = []
    for rel, fns in transforms.items():
        path = ROOT / rel
        old = path.read_text(encoding="utf-8")
        new = old
        for fn in fns:
            new = fn(new)
        if new != old:
            changes.append((path, new))

    # Hook helper: name the files a regeneration would rewrite, one per line,
    # so the pre-commit hook can check and stage exactly those.
    if list_drift:
        for path, _ in changes:
            print(path.relative_to(ROOT).as_posix())
        return 0

    orphans = find_orphans(articles)
    sigma_unlisted, sigma_missing = find_sigma_problems(sigma_rows)
    repeated_fields = repeated_field_problems()
    shared_drift = shared_selection_drift()
    # every page needs the skip link and the <main> landmark it targets; a new
    # page copied from an old template would silently drop them
    no_main = [rel for rel in site_pages() + ["404.html"]
               if not all(s in (ROOT / rel).read_text(encoding="utf-8")
                          for s in ('<a href="#main" class="skip-link">', '<main id="main">'))]
    bad_hashes = csp_hash_problems()
    html_links = html_link_problems()
    long_descs = description_problems()

    if check:
        problems = False
        if orphans:
            print("site-build: ORPHAN - research pages not listed in research/articles.json:")
            for rel in orphans:
                print(f"  - {rel}")
            print("\nAdd an entry to research/articles.json (then regenerate), or delete the file.")
            problems = True
        if sigma_unlisted:
            print("site-build: ORPHAN - sigma-pack files missing from the ATT&CK table in tools/sigma-pack/README.md:")
            for rel in sigma_unlisted:
                print(f"  - {rel}")
            print("\nAdd a table row (then regenerate), or delete the file.")
            problems = True
        if sigma_missing:
            print("site-build: DANGLING - ATT&CK table rows pointing at files that do not exist:")
            for rel in sigma_missing:
                print(f"  - {rel}")
            print("\nFix the path in tools/sigma-pack/README.md, or remove the row.")
            problems = True
        if shared_drift:
            print(f"site-build: SIGMA - {SHARED_COPY} differs from {SHARED_RULE} in:")
            for name in shared_drift:
                print(f"  - {name}")
            print("\nCopy the selection across, so both rules know the same agents.")
            problems = True
        if repeated_fields:
            print("site-build: SIGMA - a detection map names one field twice (Chainsaw will not load the rule):")
            for rel, n, field in repeated_fields:
                print(f"  - {rel}:{n}: {field}")
            print("\nSplit it into list items or separate selections joined in the condition (see tools/site-build/README.md).")
            problems = True
        if reel_stale:
            print("site-build: HERO - a sigma-pack file or hero-reel.json changed since the homepage reel was built.")
            print("\nRegenerate where ../detections sits next to this repo (the workspace): python3 tools/site-build/build_indexes.py")
            problems = True
        if no_main:
            print("site-build: MISSING - pages without the skip link or <main id=\"main\">:")
            for rel in no_main:
                print(f"  - {rel}")
            print("\nCopy both from an existing page (first child of <body>, and <main> between </nav> and <footer>).")
            problems = True
        if html_links:
            print("site-build: LINKS - internal links written as .html (each one is a 308 redirect):")
            for rel, h in html_links:
                print(f"  - {rel}: {h}")
            print("\nUse the served URL: x.html -> x, dir/index.html -> dir/, index.html -> ./ (see tools/site-build/README.md).")
            problems = True
        if long_descs:
            print(f"site-build: DESCRIPTION - meta description missing, repeated or over {DESC_MAX} characters:")
            for rel, why in long_descs:
                print(f"  - {rel}: {why}")
            print(f"\nGive each page one <meta name=\"description\"> of at most {DESC_MAX} characters (about 155 is the target).")
            problems = True
        if bad_hashes:
            print("site-build: CSP - 404.html inline script hash not in _headers:")
            for token in bad_hashes:
                print(f"  - '{token}'")
            print("\nReplace the old sha256-... in the Content-Security-Policy lines of _headers with this one.")
            problems = True
        if changes:
            print("site-build: DRIFT - these files are out of sync with research/articles.json:")
            for path, _ in changes:
                print(f"  - {path.relative_to(ROOT)}")
            print("\nRun:  python3 tools/site-build/build_indexes.py   then commit the result.")
            problems = True
        if problems:
            return 1
        print(f"site-build: OK - {len(articles)} articles, all derived files in sync.")
        return 0

    for path, new in changes:
        path.write_text(new, encoding="utf-8")
        print(f"  updated {path.relative_to(ROOT)}")
    if not changes:
        print(f"site-build: nothing to do - {len(articles)} articles already in sync.")
    else:
        print(f"site-build: regenerated {len(changes)} file(s) from {len(articles)} articles.")
    # Regeneration cannot register an orphan (it has no metadata for it), so warn
    # loudly; --check (the pre-commit hook gate) is what enforces this.
    if orphans:
        print("site-build: WARNING - orphaned research pages not in research/articles.json:")
        for rel in orphans:
            print(f"  - {rel}")
        print("Add them to the manifest or delete them; the hook will fail while they exist.")
    for label, items, fix in (
        ("sigma-pack files missing from the ATT&CK table", sigma_unlisted, "Add a table row"),
        ("ATT&CK table rows with no matching file", sigma_missing, "Fix or remove the row"),
    ):
        if items:
            print(f"site-build: WARNING - {label}:")
            for rel in items:
                print(f"  - {rel}")
            print(f"{fix} in tools/sigma-pack/README.md; the hook will fail while this stands.")
    if shared_drift:
        print(f"site-build: WARNING - {SHARED_COPY} differs from {SHARED_RULE} in: {', '.join(shared_drift)}")
        print("Copy the selection across; the hook will fail while this stands.")
    if repeated_fields:
        print("site-build: WARNING - a detection map names one field twice (Chainsaw will not load the rule):")
        for rel, n, field in repeated_fields:
            print(f"  - {rel}:{n}: {field}")
        print("Split it; the hook will fail while this stands.")
    if reel_stale:
        print("site-build: WARNING - the homepage reel is older than the sigma-pack; regenerate it in the workspace.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Regenerate UMBRASEC derived lists from research/articles.json")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 if any file is out of sync (writes nothing)")
    mode.add_argument("--list-drift", action="store_true", help="print the files a regeneration would rewrite (writes nothing)")
    args = ap.parse_args()
    sys.exit(build(args.check, args.list_drift))


if __name__ == "__main__":
    main()
