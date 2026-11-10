"""Every fact the film shows must match the repos it comes from.

Run from the umbrasec.dev root:
    BRAND_VIDEO_CLAIMS=<fresh predicate.json> \
    python3 -m unittest discover -s tools/brand-video -p 'test_*.py'
"""
import html
import json
import os
import re
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import content

SITE = Path(__file__).resolve().parents[2]
DETECTIONS = SITE.parent / "detections"
ARTICLE = SITE / "research" / "detecting-hijacked-ai-coding-agents.html"
AGENT_CVES = ("CVE-2025-8217", "CVE-2025-53773", "CVE-2025-54135",
              "CVE-2025-54136", "CVE-2026-110202")


def page_text(path):
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    return squash(html.unescape(re.sub(r"<[^>]+>", "", raw)))


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


class ContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = content.load(SITE, DETECTIONS)

    def test_quotes_are_word_for_word(self):
        text = page_text(ARTICLE)
        self.assertEqual(len(self.c.sources), 3)
        for s in self.c.sources:
            self.assertTrue(s.mark)
            self.assertIn(squash(s.before + s.mark + s.after), text)

    def test_cves_are_on_the_site(self):
        self.assertEqual(self.c.agent_cves, AGENT_CVES)
        article = ARTICLE.read_text(encoding="utf-8")
        for cve in AGENT_CVES:
            self.assertIn(cve, article)
        research = " ".join(p.read_text(encoding="utf-8")
                            for p in (SITE / "research").glob("*.html"))
        for cve in ("CVE-2026-102764", "CVE-2026-42271"):
            self.assertIn(cve, research)
            self.assertIn(cve, self.c.signals)

    def test_tiles_follow_the_hero_reel(self):
        index = (SITE / "index.html").read_text(encoding="utf-8")
        ids = tuple(re.findall(r'data-tr-id="([^"]+)"', index))
        self.assertEqual(self.c.tiles, ids)
        self.assertEqual(len(self.c.tiles), self.c.pack_sigma + self.c.pack_kql)
        self.assertEqual(len(self.c.tiles), 29)

    def test_pack_counts(self):
        self.assertEqual((self.c.pack_sigma, self.c.pack_kql), (22, 7))

    def test_kev_total(self):
        data = json.loads((SITE / "assets" / "exploited-latest.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(self.c.kev_total, data["total"])
        self.assertIn(f"KEV {data['total']:,}", self.c.signals)

    def test_rule_lines_exist(self):
        rule_raw = (SITE / self.c.rule_path).read_text(encoding="utf-8")
        rule = squash(rule_raw)
        checked = 0
        for line in self.c.rule_lines:
            s = line.strip()
            if s == "..." or s.startswith("condition:") or s.startswith("and ("):
                continue
            s = s.removeprefix("- ")
            self.assertIn(squash(s), rule, s)
            checked += 1
        self.assertGreaterEqual(checked, 10)
        self.assertEqual(self.c.rule_lines[0],
                         "title: AI Coding Agent Shell Runs a Risky Command")
        self.assertIn("- attack.t1552.001", [l.strip() for l in self.c.rule_lines])
        self.assertEqual(self.c.rule_lines[-1], "level: high")
        cond = re.search(r"^\s*condition:\s*(.+)$", rule_raw, flags=re.M).group(1)
        self.assertTrue(cond.startswith("(1 of agent_* or "))
        self.assertIn(") and (1 of risk_* or ", cond)
        self.assertIn(") and not (", cond)

    def test_trace_matches_reel(self):
        index = page_text(SITE / "index.html")
        for s in ("/home/dev/.local/share/claude/versions/2.1.310",
                  "/usr/bin/bash -c 'cat ~/.aws/credentials'",
                  "catches/claude-parent-credential-read"):
            self.assertIn(s, index)
        joined = " ".join(self.c.trace_lines)
        self.assertIn("/home/dev/.local/share/claude/versions/2.1.310", joined)
        self.assertIn("/usr/bin/bash -c 'cat ~/.aws/credentials'", joined)
        self.assertEqual(self.c.claim_name, "catches/claude-parent-credential-read")

    # ---- "Exploited now": the KEV wall and its one card

    def test_wall_is_the_snapshot_joined_the_way_the_api_joins_it(self):
        feed = json.loads((SITE / "assets" / "exploited-latest.json").read_text(encoding="utf-8"))
        cov = json.loads((SITE / "assets" / "kev-coverage.json").read_text(encoding="utf-8"))
        self.assertEqual([cve for cve, _ in self.c.kev_wall], [r["cve"] for r in feed["rows"]])
        tier_of = {e["cve"]: e["tier"] for e in cov["entries"]}
        for cve, tier in self.c.kev_wall:
            self.assertEqual(tier, "gap" if tier_of.get(cve, "none") == "none" else tier_of[cve], cve)
        self.assertEqual(self.c.kev_date, feed["generated"])
        self.assertEqual([t for t, _, _ in self.c.kev_tiers], ["rule", "partial", "writeup", "gap"])
        self.assertEqual(sum(n for _, _, n in self.c.kev_tiers), len(feed["rows"]))
        # the join in functions/api/exploited.js still reads the way kev_wall copies it
        api = (SITE / "functions" / "api" / "exploited.js").read_text(encoding="utf-8")
        for line in ('if (e.tier !== "none") tierOf.set(e.cve, e.tier);',
                     'const tiers = { rule: 0, partial: 0, writeup: 0, gap: 0 };',
                     'const tier = Object.hasOwn(tiers, t) ? t : "gap";'):
            self.assertTrue(line in api, f"joinCoverage no longer has: {line}")

    def test_an_unknown_tier_is_a_gap_as_on_the_page(self):
        feed = {"rows": [{"cve": "CVE-2026-0001"}, {"cve": "CVE-2026-0002"}, {"cve": "CVE-2026-0003"}]}
        cov = {"entries": [{"cve": "CVE-2026-0001", "tier": "rule"},
                           {"cve": "CVE-2026-0002", "tier": "shiny"},
                           {"cve": "CVE-2026-0003", "tier": "none"}]}
        self.assertEqual(content.kev_wall(feed, cov),
                         (("CVE-2026-0001", "rule"), ("CVE-2026-0002", "gap"), ("CVE-2026-0003", "gap")))

    def test_tier_names_are_the_pages_own(self):
        js = (SITE / "assets" / "exploited.js").read_text(encoding="utf-8")
        self.assertEqual(content.tier_labels(js), {t: label for t, label, _ in self.c.kev_tiers})
        self.assertEqual(self.c.kev_tier_label, "Partial rule")

    def test_card_is_what_exploited_shows_for_that_cve(self):
        page = (SITE / "exploited.html").read_text(encoding="utf-8")
        card = re.search(r'<article class="card" data-cve="%s">(.*?)</article>' % self.c.kev_cve,
                         page, re.S).group(1)
        text = squash(html.unescape(re.sub(r"<[^>]+>", " ", card)))
        for s in (self.c.kev_tier_label, self.c.kev_product, self.c.kev_note, self.c.kev_rule,
                  f"{self.c.kev_claims} tested claims"):
            self.assertIn(s, text)
        self.assertEqual(self.c.kev_cve, "CVE-2026-109619")
        self.assertEqual(self.c.kev_tier, "partial")

    def test_card_claims_are_the_ledgers(self):
        claims = Path(os.environ.get("BRAND_VIDEO_CLAIMS", DETECTIONS / "out" / "predicate.json"))
        rec = json.loads(claims.read_text(encoding="utf-8"))["rules"][Path(self.c.kev_rule).stem]
        self.assertEqual(rec["status"], "verified")
        self.assertEqual(sum(rec["counts"].values()), self.c.kev_claims)

    def _site_copy(self, tmp):
        site = Path(tmp) / "site"
        shutil.copytree(SITE, site, ignore=shutil.ignore_patterns(
            "node_modules", ".git", ".superpowers", ".cache", "out", ".claude", ".mcp.json",
            "video", "dist"))
        return site

    def _edit_coverage(self, site, change):
        path = site / "assets" / "kev-coverage.json"
        cov = json.loads(path.read_text(encoding="utf-8"))
        change(next(e for e in cov["entries"] if e["cve"] == content.KEV_CVE))
        path.write_text(json.dumps(cov), encoding="utf-8")

    def test_load_refuses_when_the_tier_is_no_longer_partial(self):
        # the film says "Partial rule"; a promotion (or a demotion) must stop the render
        for tier in ("rule", "writeup", "none"):
            with tempfile.TemporaryDirectory() as tmp:
                site = self._site_copy(tmp)
                self._edit_coverage(site, lambda e: e.update(tier=tier))
                with self.assertRaises(content.FactError, msg=tier):
                    content.load(site, DETECTIONS)

    def test_load_refuses_a_changed_note_or_claim_count(self):
        for change in (lambda e: e.update(note="Covers every case."),
                       lambda e: e.update(note=""),
                       lambda e: e.update(claims=e["claims"] + 1)):
            with tempfile.TemporaryDirectory() as tmp:
                site = self._site_copy(tmp)
                self._edit_coverage(site, change)
                with self.assertRaises(content.FactError):
                    content.load(site, DETECTIONS)

    def test_load_refuses_when_the_cve_leaves_the_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self._site_copy(tmp)
            path = site / "assets" / "exploited-latest.json"
            feed = json.loads(path.read_text(encoding="utf-8"))
            feed["rows"] = [r for r in feed["rows"] if r["cve"] != content.KEV_CVE]
            path.write_text(json.dumps(feed), encoding="utf-8")
            with self.assertRaises(content.FactError):
                content.load(site, DETECTIONS)

    def test_a_new_snapshot_changes_the_wall_without_a_code_change(self):
        # the counts are read at render time: add one entry and every number follows
        with tempfile.TemporaryDirectory() as tmp:
            site = self._site_copy(tmp)
            path = site / "assets" / "exploited-latest.json"
            feed = json.loads(path.read_text(encoding="utf-8"))
            feed["rows"].insert(0, dict(feed["rows"][0], cve="CVE-2026-999999"))
            feed["generated"] = "2026-11-09"
            path.write_text(json.dumps(feed), encoding="utf-8")
            c = content.load(site, DETECTIONS)
            self.assertEqual(len(c.kev_wall), len(self.c.kev_wall) + 1)
            self.assertEqual(c.kev_wall[0], ("CVE-2026-999999", "gap"))
            self.assertEqual(dict((t, n) for t, _, n in c.kev_tiers)["gap"],
                             dict((t, n) for t, _, n in self.c.kev_tiers)["gap"] + 1)
            self.assertEqual((c.kev_date, c.kev_days), ("2026-11-09", self.c.kev_days + 7))

    def test_site_date(self):
        self.assertEqual(content.site_date("2026-11-02"), "Nov 2, 2026")

    def test_claims_all_pass(self):
        self.assertGreater(self.c.claims_passed, 0)
        self.assertEqual(self.c.claims_executed, self.c.claims_passed)

    def test_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            shutil.copytree(SITE, site, ignore=shutil.ignore_patterns(
                "node_modules", ".git", ".superpowers", ".cache", "out", ".claude", ".mcp.json"))
            art = site / "research" / ARTICLE.name
            art.write_text(art.read_text(encoding="utf-8")
                           .replace("inventory secrets", "list secrets"),
                           encoding="utf-8")
            with self.assertRaises(content.FactError):
                content.load(site, DETECTIONS)

    def test_stale_claims_refuse(self):
        claims = Path(os.environ.get("BRAND_VIDEO_CLAIMS",
                                     DETECTIONS / "out" / "predicate.json"))
        data = json.loads(claims.read_text(encoding="utf-8"))
        data["generated_at"] = "2026-01-01T00:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "predicate.json"
            old.write_text(json.dumps(data), encoding="utf-8")
            saved = os.environ.get("BRAND_VIDEO_CLAIMS")
            os.environ["BRAND_VIDEO_CLAIMS"] = str(old)
            try:
                with self.assertRaises(content.FactError):
                    content.load(SITE, DETECTIONS)
            finally:
                if saved is None:
                    os.environ.pop("BRAND_VIDEO_CLAIMS")
                else:
                    os.environ["BRAND_VIDEO_CLAIMS"] = saved

    def test_case_cards_say_whose_words(self):
        # the page text is the write-up's own account of each case, so a card
        # is headed as a case, never as the source's own words
        for s in self.c.sources:
            self.assertRegex(s.label, r"^Case [123] · ")

    def test_quotes_end_where_the_sentence_ends(self):
        # a quote cut mid-sentence can drop what qualifies it, like the
        # Amazon Q instruction never running
        text = page_text(ARTICLE)
        for s in self.c.sources:
            q = squash(s.before + s.mark + s.after)
            end = text.index(q) + len(q)
            self.assertTrue(q.endswith("."), q)
            self.assertRegex(text[end:end + 2], r"^ [A-Z]", q)

    def test_rule_excerpt_marks_cuts_like_the_hero_reel(self):
        index = (SITE / "index.html").read_text(encoding="utf-8")
        start = index.index('data-tr-id="T1552.001"')
        panel = index[index.index("tr-panel tr-rule", start):]
        panel = panel[:panel.index("tr-foot")]
        reel = [squash(html.unescape(re.sub(r"<[^>]+>", "", ln)))
                for ln in re.findall(r'<div class="ln[^"]*">(.*?)</div>', panel)]
        self.assertGreater(len(reel), 5)
        film = [ln.strip() for ln in self.c.rule_lines]
        a = film.index("agent_parent:")
        self.assertEqual(film[a:a + len(reel)], reel)

    def test_rule_excerpt_marks_left_out_tags(self):
        rule = (SITE / content.RULE).read_text(encoding="utf-8")
        block = re.search(r"^tags:\n((?:[ \t]+- .*\n)+)", rule, flags=re.M).group(1)
        tags = re.findall(r"- (\S+)", block)
        film = [ln.strip() for ln in self.c.rule_lines]
        shown = film[film.index("tags:") + 1:film.index("detection:")]
        i = tags.index("attack.t1552.001")
        want = ((["..."] if i > 0 else []) + ["- attack.t1552.001"]
                + (["..."] if i < len(tags) - 1 else []))
        self.assertEqual(shown, want)

    def test_load_refuses_a_cut_quote(self):
        cut = (content.SOURCES[0],
               replace(content.SOURCES[1], after=""),
               content.SOURCES[2])
        with mock.patch.object(content, "SOURCES", cut):
            with self.assertRaises(content.FactError):
                content.load(SITE, DETECTIONS)

    def test_load_refuses_an_unmarked_cut(self):
        unmarked = tuple(ln for ln in content.RULE_LINES if ln.strip() != "...")
        with mock.patch.object(content, "RULE_LINES", unmarked):
            with self.assertRaises(content.FactError):
                content.load(SITE, DETECTIONS)

    def test_article_eyebrow_is_the_articles_own(self):
        self.assertIn(self.c.article_eyebrow.upper(), page_text(ARTICLE).upper())

    def test_load_refuses_a_changed_eyebrow(self):
        with mock.patch.object(content, "ARTICLE_EYEBROW", "Research · AI"):
            with self.assertRaises(content.FactError):
                content.load(SITE, DETECTIONS)

    def _refuses_sources(self, sources):
        with mock.patch.object(content, "SOURCES", tuple(sources)):
            with self.assertRaises(content.FactError):
                content.load(SITE, DETECTIONS)

    def test_load_refuses_swapped_case_cves(self):
        s1, s2, s3 = content.SOURCES
        self._refuses_sources((s1, replace(s2, label=s3.label.replace("3", "2")),
                               replace(s3, label=s2.label.replace("2", "3"))))

    def test_load_refuses_a_product_on_the_wrong_case(self):
        s1, s2, s3 = content.SOURCES
        self._refuses_sources((s1, replace(s2, title="Roo Code"), s3))

    def test_load_refuses_a_wrong_case_title(self):
        s1, s2, s3 = content.SOURCES
        self._refuses_sources((replace(s1, title="Malicious extension versions"), s2, s3))

    def test_load_refuses_a_wrong_case_date(self):
        s1, s2, s3 = content.SOURCES
        self._refuses_sources((replace(s1, label=s1.label.replace("2025", "2024")), s2, s3))

    def test_load_refuses_a_wrong_case_name(self):
        s1, s2, s3 = content.SOURCES
        self._refuses_sources((replace(s1, label=s1.label.replace("Nx", "Npm")), s2, s3))

    def test_load_refuses_a_changed_technique_name(self):
        with mock.patch.object(content, "TECHNIQUE_NAME", "Unsecured Credentials"):
            with self.assertRaises(content.FactError):
                content.load(SITE, DETECTIONS)


if __name__ == "__main__":
    unittest.main()
