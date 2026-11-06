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


if __name__ == "__main__":
    unittest.main()
