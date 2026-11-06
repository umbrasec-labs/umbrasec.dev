import unittest

import timeline as tl
from content import RULE_LINES


def on_beat(t):
    return abs(t / tl.BEAT - round(t / tl.BEAT)) < 1e-9


class TimelineTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual((tl.W, tl.H, tl.FPS, tl.DURATION, tl.BPM, tl.BEAT),
                         (1920, 1080, 30, 15.0, 120, 0.5))

    def test_sections_contiguous_on_beats(self):
        keys = [s.key for s in tl.SECTIONS]
        self.assertEqual(keys, ["research", "papers", "query", "publish", "end"])
        self.assertEqual(tl.SECTIONS[0].start, 0.0)
        self.assertEqual(tl.SECTIONS[-1].end, 15.0)
        for a, b in zip(tl.SECTIONS, tl.SECTIONS[1:]):
            self.assertEqual(a.end, b.start)
        for s in tl.SECTIONS:
            self.assertTrue(on_beat(s.start) and on_beat(s.end), s)
        self.assertEqual([(s.start, s.end) for s in tl.SECTIONS],
                         [(0.0, 3.0), (3.0, 6.0), (6.0, 10.0), (10.0, 12.5), (12.5, 15.0)])

    def test_section_at(self):
        self.assertEqual(tl.section_at(0.0).key, "research")
        self.assertEqual(tl.section_at(2.999).key, "research")
        self.assertEqual(tl.section_at(3.0).key, "papers")
        self.assertEqual(tl.section_at(14.99).key, "end")

    def test_events_sorted_within_film(self):
        ts = [e.t for e in tl.EVENTS]
        self.assertEqual(ts, sorted(ts))
        self.assertTrue(all(0.0 <= t < 15.0 for t in ts))
        self.assertTrue(all(-1.0 <= e.pan <= 1.0 for e in tl.EVENTS))

    def test_major_hits_on_beats(self):
        major = {"pop", "ping", "lock", "impact", "thunk", "match", "confirm", "bell", "kick"}
        hits = [e for e in tl.EVENTS if e.kind in major]
        self.assertGreater(len(hits), 20)
        for e in hits:
            self.assertTrue(on_beat(e.t), e)

    def test_fast_windows_within_film(self):
        for a, b in tl.FAST:
            self.assertTrue(0.0 <= a < b <= 15.0)

    def test_timecode(self):
        self.assertEqual(tl.timecode(0.0), "00:00:00:00")
        self.assertEqual(tl.timecode(2.4), "00:00:02:12")
        self.assertEqual(tl.timecode(14.5), "00:00:14:15")

    def test_easing_endpoints(self):
        for f in (tl.ease_in_out_cubic, tl.ease_out_cubic, tl.ease_in_cubic,
                  tl.ease_out_back, tl.ease_out_expo):
            self.assertAlmostEqual(f(0.0), 0.0, places=6, msg=f.__name__)
            self.assertAlmostEqual(f(1.0), 1.0, places=6, msg=f.__name__)

    def test_rule_lines_type_on_sixteenths(self):
        # one key per typed line, a "..." line shows with the line above it,
        # and the rule is whole before the wire starts
        self.assertEqual(len(tl.RULE_LINE_T), len(RULE_LINES))
        typed = [t for t, ln in zip(tl.RULE_LINE_T, RULE_LINES) if ln.strip() != "..."]
        keys = [e.t for e in tl.EVENTS if e.kind == "key"]
        self.assertEqual(keys, typed)
        for a, b in zip(typed, typed[1:]):
            self.assertAlmostEqual(b - a, tl.TYPE_STEP)
        for i, ln in enumerate(RULE_LINES):
            if ln.strip() == "..." and i > 0:
                self.assertEqual(tl.RULE_LINE_T[i], tl.RULE_LINE_T[i - 1])
        self.assertLess(max(tl.RULE_LINE_T), tl.WIRE[0])

    def test_prog_clamps(self):
        self.assertEqual(tl.prog(0.0, 1.0, 2.0), 0.0)
        self.assertEqual(tl.prog(1.5, 1.0, 2.0), 0.5)
        self.assertEqual(tl.prog(3.0, 1.0, 2.0), 1.0)
        self.assertEqual(tl.lerp(10, 20, 0.25), 12.5)


if __name__ == "__main__":
    unittest.main()
