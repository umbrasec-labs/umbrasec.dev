import unittest

import timeline as tl
from content import RULE_LINES


def on_beat(t):
    return abs(t / tl.BEAT - round(t / tl.BEAT)) < 1e-9


class TimelineTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual((tl.W, tl.H, tl.DURATION, tl.BPM, tl.BEAT), (1920, 1080, 22.0, 120, 0.5))
        # 60 fps, or 30 as the fallback; what steps does so 30 times a second either way
        self.assertIn(tl.FPS, (60, 30))
        self.assertEqual(tl.TICK, 30)
        self.assertEqual(tl.FRAMES, int(22 * tl.FPS))
        self.assertEqual((tl.OUT_W, tl.OUT_H), (2560, 1440))
        self.assertEqual((tl.MASTER_W, tl.MASTER_H), (3840, 2160))

    def test_the_layout_space_does_not_follow_the_output_size(self):
        try:
            tl.set_output(3840, 2160)
            self.assertEqual((tl.W, tl.H, tl.SCALE), (1920, 1080, 2.0))
            with self.assertRaises(ValueError):
                tl.set_output(3840, 2000)
        finally:
            tl.set_output(2560, 1440)
        self.assertEqual((tl.OUT_W, tl.OUT_H), (2560, 1440))

    def test_sections_contiguous_on_beats(self):
        keys = [s.key for s in tl.SECTIONS]
        self.assertEqual(keys, ["research", "papers", "query", "exploited", "publish", "end"])
        self.assertEqual(tl.SECTIONS[0].start, 0.0)
        self.assertEqual(tl.SECTIONS[-1].end, tl.DURATION)
        for a, b in zip(tl.SECTIONS, tl.SECTIONS[1:]):
            self.assertEqual(a.end, b.start)
        for s in tl.SECTIONS:
            self.assertTrue(on_beat(s.start) and on_beat(s.end), s)
        self.assertEqual([(s.start, s.end) for s in tl.SECTIONS],
                         [(0.0, 3.0), (3.0, 6.0), (6.0, 10.0), (10.0, 14.5), (14.5, 19.0),
                          (19.0, 22.0)])

    def test_the_first_ten_seconds_are_the_first_film(self):
        # the hook: every cue up to the confirm is where the 15 s film had it
        self.assertEqual((tl.T_POP, tl.T_PING, tl.PING_END, tl.T_LOCK, tl.DIVE), (0.0, 0.5, 1.6, 2.5, (2.9, 3.2)))
        self.assertEqual(tl.HOPS, (1.25, 1.5, 1.75, 2.0, 2.25))
        self.assertEqual((tl.FLICKS, tl.CITES), ((3.0, 3.125, 3.25), (4.0, 4.5, 5.0)))
        self.assertEqual(tl.SWEEPS, ((3.5, 4.0), (4.0, 4.5), (4.5, 5.0)))
        self.assertEqual((tl.GATHER, tl.T_CHIP, tl.CHIP_FLIGHT), ((5.0, 5.5), 5.5, (6.0, 6.375)))
        self.assertEqual((tl.RULE_IN, tl.TYPE_START, tl.TYPE_STEP), ((5.9, 6.2), 6.125, 0.125))
        self.assertEqual((tl.TRACE_IN, tl.WIRE, tl.T_MATCH, tl.COUNT, tl.T_CONFIRM),
                         ((7.5, 7.875), (8.0, 8.4), 8.5, (8.5, 9.5), 9.5))
        self.assertEqual(tl.FAST[:5], ((1.05, 2.52), (2.85, 3.25), (5.0, 5.55), (6.0, 6.4), (7.5, 8.45)))
        # and so is every sound before the camera leaves the rule
        early = [e for e in tl.EVENTS if e.t < tl.PAN_OUT[0]]
        self.assertEqual(len(early), 74)
        self.assertEqual(max(e.t for e in early), 9.75)
        self.assertEqual(tl.pan(tl.PAN_OUT[0]), 0.0)

    def test_exploited_now_cues_run_in_order(self):
        self.assertEqual(tl.PAN_OUT[0], tl.T_CONFIRM + 0.45)   # where the first film began to fold
        order = [tl.PAN_OUT[0], tl.WALL_IN[0], tl.PAN_OUT[1], tl.WALL_IN[1], tl.SCAN[0], tl.SCAN[1],
                 tl.TO_LOCK[1], tl.T_KEV_LOCK, tl.CARD_IN[1], tl.T_TIER, tl.PAN_BACK[0],
                 tl.PAN_BACK[1], tl.FOLD[0]]
        self.assertEqual(order, sorted(order))
        # the card is whole for at least a second and a half before the camera leaves
        self.assertGreaterEqual(tl.PAN_BACK[0] - tl.CARD_IN[1], 1.5)
        self.assertEqual(tl.SCAN_TICKS[0], tl.SCAN[0])
        self.assertLess(tl.SCAN_TICKS[-1], tl.SCAN[1])
        for a, b in zip(tl.SCAN_TICKS, tl.SCAN_TICKS[1:]):
            self.assertAlmostEqual(b - a, 0.125)   # 16th notes

    def test_the_camera_pans_out_and_all_the_way_back(self):
        self.assertEqual(tl.pan(0.0), 0.0)
        self.assertEqual(tl.pan(tl.PAN_OUT[1]), 1.0)
        self.assertEqual(tl.pan((tl.PAN_OUT[1] + tl.PAN_BACK[0]) / 2), 1.0)
        self.assertEqual(tl.pan(tl.PAN_BACK[1]), 0.0)
        self.assertEqual(tl.pan(tl.DURATION), 0.0)
        for w in (tl.PAN_OUT, tl.PAN_BACK):   # both whips are motion-blurred
            self.assertTrue(tl.fast(w[0]) and tl.fast(w[1]))

    def test_publish_and_end_card_cues(self):
        order = [tl.FOLD[0], tl.FOLD[1], tl.T_TILE, tl.BROWSER_IN[0], tl.TICKS[0], tl.TICKS[2],
                 tl.READ[0], tl.READ[1], tl.T_LIVE, tl.COLLAPSE[0], tl.COLLAPSE[1], tl.DECODE_1[0],
                 tl.DECODE_2[1], tl.T_LAND, tl.LOCKUP_IN[1], tl.SWEEP[0], tl.SWEEP[1],
                 tl.FADE_OUT[0], tl.FADE_OUT[1]]
        self.assertEqual(order, sorted(order))
        self.assertEqual((tl.T_LAND, tl.FADE_OUT[1]), (20.0, tl.DURATION))
        for t in tl.TICKS:
            self.assertTrue(on_beat(t), t)   # one destination a beat
        self.assertGreaterEqual(tl.COLLAPSE[0] - tl.T_LIVE, 1.0)

    def test_section_at(self):
        self.assertEqual(tl.section_at(0.0).key, "research")
        self.assertEqual(tl.section_at(2.999).key, "research")
        self.assertEqual(tl.section_at(3.0).key, "papers")
        self.assertEqual(tl.section_at(10.0).key, "exploited")
        self.assertEqual(tl.section_at(14.5).key, "publish")
        self.assertEqual(tl.section_at(21.99).key, "end")

    def test_events_sorted_within_film(self):
        ts = [e.t for e in tl.EVENTS]
        self.assertEqual(ts, sorted(ts))
        self.assertTrue(all(0.0 <= t < tl.DURATION for t in ts))
        self.assertTrue(all(-1.0 <= e.pan <= 1.0 for e in tl.EVENTS))

    def test_major_hits_on_beats(self):
        major = {"pop", "ping", "lock", "impact", "thunk", "match", "confirm", "bell", "kick"}
        hits = [e for e in tl.EVENTS if e.kind in major]
        self.assertGreater(len(hits), 20)
        for e in hits:
            self.assertTrue(on_beat(e.t), e)

    def test_fast_windows_within_film(self):
        for a, b in tl.FAST:
            self.assertTrue(0.0 <= a < b <= tl.DURATION)

    def test_timecode(self):
        self.assertEqual(tl.timecode(0.0), "00:00:00:00")
        self.assertEqual(tl.timecode(2.4), f"00:00:02:{round(0.4 * tl.FPS):02d}")
        self.assertEqual(tl.timecode(21.5), f"00:00:21:{tl.FPS // 2:02d}")

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
