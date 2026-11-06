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

    def test_a_late_close_lands_the_title_only_once_it_has_decoded(self):
        import timeline as tl
        t = float(re.search(r"const LANDS_FROM = ([\d.]+)", self.js).group(1))
        self.assertGreaterEqual(t, tl.DECODE_2[1])
        self.assertLess(t, float(re.search(r"const HANDOFF = ([\d.]+)", self.js).group(1)))

    def test_skip_names_its_key(self):
        skip = re.search(r"<button[^>]*data-intro-skip[^>]*>.*?</button>", self.intro, re.S).group(0)
        self.assertIn('aria-keyshortcuts="Escape"', skip)
        # the name stays "Skip intro"; the key is announced from aria-keyshortcuts
        self.assertIn('<kbd aria-hidden="true">Esc</kbd>', skip)


class IntroCssTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (SITE / "assets" / "umbra.css").read_text(encoding="utf-8")

    def _rule(self, selector):
        m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(m, selector)
        return m.group(1)

    def test_the_scrollbar_keeps_its_place(self):
        # locking the page must not change its width, or the film box and
        # the hero jump on classic-scrollbar systems
        self.assertIn("scrollbar-gutter: stable", self._rule("html.intro-on"))

    def test_the_film_box_fits_phone_toolbars(self):
        box = self._rule(".intro-box")
        self.assertIn("100vh", box)     # fallback first
        self.assertIn("100svh", box)
        self.assertLess(box.index("100vh"), box.index("100svh"))

    def test_forced_colors_beat_the_open_state(self):
        blocks = re.findall(r"@media \(forced-colors: active\) \{(.*?)\n\}", self.css, re.S)
        intro = [b for b in blocks if ".intro" in b]
        self.assertEqual(len(intro), 1)
        self.assertIn(".intro, .intro.is-open", intro[0])
        self.assertIn(".intro-btn.is-invite { border-color: Highlight; }", intro[0])


if __name__ == "__main__":
    unittest.main()
