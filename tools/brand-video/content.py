"""Every string the brand film shows, checked against the repo it comes from.

load() refuses to build the film on any mismatch: a quote that is no longer
word for word, a CVE the site no longer names, a rule line that changed, a
tile list that drifted from the hero reel, a KEV wall whose CVE is no longer
shown on /exploited as the film shows it, or a Claims Ledger report that is
stale or not all green. Numbers (pack counts, KEV total, claims) are read from
the repos at render time, never typed in.
"""
from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path


class FactError(Exception):
    """A fact on screen no longer matches its source."""


@dataclass(frozen=True)
class Source:
    label: str
    title: str
    before: str
    mark: str
    after: str


@dataclass(frozen=True)
class Content:
    agent_cves: tuple[str, ...]
    signals: tuple[str, ...]
    kev_total: int
    sources: tuple[Source, Source, Source]
    technique: str
    technique_name: str
    trace_lines: tuple[str, ...]
    rule_lines: tuple[str, ...]
    rule_path: str
    claim_name: str
    claims_executed: int
    claims_passed: int
    article_title: str
    article_eyebrow: str
    article_url: str
    pack_sigma: int
    pack_kql: int
    tiles: tuple[str, ...]
    # "Exploited now": the KEV snapshot joined to the coverage map, as /exploited does
    kev_date: str                        # the snapshot's day, ISO
    kev_days: int                        # the window: days from its cut to that day
    kev_wall: tuple[tuple[str, str], ...]   # (CVE, tier) per entry added in the window, newest first
    kev_tiers: tuple[tuple[str, str, int], ...]   # (tier, the site's label, count)
    kev_cve: str
    kev_tier: str
    kev_tier_label: str
    kev_product: str
    kev_added: str
    kev_note: str
    kev_rule: str
    kev_claims: int


ARTICLE = "research/detecting-hijacked-ai-coding-agents.html"
ARTICLE_TITLE = "What a Hijacked AI Coding Agent Leaves in Your Logs"
# the article header's category label, shown above its title in the film
ARTICLE_EYEBROW = "AI & LLM Security"
ARTICLE_URL = "umbrasec.dev/research/detecting-hijacked-ai-coding-agents"
RULE = "tools/sigma-pack/rules/cross-platform/ai-agent-shell-risky-command.yml"
CLAIM = "catches/claude-parent-credential-read"
TECHNIQUE = "T1552.001"
TECHNIQUE_NAME = "Credentials In Files"
MAX_CLAIMS_AGE_DAYS = 14

# The KEV entry "Exploited now" locks on. The film shows the tier the site
# gives it and the site's own note on what the rule does not cover.
KEV_CVE = "CVE-2026-109619"
KEV_TIER = "partial"
KEV_TIERS = ("rule", "partial", "writeup", "gap")   # the order /exploited lists them in

AGENT_CVES = ("CVE-2025-8217", "CVE-2025-53773", "CVE-2025-54135",
              "CVE-2025-54136", "CVE-2026-110202")
OTHER_CVES = ("CVE-2026-102764", "CVE-2026-42271")
FIELD_TECHNIQUES = ("T1558.003", "T1490", "T1190")
BINANCE = "BINANCE $6.3B"

# The three real cases the write-up names. before + mark + after is word for
# word in the article and runs to the end of its sentence, so nothing that
# qualifies it is cut; mark is the highlighted phrase. The words are the
# write-up's own account of each case, so a card is headed "Case", not
# "Source".
SOURCES = (
    Source("Case 1 · Nx s1ngularity, Aug 2025", "Malicious package versions",
           "started whichever agent CLI was installed, headless and with its "
           "permission prompts switched off, and told it to ",
           "inventory secrets and wallet files", "."),
    Source("Case 2 · CVE-2025-8217", "Amazon Q Developer for VS Code 1.84.0",
           "shipped with an injected instruction to run the Q CLI with ",
           "every tool trusted and no interaction",
           "; it did not run because of a syntax error."),
    Source("Case 3 · CVE-2026-110202", "Roo Code",
           "the third shape: ", "planted text in content the agent reads",
           ", and an auto-approve allowlist that the shell reads differently."),
)

# The hero reel's second slide (index.html, data-tr-id="T1552.001").
TRACE_LINES = (
    "_synthetic: true",
    "ParentImage:",
    "  /home/dev/.local/share/claude/versions/2.1.310",
    "CommandLine:",
    "  \"/usr/bin/bash -c 'cat ~/.aws/credentials'\"",
)

