"""Tests for kev_coverage.py. Run:
python3 -m unittest discover -s tools/site-build -p 'test_*.py'
"""

import json
import tempfile
import unittest
from pathlib import Path

import kev_coverage as kc

CVE = "CVE-2026-1000"
RULE = "rules/web/thing.yml"
ARTICLES = [{"slug": "post", "palette": {"label": "A post"}}]


def entry(**over):
    e = {
        "cve": CVE,
        "tier": "rule",
        "kev": True,
        "label": "Acme Widget",
        "note": "Covers the request line.",
        "rules": [RULE],
        "article": "post",
        "attack": ["T1190"],
    }
    e.update(over)
    return e


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.pack = root / "sigma-pack"
        self.research = root / "research"
        self.claims = root / "claims"
        (self.pack / "rules" / "web").mkdir(parents=True)
        (self.pack / "queries" / "kql").mkdir(parents=True)
        self.research.mkdir()
        self.claims.mkdir()
        (self.pack / RULE).write_text(f"description: {CVE}\ntags:\n    - attack.initial-access\n    - attack.t1190\n")
        (self.research / "post.html").write_text(f"<p>{CVE}</p>")

    def problems(self, mapping, named=None):
        named = {CVE} if named is None else named
        return kc.problems(mapping, named, self.pack, self.research, ARTICLES)

    def assertProblem(self, mapping, text, named=None):
        found = self.problems(mapping, named)
        self.assertTrue(any(text in p for p in found), found)


class NamedCves(Fixture):
    def test_finds_rule_query_and_article_cves(self):
        (self.pack / "queries" / "kql" / "q.kql").write_text("// CVE-2026-2000")
        (self.research / "other.html").write_text("<p>CVE-2026-3000</p>")
        self.assertEqual(kc.named_cves(self.pack, self.research), {CVE, "CVE-2026-2000", "CVE-2026-3000"})

    def test_cve_in_script_block_ignored(self):
        (self.research / "other.html").write_text('<script type="application/ld+json">CVE-2026-4000</script>')
        self.assertNotIn("CVE-2026-4000", kc.named_cves(self.pack, self.research))

    def test_pack_readme_ignored(self):
        (self.pack / "README.md").write_text("CVE-2026-5000")
        self.assertNotIn("CVE-2026-5000", kc.named_cves(self.pack, self.research))


class Guards(Fixture):
    def test_clean_mapping_has_no_problems(self):
        self.assertEqual(self.problems([entry()]), [])

    def test_unmapped_cve_named_in_rule_fails(self):
        self.assertProblem([entry()], "CVE-2026-9999", named={CVE, "CVE-2026-9999"})

    def test_entry_nothing_names_fails(self):
        self.assertProblem([entry()], CVE, named=set())

    def test_repeated_entry_fails(self):
        self.assertProblem([entry(), entry()], "more than once")

    def test_bad_tier_fails(self):
        self.assertProblem([entry(tier="strong")], "tier")

    def test_kev_must_be_true_or_false(self):
        self.assertProblem([entry(kev="yes")], "kev")

    def test_empty_note_fails(self):
        self.assertProblem([entry(note="  ")], "note")

    def test_empty_label_fails(self):
        self.assertProblem([entry(label="")], "label")

    def test_dash_in_label_fails(self):
        self.assertProblem([entry(label="Acme \u2013 Widget")], "dash")

    def test_dash_in_note_fails(self):
        self.assertProblem([entry(note="Covers \u2014 most")], "dash")

    def test_rule_tier_needs_a_rule(self):
        self.assertProblem([entry(rules=[], attack=[])], "needs a rule")

    def test_partial_tier_needs_a_rule(self):
        self.assertProblem([entry(tier="partial", rules=[], attack=[])], "needs a rule")

    def test_rule_file_missing_fails(self):
        self.assertProblem([entry(rules=["rules/web/gone.yml"], attack=[])], "gone.yml")

    def test_rule_file_without_the_cve_fails(self):
        (self.pack / RULE).write_text("tags:\n    - attack.t1190\n")
        self.assertProblem([entry()], "does not name")

    def test_writeup_needs_an_article(self):
        self.assertProblem([entry(tier="writeup", rules=[], attack=[], article=None)], "needs an article")

    def test_rule_needs_an_article(self):
        self.assertProblem([entry(article=None)], "needs an article")

    def test_none_tier_needs_no_rule_or_article(self):
        self.assertEqual(self.problems([entry(tier="none", rules=[], attack=[], article=None)]), [])

    def test_article_slug_unknown_fails(self):
        self.assertProblem([entry(article="missing")], "missing")

    def test_article_without_the_cve_fails(self):
        (self.research / "post.html").write_text("<p>nothing</p>")
        self.assertProblem([entry()], "does not name")

    def test_attack_id_not_in_rule_tags_fails(self):
        self.assertProblem([entry(attack=["T1190", "T1059"])], "T1059")

    def test_attack_prefix_of_a_longer_tag_fails(self):
        (self.pack / RULE).write_text(f"{CVE}\ntags:\n    - attack.t1190.001\n")
        self.assertProblem([entry()], "T1190")

    def test_attack_tag_case_is_ignored(self):
        self.assertEqual(self.problems([entry(attack=["t1190"])]), [])

    def test_a_guard_problem_on_a_real_mapping_stops_nothing_else(self):
        found = self.problems([entry(tier="strong", note="", label="")])
        self.assertGreaterEqual(len(found), 3)


