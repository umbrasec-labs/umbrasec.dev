import os
import subprocess
import unittest
from pathlib import Path

import fonts

CACHE_FONTS = Path(__file__).resolve().parent / ".cache" / "fonts"


class FontsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conf = fonts.ensure_fonts()
        os.environ["FONTCONFIG_FILE"] = str(cls.conf)

    def match(self, pattern):
        out = subprocess.run(["fc-match", "-f", "%{family[0]}|%{style[0]}|%{file}", pattern],
                             capture_output=True, text=True, check=True,
                             env=dict(os.environ, FONTCONFIG_FILE=str(self.conf)))
        family, style, path = out.stdout.split("|", 2)
        return family, style, Path(path)

    def test_families_resolve_to_cached_files(self):
        # fontconfig's own weight names: a CSS number like 600 is off its scale
        for pattern, family, style in (("Inter Tight:semibold", "Inter Tight", "SemiBold"),
                                       ("Inter Tight:medium", "Inter Tight", "Medium"),
                                       ("Inter Tight:regular", "Inter Tight", "Regular"),
                                       ("JetBrains Mono:medium", "JetBrains Mono", "Medium"),
                                       ("JetBrains Mono:regular", "JetBrains Mono", "Regular")):
            got, got_style, path = self.match(pattern)
            self.assertEqual((got, got_style), (family, style), pattern)
            self.assertEqual(path.parent, CACHE_FONTS, pattern)

    def test_pango_sees_both_families(self):
        import draw  # sets FONTCONFIG_FILE itself before PangoCairo loads
        names = draw.font_families()
        self.assertIn("Inter Tight", names)
        self.assertIn("JetBrains Mono", names)

    def test_symbols_have_glyphs(self):
        # counted with font fallback off, so a glyph borrowed from a system
        # font counts as missing
        import draw
        self.assertEqual(draw.unknown_glyphs("→ · × [1] $6.3B", family="JetBrains Mono", px=24), 0)
        self.assertEqual(draw.unknown_glyphs("Forge the rule. → ·", family="Inter Tight", px=24, weight=600), 0)

    def test_missing_glyph_is_counted(self):
        # JetBrains Mono has no check mark, so the film draws ticks as paths
        import draw
        self.assertEqual(draw.unknown_glyphs("✓", family="JetBrains Mono", px=24), 1)


if __name__ == "__main__":
    unittest.main()
