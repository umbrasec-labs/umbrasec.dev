"""render.py: what drift reports and what the facts file holds."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import content
import render

SITE = Path(__file__).resolve().parents[2]


class FramesTest(unittest.TestCase):
    """Parallel rendering gives the same frames in the same order, and never
    runs far ahead of the encoder."""

    def test_parallel_frames_are_the_serial_frames_in_order(self):
        import hashlib
        import timeline as tl
        c = content.load(SITE, SITE.parent / "detections")
        sha = lambda gen: [hashlib.sha256(f).hexdigest() for f in gen]
        pool = render.workers(c, 3)
        try:
            tl.set_output(480, 270)   # small frames: this is about order, not pixels
            serial = sha(render._frames(None, 1, 12))
            parallel = sha(render._frames(pool, 3, 12))
            # the same workers then render another size, as they do for the master
            tl.set_output(960, 540)
            big_serial = sha(render._frames(None, 1, 4))
            big_parallel = sha(render._frames(pool, 3, 4))
        finally:
            pool.terminate()
            pool.join()
            tl.set_output(2560, 1440)
        self.assertEqual(len(set(serial)), 12)
        self.assertEqual(parallel, serial)
        self.assertEqual(big_parallel, big_serial)
        self.assertNotEqual(big_serial[0], serial[0])

    def test_frames_waiting_for_the_encoder_are_bounded(self):
        import timeline as tl
        self.assertLessEqual(render.ahead(64), 128)
        # the 4K master's waiting frames fit in memory many times over
        frame = tl.MASTER_W * tl.MASTER_H * 4
        self.assertLess(render.ahead(8) * frame, 1 << 30)


class FactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = content.load(SITE, SITE.parent / "detections")

    def test_facts_hold_the_wall_its_counts_and_its_date(self):
        f = render.facts(self.c)
        for k in ("kev_date", "kev_days", "kev_tiers", "kev_wall", "kev_cve", "kev_tier",
                  "kev_note", "kev_rule", "kev_claims"):
            self.assertIn(k, f)
        self.assertEqual(f["kev_date"], self.c.kev_date)
        self.assertEqual(f["kev_wall"], [list(x) for x in self.c.kev_wall])
        self.assertEqual(f["kev_tiers"], [list(x) for x in self.c.kev_tiers])
        self.assertEqual(json.loads(json.dumps(f)), f)   # plain JSON types

    def test_the_committed_facts_are_this_films(self):
        f = json.loads(render.FACTS.read_text())
        self.assertEqual(set(f), {"rendered", *render.FIGURES})
        self.assertEqual(f["kev_cve"], content.KEV_CVE)
        self.assertEqual(f["kev_tier"], content.KEV_TIER)

    def _drift(self, **changed):
        """drift() against a facts file that differs from the repos in `changed`."""
        then = render.facts(self.c)
        then.update(changed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "facts.json"
            path.write_text(json.dumps(then))
            with mock.patch.object(render, "FACTS", path):
                return render.drift()

    def test_no_drift_against_itself(self):
        self.assertEqual(self._drift(), [])

    def test_drift_flags_the_date_and_the_counts(self):
        tiers = [list(x) for x in self.c.kev_tiers]
        tiers[-1][2] -= 1
        out = self._drift(kev_date="2026-10-01", kev_tiers=tiers)
        self.assertEqual(len(out), 2)
        self.assertTrue(any(ln.startswith("kev_date:") and "2026-10-01" in ln for ln in out))
        self.assertTrue(any(ln.startswith("kev_tiers:") for ln in out))

    def test_drift_names_what_happened_to_the_wall(self):
        wall = [list(x) for x in self.c.kev_wall]
        gone = wall.pop(3)                     # the film showed one that has since left...
        wall.insert(0, ["CVE-2020-0001", "gap"])   # ...lacked one that has joined...
        i = next(k for k, (cve, _) in enumerate(wall) if cve == self.c.kev_cve)
        wall[i] = [self.c.kev_cve, "writeup"]  # ...and showed the card's CVE in another tier
        out = self._drift(kev_wall=wall)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("kev_wall: 1 joined, 1 left"), out[0])
        self.assertIn(f"{self.c.kev_cve} is partial now, was writeup", out[0])
        self.assertNotIn(gone[0], out[0])      # counted, not listed: the wall can be long

    def test_drift_flags_the_card(self):
        out = self._drift(kev_claims=self.c.kev_claims - 1, kev_note="An older note.")
        self.assertEqual(sorted(ln.split(":")[0] for ln in out), ["kev_claims", "kev_note"])


if __name__ == "__main__":
    unittest.main()
