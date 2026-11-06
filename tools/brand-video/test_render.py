"""Frames come out at film size with the site's orange intact.

Run from the umbrasec.dev root with BRAND_VIDEO_CLAIMS set (see test_content).
"""
import unittest
from pathlib import Path

import compose
import content

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


if __name__ == "__main__":
    unittest.main()