class Claims(Fixture):
    def test_claim_count_sums_claims(self):
        (self.claims / "thing.yml").write_text("rule: x\nclaims:\n  - id: a\n  - id: b\n")
        self.assertEqual(kc.claim_count(RULE, self.claims), 2)

    def test_claim_count_without_a_file_is_zero(self):
        self.assertEqual(kc.claim_count(RULE, self.claims), 0)


class Asset(Fixture):
    def render(self, mapping, claims_dir=None, committed=None):
        return json.loads(kc.render_asset(mapping, ARTICLES, claims_dir, committed))

    def test_render_asset_fills_rules_article_and_claims(self):
        (self.claims / "thing.yml").write_text("claims:\n  - id: a\n  - id: b\n  - id: c\n")
        out = self.render([entry()], self.claims)["entries"][0]
        self.assertEqual(out["claims"], 3)
        self.assertEqual(out["rules"], [{"name": "thing.yml", "url": kc.RULE_URL + RULE}])
        self.assertEqual(out["article"], {"title": "A post", "url": "/research/post"})
        self.assertEqual(out["tier"], "rule")

    def test_claims_sum_across_rules(self):
        (self.pack / "rules" / "web" / "two.yml").write_text(f"{CVE}\n")
        (self.claims / "thing.yml").write_text("claims:\n  - id: a\n")
        (self.claims / "two.yml").write_text("claims:\n  - id: a\n  - id: b\n")
        out = self.render([entry(rules=[RULE, "rules/web/two.yml"])], self.claims)["entries"][0]
        self.assertEqual(out["claims"], 3)

    def test_none_entry_has_no_article(self):
        out = self.render([entry(tier="none", rules=[], attack=[], article=None)], self.claims)["entries"][0]
        self.assertIsNone(out["article"])
        self.assertEqual(out["claims"], 0)

    def test_render_asset_keeps_committed_counts_without_claims(self):
        committed = {"entries": [{"cve": CVE, "claims": 16}]}
        self.assertEqual(self.render([entry()], None, committed)["entries"][0]["claims"], 16)

    def test_asset_ends_with_a_newline(self):
        self.assertTrue(kc.render_asset([entry()], ARTICLES, None, None).endswith("}\n"))


class Cards(Fixture):
    def entries(self, *mapping):
        return json.loads(kc.render_asset(list(mapping), ARTICLES, None, None))["entries"]

    def test_card_shows_the_mapped_facts(self):
        html = kc.render_cards(self.entries(entry(claims=0)))
        for text in (f'data-cve="{CVE}"', "Acme Widget", "Covers the request line.", "thing.yml", "A post", "T1190", ">Rule<"):
            self.assertIn(text, html)

    def test_cards_run_rule_then_partial_then_writeup(self):
        html = kc.render_cards(self.entries(
            entry(cve="CVE-2026-3", tier="writeup", rules=[], attack=[]),
            entry(cve="CVE-2026-2", tier="partial"),
            entry(cve="CVE-2026-1"),
        ))
        self.assertLess(html.index("CVE-2026-1"), html.index("CVE-2026-2"))
        self.assertLess(html.index("CVE-2026-2"), html.index("CVE-2026-3"))

    def test_none_and_non_kev_entries_get_no_card(self):
        html = kc.render_cards(self.entries(
            entry(cve="CVE-2026-1", tier="none", rules=[], attack=[], article=None),
            entry(cve="CVE-2026-2", kev=False),
        ))
        self.assertNotIn("data-cve", html)

    def test_card_text_is_escaped(self):
        self.assertIn("&lt;b&gt;", kc.render_cards(self.entries(entry(note="<b>"))))

    def test_claims_line_only_when_there_are_claims(self):
        asset = json.loads(kc.render_asset([entry()], ARTICLES, None, {"entries": [{"cve": CVE, "claims": 16}]}))["entries"]
        self.assertIn("16 tested claims", kc.render_cards(asset))
        self.assertNotIn("tested claims", kc.render_cards(self.entries(entry())))


class Nav(Fixture):
    def page(self, name, links):
        (self.research / name).write_text(f'<nav aria-label="Site">{links}</nav><footer><a>Exploited now</a></footer>')

    def test_nav_problems_lists_page_without_link(self):
        self.page("a.html", '<a href="x">About</a>')
        self.page("b.html", '<a href="x">Exploited now</a>')
        self.assertEqual(kc.nav_problems(["a.html", "b.html"], self.research), ["a.html"])


if __name__ == "__main__":
    unittest.main()
