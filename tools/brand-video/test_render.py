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
        self.assertEqual((s.get_width(), s.get_height()), (1920, 1080))
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
        for t in (449 / 30, 0.0):
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
