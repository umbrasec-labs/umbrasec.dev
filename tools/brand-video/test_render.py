"""Frames come out at film size with the site's orange intact.

Run from the umbrasec.dev root with BRAND_VIDEO_CLAIMS set (see test_content).
"""
import unittest
from pathlib import Path

import compose
import content
import draw
import timeline as tl

SITE = Path(__file__).resolve().parents[2]
ACCENT = (0xF2, 0x56, 0x23)


def near(surface, rgb, tol=12):
    """Pixels within tol of rgb on every channel (cairo stores B, G, R, x)."""
    data = bytes(surface.get_data())
    r0, g0, b0 = rgb
    n = 0
    for i in range(0, len(data), 4):
        if (abs(data[i + 2] - r0) <= tol and abs(data[i + 1] - g0) <= tol
                and abs(data[i] - b0) <= tol):
            n += 1
    return n


class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = content.load(SITE, SITE.parent / "detections")

    def test_frame_shape_and_accent(self):
        s = compose.frame(2.4, self.c)
        self.assertEqual((s.get_width(), s.get_height()), (2560, 1440))
        self.assertGreaterEqual(near(s, ACCENT), 200)

    def test_papers_quotes_render(self):
        # every glyph on the case cards comes from the film's own fonts
        for s in self.c.sources:
            self.assertEqual(draw.unknown_glyphs(s.mark, family=draw.DISPLAY, px=24, weight=500), 0)
            self.assertEqual(draw.unknown_glyphs(s.before + s.after, family=draw.DISPLAY, px=24,
                                                 weight=500), 0)
            self.assertEqual(draw.unknown_glyphs(s.title, family=draw.DISPLAY, px=24, weight=600), 0)
            self.assertEqual(draw.unknown_glyphs(s.label.upper(), family=draw.MONO, px=24,
                                                 weight=500), 0)

    def test_case_cards_fit_and_hold_still(self):
        import s2_papers
        for i, s in enumerate(self.c.sources):
            lay = s2_papers.page_layout(i, s)   # refuses content that overflows its card
            self.assertGreaterEqual(len(lay["bands"]), 1)
            settled = s2_papers.EXIT[0] - (tl.FLICKS[i] + s2_papers.FLIP)
            self.assertGreaterEqual(settled, 0.6)


    def test_query_panels_fit(self):
        import s3_query
        lay = s3_query.layout(self.c)
        self.assertGreaterEqual(s3_query.CODE_PX, 21)
        for name in ("trace", "rule", "claims"):
            panel = lay[name]
            for w in panel["widths"]:
                self.assertLessEqual(w, panel["inner"], name)
            self.assertLess(panel["bottom"], tl.H - draw.cq(5), name)   # clear of the HUD
            self.assertGreater(panel["top"], draw.cq(5), name)

    def test_wire_joins_the_two_credentials_strings(self):
        import s3_query
        lay = s3_query.layout(self.c)
        start, end = lay["wire"][0], lay["wire"][-1]
        tx, ty, tw, th = lay["trace"]["hl"][".aws/credentials"]
        rx, ry, rw, rh = lay["rule"]["hl"]["'.aws/credentials'"]
        self.assertAlmostEqual(start[0], tx + tw, delta=2)
        self.assertTrue(ty <= start[1] <= ty + th)
        self.assertAlmostEqual(end[0], rx, delta=2)
        self.assertTrue(ry <= end[1] <= ry + rh)

    def test_the_tag_line_is_where_the_chip_lands(self):
        import s2_papers
        import s3_query
        x, y, w, h = s3_query.layout(self.c)["rule"]["hl"]["attack.t1552.001"]
        self.assertEqual(s2_papers.chip_target(self.c), (x + w / 2, y + h / 2))


    def test_publish_layout_fits(self):
        import s4_publish
        lay = s4_publish.layout(self.c)
        b, p = lay["browser"], lay["pack"]
        for w in b["widths"]:
            self.assertLessEqual(w, b["inner"])
        for w in p["widths"]:
            self.assertLessEqual(w, p["width"])
        for box in (b, p):
            self.assertLess(box["bottom"], tl.H - draw.cq(5))
            self.assertGreater(box["top"], draw.cq(5))
        self.assertEqual([t for t, _ in p["tiles"]], list(self.c.tiles))
        self.assertEqual(p["lit"], self.c.tiles.index(self.c.technique))

    def test_publish_excerpt_marks_its_cuts(self):
        import s4_publish
        lines = s4_publish.mini_lines(self.c)
        rule = list(self.c.rule_lines)
        last = None
        for ln in lines:
            if ln.strip() == "...":
                last = None
                continue
            self.assertIn(ln, rule)
            i = rule.index(ln)
            if last is not None:
                self.assertEqual(i, last + 1, f"cut before {ln!r} is not marked")
            last = i


    def test_loop_seam(self):
        # the last frame and the first are both plain charcoal, so the loop does not jump
        bg = luminance(draw.BG)
        for t in ((tl.FRAMES - 1) / tl.FPS, 0.0):
            self.assertAlmostEqual(mean_luminance(compose.frame(t, self.c)), bg, delta=3, msg=t)

    def test_end_card_stop_sits_after_the_second_line(self):
        import s5_end
        lay = s5_end.layout()
        x, y, size = lay["stop"]
        self.assertGreater(x - size / 2, lay["l2_right"])
        self.assertLess(x - size / 2 - lay["l2_right"], draw.cq(0.6))
        self.assertLess(abs(y + size / 2 - lay["l2_base"]), 1.0)   # sits on the baseline
        # the letters drawn one by one end where the whole line ends
        last = s5_end.L2[-1]
        lw = draw.measure(last, family=draw.DISPLAY, px=s5_end.LINE_PX, weight=600,
                          tracking=s5_end.LINE_TRACK)[0]
        self.assertAlmostEqual(lay["xs"][-1] + lw, lay["l2_right"], delta=draw.cq(0.3))
        x0, y0, s0, _ = s5_end.dot(tl.T_LAND, self.c)
        self.assertAlmostEqual(x0, x, delta=0.5)
        self.assertAlmostEqual(y0, y, delta=0.5)


    def test_poster_fits_its_budget(self):
        import tempfile
        import encode
        with tempfile.TemporaryDirectory() as tmp:
            png, jpg = Path(tmp) / "p.png", Path(tmp) / "p.jpg"
            import render
            self.assertTrue(tl.SWEEP[1] < render.POSTER_T < tl.FADE_OUT[0])   # the settled end card
            compose.frame(render.POSTER_T, self.c, grain=False).write_to_png(str(png))
            encode.poster(png, jpg)
            self.assertLessEqual(jpg.stat().st_size, encode.POSTER_MAX)
            self.assertEqual(encode.POSTER_MAX, 350_000)
            p = encode.probe(jpg)
            self.assertEqual((p["width"], p["height"]), (2560, 1440))


