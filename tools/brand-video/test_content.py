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
from pathlib import Path

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

    def test_claims_all_pass(self):
        self.assertGreater(self.c.claims_passed, 0)
        self.assertEqual(self.c.claims_executed, self.c.claims_passed)

    def test_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            shutil.copytree(SITE, site, ignore=shutil.ignore_patterns(
                "node_modules", ".git", ".superpowers", ".cache", "out"))
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


if __name__ == "__main__":
    unittest.main()