# Real lines of the rule. "..." marks lines left out, as the hero reel does:
# the detection part is the reel's slide line for line, and the one tag shown
# keeps marks for the tags around it. The condition is the real one,
# shortened.
RULE_LINES = (
    "title: AI Coding Agent Shell Runs a Risky Command",
    "tags:",
    "  ...",
    "  - attack.t1552.001",
    "  ...",
    "detection:",
    "  agent_parent:",
    "    ...",
    "    - ParentImage|contains:",
    "        - '/.local/share/claude/versions/'",
    "        ...",
    "  risk_credential:",
    "    - CommandLine|contains:",
    "        - '.aws/credentials'",
    "        ...",
    "  condition: (1 of agent_* or ...)",
    "    and (1 of risk_* or ...) and not ...",
    "level: high",
)


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def text_of(path: Path) -> str:
    """Visible text of an HTML file, tags dropped, entities decoded."""
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    return squash(html.unescape(re.sub(r"<[^>]+>", "", raw)))


def reel_rule_lines(index_raw: str, technique: str) -> list[str]:
    """The rule panel of the hero reel's slide for a technique, line by line."""
    start = index_raw.index(f'data-tr-id="{technique}"')
    panel = index_raw[index_raw.index("tr-panel tr-rule", start):]
    panel = panel[:panel.index("tr-foot")]
    return [squash(html.unescape(re.sub(r"<[^>]+>", "", ln)))
            for ln in re.findall(r'<div class="ln[^"]*">(.*?)</div>', panel)]


def rule_tags(rule_raw: str) -> list[str]:
    block = re.search(r"^tags:\n((?:[ \t]+- .*\n)+)", rule_raw, flags=re.M)
    return re.findall(r"- (\S+)", block.group(1)) if block else []


def _need(cond: bool, what: str) -> None:
    if not cond:
        raise FactError(what)


def _claims(path: Path, pack_total: int) -> tuple[int, int, dict]:
    _need(path.is_file(), f"no Claims Ledger report at {path}; re-run the harness")
    data = json.loads(path.read_text(encoding="utf-8"))
    s = data.get("summary", {})
    made = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - made).days
    _need(age <= MAX_CLAIMS_AGE_DAYS,
          f"Claims Ledger report is {age} days old; re-run the harness")
    _need(data.get("ok") is True and s.get("failed") == 0,
          "Claims Ledger report is not all green")
    _need(s.get("rules") == pack_total,
          f"Claims Ledger covers {s.get('rules')} rules, the pack has {pack_total}")
    executed, passed = int(s["executed"]), int(s["passed"])
    _need(executed == passed > 0, f"claims: {passed} of {executed} passed")
    return executed, passed, data.get("rules", {})


def site_date(iso: str) -> str:
    """The site's date style, as in the article headers: Nov 6, 2026."""
    d = date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def tier_labels(exploited_js: str) -> dict[str, str]:
    """The names /exploited gives the tiers (TIERS in assets/exploited.js)."""
    m = re.search(r"const TIERS = \{([^}]*)\}", exploited_js)
    _need(m is not None, "assets/exploited.js no longer has a TIERS table")
    return dict(re.findall(r'(\w+): "([^"]+)"', m.group(1)))


def kev_wall(feed: dict, coverage: dict) -> tuple[tuple[str, str], ...]:
    """Each entry added in the window with its tier, joined the way
    functions/api/exploited.js joinCoverage does: a "none" entry, an unmapped
    CVE and a tier name the page does not know are all a gap."""
    tier_of = {e["cve"]: e["tier"] for e in coverage["entries"] if e["tier"] != "none"}

    def tier(cve: str) -> str:
        t = tier_of.get(cve)
        return t if t in KEV_TIERS else "gap"
    return tuple((r["cve"], tier(r["cve"])) for r in feed["rows"])


