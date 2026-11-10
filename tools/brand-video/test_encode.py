"""The encoder, the size budget of the site copy, and where the 4K master may go."""
import tempfile
import unittest
from array import array
from pathlib import Path

import encode
import sound
import timeline as tl

SITE = Path(__file__).resolve().parents[2]


class EncodeTest(unittest.TestCase):
    def test_pipeline_one_second(self):
        frame = bytes([0x17, 0x17, 0x17, 0xFF]) * (2560 * 1440)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            wav = tmp / "s.wav"
            silence = array("f", [0.0] * sound.RATE)
            sound.write_wav(wav, silence, silence)
            site = tmp / "site.mp4"
            encode.film((frame for _ in range(tl.FPS)), wav, site, bps=encode.SITE_BPS,
                        audio_bps=encode.SITE_AUDIO_BPS)
            s = encode.probe(site)
            self.assertEqual((s["width"], s["height"], s["fps"]), (2560, 1440, f"{tl.FPS}/1"))
            self.assertIn("H.264", s["video"])
            self.assertEqual((s["audio_channels"], s["audio_rate"]), (2, 48000))
            self.assertAlmostEqual(s["duration"], 1.0, delta=1 / 30 + 1e-6)

    def test_pipeline_follows_the_output_size(self):
        # the 4K master goes through the same pipeline, at timeline's master size
        try:
            tl.set_output(tl.MASTER_W, tl.MASTER_H)
            frame = bytes([0x17, 0x17, 0x17, 0xFF]) * (tl.OUT_W * tl.OUT_H)
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                wav = tmp / "s.wav"
                silence = array("f", [0.0] * (sound.RATE // 2))
                sound.write_wav(wav, silence, silence)
                master = tmp / "master.mp4"
                encode.film((frame for _ in range(tl.FPS // 2)), wav, master,
                            bps=encode.MASTER_BPS, audio_bps=encode.MASTER_AUDIO_BPS)
                m = encode.probe(master)
                self.assertEqual((m["width"], m["height"], m["fps"]), (3840, 2160, f"{tl.FPS}/1"))
        finally:
            tl.set_output(2560, 1440)


class SiteCopyBudgetTest(unittest.TestCase):
    """Cloudflare Pages refuses a file over 25 MiB, and the film plays on every visit."""

    def test_the_bitrate_cannot_carry_the_site_copy_past_its_budget(self):
        self.assertEqual(encode.PAGES_MAX_BYTES, 25 * 1024 * 1024)
        self.assertLessEqual(encode.SITE_MAX_BYTES, 20_000_000)
        self.assertLess(encode.SITE_MAX_BYTES, encode.PAGES_MAX_BYTES)
        # even if the encoder spends every bit it is allowed
        self.assertLess(encode.site_bytes_estimate(), encode.SITE_MAX_BYTES)

    def test_the_committed_site_copy_is_under_budget_and_is_this_film(self):
        film = SITE / "assets" / "video" / "brand-film.mp4"
        size = film.stat().st_size
        self.assertLessEqual(size, encode.SITE_MAX_BYTES, f"{size:,} bytes")
        p = encode.probe(film)
        self.assertEqual((p["width"], p["height"]), (tl.OUT_W, tl.OUT_H))
        self.assertEqual(p["fps"], f"{tl.FPS}/1")
        self.assertAlmostEqual(p["duration"], tl.DURATION, delta=0.05)
        self.assertEqual((p["audio_channels"], p["audio_rate"]), (2, 48000))

    def test_the_committed_poster_is_1440p_and_small(self):
        jpg = SITE / "assets" / "video" / "brand-film-poster.jpg"
        self.assertLessEqual(jpg.stat().st_size, encode.POSTER_MAX)
        p = encode.probe(jpg)
        self.assertEqual((p["width"], p["height"]), (2560, 1440))


class MasterTest(unittest.TestCase):
    """The 4K master is never committed and never served."""

    def test_the_default_folder_is_git_ignored_and_never_staged(self):
        import render
        import subprocess
        self.assertEqual(render.MASTER_DIR, SITE / "tools" / "brand-video" / "out")
        target = render.MASTER_DIR / render.master_name()
        self.assertEqual(render.master_name(), f"umbrasec-brand-film-2160p{tl.FPS}.mp4")
        r = subprocess.run(["git", "-C", str(SITE), "check-ignore", "-q", str(target)])
        self.assertEqual(r.returncode, 0, "tools/brand-video/out/ is no longer git-ignored")
        # Pages only ever gets "git archive HEAD" minus the TRIM list, and this
        # whole folder is on that list as well
        stage = (SITE / "tools" / "local-deploy" / "stage.sh").read_text(encoding="utf-8")
        self.assertIn("git -C \"$REPO\" archive HEAD", stage)
        self.assertIn('"tools/brand-video"', stage)
        self.assertEqual(render.check_master_dir(render.MASTER_DIR), render.MASTER_DIR.resolve())

    def test_a_tracked_folder_is_refused(self):
        import render
        for bad in (SITE / "assets" / "video", SITE, SITE / "tools" / "brand-video"):
            with self.assertRaises(SystemExit, msg=str(bad)):
                render.check_master_dir(bad)

    def test_a_folder_outside_the_repo_is_fine(self):
        import render
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(render.check_master_dir(Path(tmp)), Path(tmp).resolve())


if __name__ == "__main__":
    unittest.main()
