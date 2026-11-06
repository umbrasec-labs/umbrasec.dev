import unittest

import cairo

import draw


class DrawTest(unittest.TestCase):
    def test_rgb(self):
        self.assertEqual(draw.rgb("#f25623"), (242 / 255, 86 / 255, 35 / 255))

    def test_scramble_resolves(self):
        s = "CVE-2025-8217"
        self.assertEqual(draw.scramble(s, 1.0, 7), s)

    def test_scramble_keeps_shape(self):
        s = "Lock · hijacked AI coding agents."
        out = draw.scramble(s, 0.4, 7)
        self.assertEqual(len(out), len(s))
        for a, b in zip(s, out):
            if a in " -.:/·":
                self.assertEqual(a, b)
        self.assertNotEqual(out, s)

    def test_scramble_is_deterministic(self):
        self.assertEqual(draw.scramble("T1552.001", 0.3, 11), draw.scramble("T1552.001", 0.3, 11))

    def test_scramble_decodes_left_to_right(self):
        s = "ABCDEFGHIJ"
        self.assertEqual(draw.scramble(s, 0.5, 3)[:5], "ABCDE")

    def test_small_readable_text_refused(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 32, 32)
        ctx = cairo.Context(surface)
        with self.assertRaises(ValueError):
            draw.text(ctx, "too small", 0, 20, family="Inter Tight", px=17, color=draw.TEXT)
        draw.text(ctx, "HUD", 0, 20, family="JetBrains Mono", px=17, color=draw.DIM, hud=True)

    def test_text_returns_size(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 100)
        ctx = cairo.Context(surface)
        w, h = draw.text(ctx, "Forge the rule", 10, 60, family="Inter Tight", px=40,
                         weight=600, color=draw.ACCENT)
        self.assertGreater(w, 150)
        self.assertGreater(h, 30)


if __name__ == "__main__":
    unittest.main()