def _kev(site: Path, feed: dict, claim_rules: dict) -> dict:
    """The facts of "Exploited now", from the snapshot and the coverage map as
    they are at render time."""
    coverage = json.loads((site / "assets" / "kev-coverage.json").read_text(encoding="utf-8"))
    wall = kev_wall(feed, coverage)
    _need(len(wall) > 0, "the KEV snapshot has no entries in its window")
    _need(len({cve for cve, _ in wall}) == len(wall), "the KEV snapshot lists a CVE twice")
    for cve, tier in wall:
        _need(re.fullmatch(r"CVE-\d{4}-\d{4,}", cve) is not None, f"not a CVE id: {cve!r}")
        _need(tier in KEV_TIERS, f"{cve}: unknown tier {tier!r}")
    labels = tier_labels((site / "assets" / "exploited.js").read_text(encoding="utf-8"))
    _need(set(labels) == set(KEV_TIERS), f"/exploited now has the tiers {sorted(labels)}")
    tiers = tuple((t, labels[t], sum(1 for _, x in wall if x == t)) for t in KEV_TIERS)
    days = (date.fromisoformat(feed["generated"]) - date.fromisoformat(feed["cut"])).days
    _need(days > 0, "the KEV snapshot's window is empty")

    row = next((r for r in feed["rows"] if r["cve"] == KEV_CVE), None)
    _need(row is not None, f"{KEV_CVE} is no longer in the KEV snapshot's window")
    entry = next((e for e in coverage["entries"] if e["cve"] == KEV_CVE), None)
    _need(entry is not None and entry.get("kev") is True,
          f"{KEV_CVE} is not a KEV entry in the coverage map")
    # the film says "Partial rule" and nothing stronger: any other tier stops the render
    _need(entry["tier"] == KEV_TIER,
          f"{KEV_CVE} is tier {entry['tier']!r} now; the film shows it as {KEV_TIER!r}")
    product = f"{row['vendor']} {row['product']}".strip()
    _need(product == entry["label"], f"{KEV_CVE}: the snapshot says {product!r}, "
                                     f"the coverage map {entry['label']!r}")
    note = entry.get("note", "")
    _need(bool(note), f"{KEV_CVE} has no note on what its rule leaves out")
    _need(len(entry["rules"]) == 1, f"{KEV_CVE} now maps to {len(entry['rules'])} rules; "
                                    "the film's card shows one")
    rule = entry["rules"][0]["name"]
    rule_files = list((site / "tools" / "sigma-pack" / "rules").rglob(rule))
    _need(len(rule_files) == 1, f"{rule} is not one file in the pack")
    rec = claim_rules.get(Path(rule).stem)
    _need(rec is not None and rec.get("status") == "verified",
          f"the Claims Ledger report does not verify {rule}")
    claims = sum(rec["counts"].values())
    _need(claims == entry.get("claims") and claims > 0,
          f"{rule}: the report has {claims} claims, the coverage map {entry.get('claims')}")
    # /exploited shows the same card: same tier name, note, rule file and claim count
    page = text_of(site / "exploited.html")
    for s in (KEV_CVE, labels[KEV_TIER], product, note, rule, f"{claims} tested claims"):
        _need(s in page, f"/exploited no longer shows {s!r}")
    return dict(kev_date=feed["generated"], kev_days=days, kev_wall=wall, kev_tiers=tiers,
                kev_cve=KEV_CVE, kev_tier=KEV_TIER, kev_tier_label=labels[KEV_TIER],
                kev_product=product, kev_added=row["added"], kev_note=note, kev_rule=rule,
                kev_claims=claims)


MONTHS = dict(Jan="January", Feb="February", Mar="March", Apr="April", May="May",
              Jun="June", Jul="July", Aug="August", Sep="September", Oct="October",
              Nov="November", Dec="December")


def _case_card(art_text: str, s: Source) -> None:
    """The card's case and title belong to the sentence its quote comes from:
    "Case 2 · CVE-X" over "Product" needs "Product (CVE-X" there; "Case 1 · Name,
    Aug 2025" needs every word of Name and "(August 2025)" there."""
    quote = squash(s.before + s.mark + s.after)
    start = art_text.index(quote)
    sentence = art_text[art_text.rfind(". ", 0, start) + 2:start + len(quote)]
    case = s.label.split(" · ", 1)[1]
    _need(s.title.lower() in sentence.lower(),
          f"card title {s.title!r} is not in its case's sentence")
    if re.fullmatch(r"CVE-\d{4}-\d+", case):
        _need(f"{s.title} ({case}" in sentence,
              f"{case} is not the article's CVE for {s.title!r}")
        return
    name, when = case.rsplit(", ", 1)
    for word in name.split():
        _need(word in sentence, f"{word!r} is not in its case's sentence")
    month, year = when.split()
    _need(f"({MONTHS.get(month, month)} {year})" in sentence,
          f"case date {when!r} is not the article's")


