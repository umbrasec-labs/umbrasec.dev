"""The film on the home page: placed in "How this project works", lazy, muted,
captioned in plain words, and dated with the render it shows."""
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

    def test_caption_is_plain_and_dated_by_the_render(self):
        cap = re.search(r'<figcaption id="film-desc"[^>]*>(.*?)</figcaption>', self.fig, re.S)
        text = re.sub(r"<[^>]+>", "", cap.group(1))
        self.assertNotRegex(text, r"CVE-\d")
        rendered = date.fromisoformat(json.loads((HERE / "facts.json").read_text())["rendered"])
        self.assertIn(f"as of {as_of(rendered)}", text)


if __name__ == "__main__":
    unittest.main()