class ExploitedNowTest(unittest.TestCase):
    """04: the KEV wall, its counts and the one card."""

    @classmethod
    def setUpClass(cls):
        import s3x_exploited
        cls.c = content.load(SITE, SITE.parent / "detections")
        cls.s = s3x_exploited
        cls.lay = s3x_exploited.layout(cls.c)

    def test_the_wall_is_the_snapshot_entry_for_entry(self):
        import json
        feed = json.loads((SITE / "assets" / "exploited-latest.json").read_text(encoding="utf-8"))
        self.assertEqual([cve for cve, _, _, _ in self.lay["cells"]], [r["cve"] for r in feed["rows"]])
        self.assertEqual([(cve, tier) for cve, tier, _, _ in self.lay["cells"]], list(self.c.kev_wall))
        self.assertEqual(self.lay["cells"][self.lay["lock"]][0], self.c.kev_cve)

    def test_wall_and_card_fit_clear_of_the_hud(self):
        left, top, width = self.s.WALL_BOX
        for _, _, (x, y, w, h), _ in self.lay["cells"]:
            self.assertGreaterEqual(x, left - 0.01)
            self.assertLessEqual(x + w, left + width + 0.01)
        self.assertLess(top + self.lay["height"], tl.H - draw.cq(5))
        self.assertGreater(self.s.HEAD_TOP, draw.cq(5))
        card = self.lay["card"]
        self.assertLess(card["top"] + card["height"], tl.H - draw.cq(5))
        self.assertLessEqual(card["left"] + card["width"], tl.W - draw.cq(3.4))
        self.assertGreater(card["left"], left + width)   # beside the wall, not over it

    def test_the_heading_carries_the_snapshots_own_date_and_numbers(self):
        head = "".join(self.lay["head"])
        self.assertIn(f"{self.c.kev_total:,} known exploited", head)
        self.assertIn(f"{len(self.c.kev_wall)} added in {self.c.kev_days} days", head)
        self.assertEqual(self.lay["asof"], f"as of {content.site_date(self.c.kev_date)}")

    def test_counts_start_at_zero_and_end_at_the_tier_totals(self):
        before = self.s.counts(tl.SCAN[0] - 0.01, self.c)
        self.assertEqual(set(before.values()), {0})
        after = self.s.counts(tl.SCAN[1], self.c)
        self.assertEqual(after, {tier: n for tier, _, n in self.c.kev_tiers})
        self.assertEqual(sum(after.values()), len(self.c.kev_wall))
        mid = self.s.counts((tl.SCAN[0] + tl.SCAN[1]) / 2, self.c)
        self.assertTrue(0 < sum(mid.values()) < len(self.c.kev_wall))

    def test_the_card_says_partial_rule_and_carries_the_limits(self):
        card = self.lay["card"]
        self.assertEqual(self.c.kev_tier, "partial")
        self.assertEqual(card["badge"], "PARTIAL RULE")
        self.assertEqual(card["badge"], self.c.kev_tier_label.upper())
        # the whole note, not a cut of it
        self.assertEqual(card["note"].layout.get_text(), self.c.kev_note)
        self.assertIn("a match means probing, not compromise", self.c.kev_note)
        self.assertEqual(card["claims"], f"{self.c.kev_claims} tested claims")
        # nothing in this section's source calls it a match, a catch or covered
        src = (Path(self.s.__file__)).read_text(encoding="utf-8")
        drawn = [ln for ln in src.splitlines() if "d.text(" in ln or "f\"" in ln]
        for word in ("Match", "MATCH", "caught", "Caught", "covered", "Covered", "detected"):
            self.assertFalse(any(word in ln for ln in drawn), word)

    def test_the_badge_is_on_the_card_from_its_first_frame(self):
        # there is no frame with the CVE on a card and no tier beside it
        self.assertLessEqual(tl.CARD_IN[0], tl.T_TIER)
        s = compose.frame(tl.CARD_IN[1], self.c, grain=False)
        partial = tuple(round(v * 255) for v in self.s.TIER_COLOR["partial"])
        self.assertGreaterEqual(near(s, partial, tol=10), 300)

    def test_tier_colours_are_the_sites(self):
        css = (SITE / "assets" / "umbra.css").read_text(encoding="utf-8")
        for tier, name in (("rule", "--t-rule"), ("partial", "--t-partial"),
                           ("writeup", "--t-writeup"), ("gap", "--t-gap")):
            import re
            hex_ = re.search(name + r":\s*(#[0-9a-fA-F]{6})", css).group(1)
            self.assertEqual(self.s.TIER_COLOR[tier], draw.rgb(hex_), tier)

    def test_only_the_rule_and_the_wall_move_with_the_camera(self):
        import s3_query, s4_publish, s5_end
        mid = (tl.PAN_OUT[1] + tl.PAN_BACK[0]) / 2
        self.assertEqual(compose.shift(s3_query, 0.0), 0.0)
        self.assertEqual(compose.shift(self.s, 0.0), tl.W)       # the wall waits off to the right
        self.assertEqual(compose.shift(s3_query, mid), -tl.W)
        self.assertEqual(compose.shift(self.s, mid), 0.0)
        self.assertEqual(compose.shift(s3_query, tl.FOLD[0]), 0.0)
        for m in (s4_publish, s5_end):
            self.assertEqual(compose.shift(m, mid), 0.0)

    def test_the_dot_never_jumps_between_sections(self):
        # one continuous shot: across each handover the dot moves less than it could fly
        for t in (tl.PAN_OUT[0], tl.SCAN[0], tl.TO_LOCK[0], tl.PAN_BACK[0], tl.PAN_BACK[1],
                  tl.FOLD[0], tl.COLLAPSE[1]):
            a = compose.dot_at(t - 1 / 240, self.c)
            b = compose.dot_at(t + 1 / 240, self.c)
            self.assertIsNotNone(a, t)
            self.assertIsNotNone(b, t)
            self.assertLess(abs(a[0] - b[0]) + abs(a[1] - b[1]), draw.cq(2.5), t)

    def test_wall_frames_render_at_film_size(self):
        s = compose.frame(13.0, self.c)
        self.assertEqual((s.get_width(), s.get_height()), (2560, 1440))
        self.assertGreaterEqual(near(s, ACCENT), 50)


def luminance(rgb):
    r, g, b = (v * 255 for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mean_luminance(surface):
    data = bytes(surface.get_data())
    n, total = 0, 0.0
    for i in range(0, len(data), 64):          # every 16th pixel is plenty
        total += 0.2126 * data[i + 2] + 0.7152 * data[i + 1] + 0.0722 * data[i]
        n += 1
    return total / n


if __name__ == "__main__":
    unittest.main()
