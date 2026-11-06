"""The film's sound: right length, mastered to the reference's loudness, a clean loop."""
import math
import unittest

import sound
import timeline as tl


def rms_db(xs):
    m = sum(x * x for x in xs) / max(1, len(xs))
    return 10 * math.log10(m) if m > 0 else -200.0


class SoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        l, r = sound.synth(tl.EVENTS, tl.DURATION)
        cls.raw = (l, r)
        cls.l, cls.r = sound.master(l, r)

    def test_length(self):
        self.assertEqual(len(self.raw[0]), 720000)
        self.assertEqual(len(self.raw[1]), 720000)
        self.assertEqual(len(self.l), 720000)

    def test_levels(self):
        peak, rms = sound.levels(self.l, self.r)
        self.assertLessEqual(peak, -1.0)
        self.assertAlmostEqual(rms, -11.1, delta=2.0)

    def test_clean_loop(self):
        tail = int(0.15 * sound.RATE)
        self.assertLess(rms_db(list(self.l[-tail:]) + list(self.r[-tail:])), -50.0)
        self.assertEqual(self.l[0], 0.0)
        self.assertEqual(self.r[0], 0.0)


if __name__ == "__main__":
    unittest.main()
