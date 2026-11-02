"""
kev_coverage.py - what UMBRASEC has published against each CVE.

tools/site-build/kev-coverage.json is hand-kept: one entry per CVE named in a
pack rule, a pack query or a research article. The tier is a human judgement,
because a rule that merely mentions a CVE is not coverage:

  rule     a pack rule detects exploitation of this CVE
  partial  a pack rule covers only part of it
  writeup  an article has hunt or detection content, with no pack rule for it
  none     named in our work but not covered, for example cited for context

The generator turns that into assets/kev-coverage.json, which /api/exploited
reads, and the Detections shipped cards on /exploited. problems() is what
--check runs, so a tier cannot quietly outlive the rule or article behind it.
The kev flag is checked online by tools/local-sync/sync-exploited.mjs.
"""

import html
import json
import re
from pathlib import Path

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.DOTALL | re.IGNORECASE)
DASH_RE = re.compile("[\u2013\u2014]")

TIERS = ("rule", "partial", "writeup", "none")
NEEDS_RULE = ("rule", "partial")
NEEDS_ARTICLE = ("rule", "partial", "writeup")

RULE_URL = "https://github.com/umbrasec-labs/umbrasec.dev/blob/master/tools/sigma-pack/"


def load_mapping(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def _article_text(path: Path) -> str:
    return SCRIPT_RE.sub("", path.read_text(encoding="utf-8"))


def _pack_files(pack_dir: Path):
    for sub in ("rules", "queries"):
        for path in sorted((pack_dir / sub).rglob("*")):
            if path.is_file():
                yield path


def named_cves(pack_dir: Path, research_dir: Path) -> set:
    """Every CVE a pack rule, pack query or research page names."""
    found = set()
    for path in _pack_files(pack_dir):
        found |= set(CVE_RE.findall(path.read_text(encoding="utf-8")))
    for path in sorted(research_dir.glob("*.html")):
        found |= set(CVE_RE.findall(_article_text(path)))
    return found


def _names(text: str, cve: str) -> bool:
    return re.search(re.escape(cve) + r"(?!\d)", text) is not None


def _has_tag(text: str, technique: str) -> bool:
    return re.search(r"attack\." + re.escape(technique.lower()) + r"(?![.\d])", text.lower()) is not None


def _rule_problems(e: dict, pack_dir: Path) -> list:
    found, texts = [], []
    for rel in e.get("rules") or []:
        path = pack_dir / rel
        if not path.is_file():
            found.append(f"{e['cve']}: rule {rel} does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        texts.append(text)
        if not _names(text, e["cve"]):
            found.append(f"{e['cve']}: rule {rel} does not name this CVE")
    for technique in e.get("attack") or []:
        if not any(_has_tag(t, technique) for t in texts):
            found.append(f"{e['cve']}: {technique} is not in the tags of its rules")
    return found


def _article_problems(e: dict, research_dir: Path, slugs: set) -> list:
    slug = e.get("article")
    if not slug:
        return []
    if slug not in slugs:
        return [f"{e['cve']}: article {slug} is not in research/articles.json"]
    if not _names(_article_text(research_dir / f"{slug}.html"), e["cve"]):
        return [f"{e['cve']}: article {slug} does not name this CVE"]
    return []


def problems(mapping: list, named: set, pack_dir: Path, research_dir: Path, articles: list) -> list:
    found = []
    mapped = [e["cve"] for e in mapping]
    for cve in sorted(named - set(mapped)):
        found.append(f"{cve}: named in the pack or a research page, but not in kev-coverage.json")
    for cve in sorted(set(mapped) - named):
        found.append(f"{cve}: in kev-coverage.json, but nothing names it any more")
    for cve in sorted({c for c in mapped if mapped.count(c) > 1}):
        found.append(f"{cve}: listed more than once")

    slugs = {a["slug"] for a in articles}
    for e in mapping:
        cve, tier = e["cve"], e.get("tier")
        if tier not in TIERS:
            found.append(f"{cve}: tier must be one of {', '.join(TIERS)}, not {tier!r}")
        if not isinstance(e.get("kev"), bool):
            found.append(f"{cve}: kev must be true or false")
        for field in ("label", "note"):
            value = e.get(field) or ""
            if not value.strip():
                found.append(f"{cve}: {field} is empty")
            if DASH_RE.search(value):
                found.append(f"{cve}: {field} has an en or em dash")
        if tier in NEEDS_RULE and not e.get("rules"):
            found.append(f"{cve}: tier {tier} needs a rule")
        if tier in NEEDS_ARTICLE and not e.get("article"):
            found.append(f"{cve}: tier {tier} needs an article")
        found += _rule_problems(e, pack_dir)
        found += _article_problems(e, research_dir, slugs)
    return found


def claim_count(rule_path: str, claims_dir: Path) -> int:
    """How many claims the ledger holds for this rule. Needs PyYAML, as hero_reel does."""
    import yaml

    path = claims_dir / f"{Path(rule_path).stem}.yml"
    if not path.is_file():
        return 0
    return len(yaml.safe_load(path.read_text(encoding="utf-8")).get("claims") or [])


def render_asset(mapping: list, articles: list, claims_dir, committed) -> str:
    """assets/kev-coverage.json. Without a claims checkout, committed counts stand."""
    titles = {a["slug"]: a["palette"]["label"] for a in articles}
    kept = {e["cve"]: e.get("claims", 0) for e in (committed or {}).get("entries", [])}
    out = []
    for e in mapping:
        rules = e.get("rules") or []
        slug = e.get("article")
        claims = sum(claim_count(r, claims_dir) for r in rules) if claims_dir else kept.get(e["cve"], 0)
        out.append({
            "cve": e["cve"],
            "tier": e["tier"],
            "kev": e["kev"],
            "label": e["label"],
            "note": e["note"],
            "rules": [{"name": Path(r).name, "url": RULE_URL + r} for r in rules],
            "article": {"title": titles[slug], "url": f"/research/{slug}"} if slug else None,
            "attack": e.get("attack") or [],
            "claims": claims,
        })
    return json.dumps({"entries": out}, indent=2) + "\n"


TIER_LABELS = {"rule": "Rule", "partial": "Partial rule", "writeup": "Writeup"}


def render_cards(entries: list) -> str:
    """The Detections shipped cards, from assets/kev-coverage.json entries. Static
    HTML, so they survive no JavaScript and an upstream outage. assets/exploited.js
    adds the date added and EPSS to each card's meta line."""
    esc = lambda s: html.escape(str(s), quote=True)
    cards = []
    shown = [e for e in entries if e["kev"] and e["tier"] in TIER_LABELS]
    for e in sorted(shown, key=lambda e: list(TIER_LABELS).index(e["tier"])):
        meta = []
        if e["claims"]:
            meta.append(f'<span>{e["claims"]} tested claims</span>')
        if e["attack"]:
            meta.append(f'<span>{esc(" ".join(e["attack"]))}</span>')
        links = [f'<a class="mono" href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(r["name"])}</a>' for r in e["rules"]]
        links.append(f'<a href="{esc(e["article"]["url"])}">{esc(e["article"]["title"])}</a>')
        cards.append(f"""                <article class="card" data-cve="{esc(e["cve"])}">
                    <div class="top"><span class="cve">{esc(e["cve"])}</span><span class="tag"><span class="sw tier-{e["tier"]}"></span>{TIER_LABELS[e["tier"]]}</span></div>
                    <div class="prod">{esc(e["label"])}</div>
                    <p class="note">{esc(e["note"])}</p>
                    <div class="meta">{"".join(meta)}</div>
                    <div class="links">{"".join(links)}</div>
                </article>""")
    return "\n" + "\n".join(cards) + "\n                "


NAV_RE = re.compile(r'<nav aria-label="Site".*?</nav>', re.DOTALL)


def nav_problems(pages: list, root: Path) -> list:
    """Pages whose site nav has no link to /exploited."""
    found = []
    for rel in pages:
        nav = NAV_RE.search((root / rel).read_text(encoding="utf-8"))
        if not nav or ">Exploited now</a>" not in nav.group(0):
            found.append(rel)
    return found
