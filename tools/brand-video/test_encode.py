"""The encoder: one pipeline makes the master and the site copy, both with sound."""
import tempfile
import unittest
from array import array
from pathlib import Path

import encode
import sound


class EncodeTest(unittest.TestCase):
    def test_pipeline_one_second(self):
        frame = bytes([0x17, 0x17, 0x17, 0xFF]) * (1920 * 1080)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            wav = tmp / "s.wav"
            silence = array("f", [0.0] * sound.RATE)
            sound.write_wav(wav, silence, silence)
            master, site = tmp / "master.mp4", tmp / "site.mp4"
            encode.film((frame for _ in range(30)), wav, master, site)
            m = encode.probe(master)
            self.assertEqual((m["width"], m["height"], m["fps"]), (1920, 1080, "30/1"))
            self.assertIn("H.264", m["video"])
            self.assertEqual((m["audio_channels"], m["audio_rate"]), (2, 48000))
            self.assertAlmostEqual(m["duration"], 1.0, delta=1 / 30 + 1e-6)
            s = encode.probe(site)
            self.assertEqual((s["width"], s["height"]), (1920, 1080))
            self.assertEqual((s["audio_channels"], s["audio_rate"]), (2, 48000))
            self.assertAlmostEqual(s["duration"], 1.0, delta=1 / 30 + 1e-6)


if __name__ == "__main__":
    unittest.main()
