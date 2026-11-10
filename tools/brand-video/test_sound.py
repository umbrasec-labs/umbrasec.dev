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
        n = int(tl.DURATION * sound.RATE)
        self.assertEqual(n, 1056000)
        self.assertEqual(len(self.raw[0]), n)
        self.assertEqual(len(self.raw[1]), n)
        self.assertEqual(len(self.l), n)

    def test_the_longer_film_plays_the_same_kit(self):
        # no new instruments: every cue is one of the first film's voices
        kit = {"bell", "cite", "confirm", "decode", "flick", "hat", "hop", "impact", "key",
               "kick", "live", "lock", "match", "ping", "pop", "purr", "riser", "shimmer",
               "slide", "swell", "thunk", "tick", "whoosh", "wire", "zip"}
        self.assertEqual({e.kind for e in tl.EVENTS}, kit)
        new = {e.kind for e in tl.EVENTS if tl.PAN_OUT[0] <= e.t < tl.FOLD[0]} - {"kick", "hat"}
        self.assertEqual(new, {"whoosh", "slide", "hop", "lock", "tick"})

    def test_the_anvil_still_strikes_once_on_the_landing(self):
        bells = [e for e in tl.EVENTS if e.kind == "bell"]
        self.assertEqual([e.t for e in bells], [tl.T_LAND])
        # the same strike as the first film, sample for sample
        strike, wet = sound.voice(bells[0])
        self.assertEqual(wet, 0.45)
        self.assertEqual(sound.ANVIL_SEED, 13517)
        self.assertEqual(strike, sound.anvil(seed=sound.ANVIL_SEED))

    def test_the_bed_reaches_the_new_collapse(self):
        kicks = [e.t for e in tl.EVENTS if e.kind == "kick"]
        self.assertEqual(kicks[-1], tl.COLLAPSE[0])
        self.assertEqual(len(kicks), int(tl.COLLAPSE[0] / tl.BEAT) + 1)
        hats = [e.t for e in tl.EVENTS if e.kind == "hat"]
        self.assertEqual((hats[0], hats[-1]), (3.25, 14.25))

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
