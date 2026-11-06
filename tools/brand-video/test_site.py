"""The film on the home page: placed in "How this project works", lazy, muted,
captioned in plain words, and dated with the render it shows; and the intro
that opens it over the page once per visitor, whose title lands on the hero."""
import json
import re
import unittest
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def as_of(d: date) -> str:
    """The site's date style, as in the article headers: Nov 6, 2026."""
    return f"{d.strftime('%b')} {d.day}, {d.year}"


class SiteEmbedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section id="approach".*?</section>', cls.html, re.S)
        cls.approach = m.group(0)
        f = re.search(r"<figure[^>]*data-film.*?</figure>", cls.approach, re.S)
        cls.fig = f.group(0) if f else ""

    def test_figure_sits_between_heading_and_cards(self):
        h2 = self.approach.index("How this project works.")
        fig = self.approach.index("data-film")
        cards = self.approach.index('class="grid md:grid-cols-3')
        self.assertLess(h2, fig)
        self.assertLess(fig, cards)

    def test_video_is_lazy_muted_and_described(self):
        v = re.search(r"<video[^>]*>", self.fig).group(0)
        for attr in ("data-film-video", "muted", "loop", "playsinline", 'preload="none"',
                     'poster="assets/video/brand-15s-poster.jpg"',
                     'aria-describedby="film-desc"'):
            self.assertIn(attr, v)
        self.assertNotIn("autoplay", v)
        self.assertIn('src="assets/video/brand-15s.mp4"', self.fig)
        for f in ("brand-15s.mp4", "brand-15s-poster.jpg"):
            self.assertTrue((SITE / "assets" / "video" / f).is_file(), f)

    def test_toggle_button(self):
        b = re.search(r"<button[^>]*data-film-toggle[^>]*>", self.fig).group(0)
        self.assertIn('type="button"', b)
        self.assertIn('aria-label="Pause the film"', b)
        self.assertIn('aria-pressed="false"', b)

    def test_sound_button(self):
        b = re.search(r"<button[^>]*data-film-sound[^>]*>", self.fig).group(0)
        self.assertIn('type="button"', b)
        self.assertIn('aria-pressed="false"', b)

    def test_caption_is_plain_and_dated_by_the_render(self):
        cap = re.search(r'<figcaption id="film-desc"[^>]*>(.*?)</figcaption>', self.fig, re.S)
        text = re.sub(r"<[^>]+>", "", cap.group(1))
        self.assertNotRegex(text, r"CVE-\d")
        rendered = date.fromisoformat(json.loads((HERE / "facts.json").read_text())["rendered"])
        self.assertIn(f"as of {as_of(rendered)}", text)


class IntroTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<div class="intro" data-intro.*?<!-- /intro -->', cls.html, re.S)
        cls.intro = m.group(0) if m else ""
        cls.js = (SITE / "assets" / "umbra.js").read_text(encoding="utf-8")

    def test_intro_is_a_hidden_dialog_before_the_nav(self):
        self.assertTrue(self.intro, "no intro markup")
        tag = re.search(r'<div class="intro"[^>]*>', self.intro).group(0)
        for attr in ("hidden", 'role="dialog"', 'aria-modal="true"', "aria-label="):
            self.assertIn(attr, tag)
        self.assertNotIn("data-intro-always", tag)
        self.assertLess(self.html.index("data-intro"), self.html.index('<nav aria-label="Site"'))

    def test_intro_video_waits_for_the_script(self):
        v = re.search(r"<video[^>]*data-intro-video[^>]*>", self.intro).group(0)
        for attr in ("muted", "playsinline", 'preload="none"'):
            self.assertIn(attr, v)
        self.assertNotIn("autoplay", v)
        self.assertIn('src="assets/video/brand-15s.mp4"', self.intro)

    def test_intro_buttons(self):
        sound = re.search(r"<button[^>]*data-intro-sound[^>]*>", self.intro).group(0)
        skip = re.search(r"<button[^>]*data-intro-skip[^>]*>", self.intro).group(0)
        for b in (sound, skip):
            self.assertIn('type="button"', b)
        # the visible label is the name (it says what a press does), so no
        # aria-label that could disagree with it
        self.assertNotIn("aria-label", sound)
        self.assertIn(">Sound on</button>", self.intro)

    def _end(self):
        m = re.search(r"const END = \{([^}]*)\}", self.js)
        self.assertIsNotNone(m, "no END in umbra.js")
        return {k: float(v) for k, v in re.findall(r"(\w+): ([\d.]+)", m.group(1))}

    def test_title_lands_where_the_film_draws_it(self):
        import s5_end
        L = s5_end.layout()
        end = self._end()
        self.assertEqual(end["w"], 1920)
        self.assertAlmostEqual(end["left"], L["left"], delta=0.01)
        self.assertAlmostEqual(end["top"], L["top"], delta=0.01)
        self.assertAlmostEqual(end["px"], s5_end.LINE_PX, delta=0.01)
        self.assertAlmostEqual(end["lh"], s5_end.LINE_LH, delta=1e-9)

    def test_handoff_is_after_the_lockup_and_before_the_fade(self):
        import timeline as tl
        t = float(re.search(r"const HANDOFF = ([\d.]+)", self.js).group(1))
        self.assertGreaterEqual(t, tl.LOCKUP_IN[1])
        self.assertLess(t, tl.FADE_OUT[0])


if __name__ == "__main__":
    unittest.main()