def load(site: Path, detections: Path) -> Content:
    site, detections = Path(site), Path(detections)
    article = site / ARTICLE
    art_text = text_of(article)
    for s in SOURCES:
        quote = squash(s.before + s.mark + s.after)
        _need(quote in art_text, f"quote no longer word for word: {quote!r}")
        end = art_text.index(quote) + len(quote)
        _need(quote.endswith(".") and re.match(r" [A-Z]|$", art_text[end:end + 2]),
              f"quote stops before its sentence ends: {quote!r}")
        _case_card(art_text, s)
    _need(ARTICLE_TITLE in art_text, f"article title changed: {ARTICLE_TITLE!r}")
    _need(ARTICLE_EYEBROW.upper() in art_text.upper(),
          f"article category label changed: {ARTICLE_EYEBROW!r}")
    art_raw = article.read_text(encoding="utf-8")
    for cve in AGENT_CVES:
        _need(cve in art_raw, f"{cve} is not in {ARTICLE}")
    research = " ".join(p.read_text(encoding="utf-8")
                        for p in sorted((site / "research").glob("*.html")))
    for cve in OTHER_CVES:
        _need(cve in research, f"{cve} is not in research/")
    _need("$6.3B" in research, "the Binance article no longer says $6.3B")

    index_raw = (site / "index.html").read_text(encoding="utf-8")
    index_text = text_of(site / "index.html")
    tiles = tuple(re.findall(r'data-tr-id="([^"]+)"', index_raw))
    for t in FIELD_TECHNIQUES + (TECHNIQUE,):
        _need(t in tiles, f"{t} is not in the hero reel")
    _need(TECHNIQUE_NAME in index_text, f"the site no longer names {TECHNIQUE} {TECHNIQUE_NAME!r}")
    for s in ("/home/dev/.local/share/claude/versions/2.1.310",
              "/usr/bin/bash -c 'cat ~/.aws/credentials'", CLAIM):
        _need(s in index_text, f"hero reel no longer shows {s!r}")

    rule_raw = (site / RULE).read_text(encoding="utf-8")
    rule = squash(rule_raw)
    for line in RULE_LINES:
        s = line.strip()
        if s == "..." or s.startswith("condition:") or s.startswith("and ("):
            continue
        s = s.removeprefix("- ")
        _need(squash(s) in rule, f"rule line not in {RULE}: {s!r}")
    film = [ln.strip() for ln in RULE_LINES]
    reel = reel_rule_lines(index_raw, TECHNIQUE)
    _need("agent_parent:" in film and len(reel) > 5
          and film[film.index("agent_parent:"):][:len(reel)] == reel,
          "the rule excerpt no longer matches the hero reel's slide line for line")
    tags = rule_tags(rule_raw)
    tag = f"attack.{TECHNIQUE.lower()}"
    _need(tag in tags, f"{tag} is no longer a tag of the rule")
    i = tags.index(tag)
    want = (["..."] if i > 0 else []) + [f"- {tag}"] + (["..."] if i < len(tags) - 1 else [])
    _need("tags:" in film and "detection:" in film
          and film[film.index("tags:") + 1:film.index("detection:")] == want,
          "the tag excerpt does not mark the tags it leaves out")
    cond = re.search(r"^\s*condition:\s*(.+)$", rule_raw, flags=re.M)
    _need(cond is not None and cond.group(1).startswith("(1 of agent_* or ")
          and ") and (1 of risk_* or " in cond.group(1)
          and ") and not (" in cond.group(1),
          "the rule's condition no longer has the shape the film shortens")

    pack = site / "tools" / "sigma-pack"
    sigma = len(list((pack / "rules").rglob("*.yml")))
    kql = len(list((pack / "queries").rglob("*.kql")))
    _need(len(tiles) == sigma + kql,
          f"hero reel has {len(tiles)} slides, the pack has {sigma + kql} files")

    kev = json.loads((site / "assets" / "exploited-latest.json")
                     .read_text(encoding="utf-8"))
    kev_total = int(kev["total"])

    claims_path = Path(os.environ.get("BRAND_VIDEO_CLAIMS")
                       or detections / "out" / "predicate.json")
    executed, passed, claim_rules = _claims(claims_path, sigma + kql)
    kev_facts = _kev(site, kev, claim_rules)

    signals = OTHER_CVES + FIELD_TECHNIQUES + (f"KEV {kev_total:,}", BINANCE)
    return Content(
        agent_cves=AGENT_CVES, signals=signals, kev_total=kev_total,
        sources=SOURCES, technique=TECHNIQUE, technique_name=TECHNIQUE_NAME,
        trace_lines=TRACE_LINES, rule_lines=RULE_LINES, rule_path=RULE,
        claim_name=CLAIM, claims_executed=executed, claims_passed=passed,
        article_title=ARTICLE_TITLE, article_eyebrow=ARTICLE_EYEBROW,
        article_url=ARTICLE_URL,
        pack_sigma=sigma, pack_kql=kql, tiles=tiles, **kev_facts,
    )
