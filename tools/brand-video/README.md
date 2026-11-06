# Brand film renderer

Makes the 15 second film on the home page ("How this project works"): one
continuous shot from research to papers to a real rule catching its trace,
publishing, and the end card. Picture and sound are made in code from one cue
list (`timeline.py`), so they cannot drift apart.

Every string on screen comes from `content.py`, which checks it against the
repos at render time (quotes word for word, CVEs on the site, rule lines and
tags against the rule file and the hero reel, pack counts, KEV total, the
article's title and label, a fresh all-green Claims Ledger report) and refuses
to render on any mismatch.

## Needs

- Python 3.12 with pycairo and PyGObject (Pango, PangoCairo). No pip packages.
- GStreamer 1.x: `gst-launch-1.0`, `gst-discoverer-1.0`, openh264, voaacenc,
  mp4mux, jpegenc, pngdec.
- Network once: the fonts (Inter Tight, JetBrains Mono, OFL) download from
  Google Fonts into `.cache/` with a private fontconfig. Nothing is read from
  or written to the home folder's caches.
- A Claims Ledger report no older than 14 days: run the detections harness
  (see `../../../detections/README.md`, "Run it locally") and point
  `BRAND_VIDEO_CLAIMS` at its `out/predicate.json`, or leave it in
  `detections/out/`.

## Use

From the umbrasec.dev root:

```
# tests
BRAND_VIDEO_CLAIMS=<predicate.json> python3 -m unittest discover -s tools/brand-video -p 'test_*.py'

# a few frames and a contact sheet, to check against the storyboard
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py stills --at 2.4,8.6,14.5 --out <dir>

# the film: master with sound, silent site copy, poster, facts.json (about 5 minutes)
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py film --out <dir>

# figures on screen that changed since the last render (exit 1 if any)
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py drift
```

After a render, copy `<dir>/brand-15s.mp4` and `<dir>/brand-15s-poster.jpg`
to `assets/video/`, and update the "as of" date in the film's caption in
`index.html` to the `rendered` date in `facts.json`.

## The film is a dated snapshot

It shows the figures true on its render date (`facts.json`). When the pack or
the claims change, the site does not fail; `render.py drift` says what moved,
and a re-render is a choice (each one adds about 7 MB to the repo).

## Files

| File | What it does |
| --- | --- |
| `content.py` | every on-screen fact, checked against the repos |
| `timeline.py` | the clock: sections, cue times, sound events, motion blur windows |
| `draw.py` | palette, text, code lines, glow, grain, HUD, perspective cards |
| `s1_research.py` ... `s5_end.py` | the five sections |
| `compose.py` | one frame: background, sections, the dot, HUD, grain, motion blur |
| `sound.py` | the synth, mastering to -11.1 dBFS RMS under a -1 dBFS ceiling |
| `encode.py` | GStreamer: H.264 master and site copy in one pass, poster, probe |
| `render.py` | `stills`, `film` and `drift` |
| `fonts.py` | downloads the fonts and writes the private fontconfig |

This folder is not deployed (it is in the TRIM list of `tools/local-deploy/stage.sh`).
