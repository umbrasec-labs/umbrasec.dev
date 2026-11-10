# Brand film renderer

Makes the 22 second film on the home page: one continuous shot from research
to papers to a real rule catching its trace, the pack set against what is
exploited now, publishing, and the end card. Picture and sound are made in code
from one cue list (`timeline.py`), so they cannot drift apart.

| | Section | Seconds |
| --- | --- | --- |
| 01 | Research | 0.0 - 3.0 |
| 02 | Papers | 3.0 - 6.0 |
| 03 | Build the query | 6.0 - 10.0 |
| 04 | Exploited now | 10.0 - 14.5 |
| 05 | Publish | 14.5 - 19.0 |
| 06 | End card | 19.0 - 22.0 |

The first ten seconds are cue for cue the first (15 second) film.

The site copy is 2560 x 1440 at 60 frames a second. Scenes draw in a
1920 x 1080 layout space that `compose.frame` scales up (`timeline.OUT_W`,
`SCALE`), so positions and the coordinates in `umbra.js` do not depend on the
output size. Film grain and scrambled letters step 30 times a second
(`timeline.TICK`) whatever the frame rate, which keeps 60 fps inside the size
budget.

## Size budget

Cloudflare Pages refuses any file over 25 MiB, and the intro plays on every
visit. The site copy's budget is 20 MB (`encode.SITE_MAX_BYTES`): the bitrate
is chosen so the film cannot pass it, `render.py film` refuses a render that
does, and `test_encode.py` checks the committed file. 4K does not fit that
budget with openh264 at this quality (about half the bits per pixel), so 4K
exists only as the optional master below.

The site shows it twice. A first-time visitor gets it as an intro over the
blurred page (with sound where the browser allows it, Skip or Esc to close);
at the end card its title is swapped for real text that flies into the hero
headline (`assets/umbra.js`, introFilm). It also loops in "How this project
works", muted until the sound button is pressed. The intro needs to know where
the end card draws the title: `END` and `HANDOFF` in `umbra.js` come from
`s5_end.layout()` and `timeline.py`, and `test_site.py` fails if a re-render
moves them (`LANDS_FROM = 19.75`, `HANDOFF = 20.7`).

Every string on screen comes from `content.py`, which checks it against the
repos at render time (quotes word for word, CVEs on the site, rule lines and
tags against the rule file and the hero reel, pack counts, KEV total, the
article's title and label, a fresh all-green Claims Ledger report) and refuses
to render on any mismatch.

"Exploited now" is read at render time from `assets/exploited-latest.json`
(the KEV snapshot) and `assets/kev-coverage.json`, joined the way
`/api/exploited` joins them: the wall is every entry in the snapshot's window,
the tier counts are counted, and the wall carries the snapshot's own date
("as of ..."). The one card it opens is `content.KEV_CVE`. The film shows that
entry as the tier the site gives it, "Partial rule", with the coverage map's
note on what the rule leaves out; `content.py` refuses to render if the tier
is anything else, if the note, rule file or claim count differ from what
`/exploited` shows, or if the entry has left the window. Nothing in that
section says a rule caught an attack.

## Needs

- Python 3.12 with pycairo and PyGObject (Pango, PangoCairo). No pip packages.
- GStreamer 1.x: `gst-launch-1.0`, `gst-discoverer-1.0`, openh264, voaacenc,
  mp4mux, jpegenc, pngdec.
- Network once: the fonts (Inter Tight, JetBrains Mono, OFL) download from
  Google Fonts into `.cache/` with a private fontconfig. Nothing is read from
  or written to the home folder's caches.
  If the machine has its own, newer JetBrains Mono under `/usr/share/fonts`
  (Debian and Ubuntu: the `fonts-jetbrains-mono` package), fontconfig prefers
  it to the downloaded one and `test_fonts.py` fails; remove that package
  before rendering.
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

# the film: site copy (with sound), poster, facts.json (about 4 minutes on 4 cores)
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py film --out <dir>

# the same, plus the 4K master (a second pass, about 10 minutes more)
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py film --out <dir> --master

# new sound only: swap the soundtrack of the films in <dir>, picture untouched
python3 tools/brand-video/render.py sound --out <dir>

# figures on screen that changed since the last render (exit 1 if any)
BRAND_VIDEO_CLAIMS=<predicate.json> python3 tools/brand-video/render.py drift
```

After a render, copy `<dir>/brand-film.mp4` and `<dir>/brand-film-poster.jpg`
to `assets/video/`, and update the two "as of" dates in the film's caption in
`index.html`: the `rendered` date and the `kev_date` in `facts.json`.

`--jobs N` sets how many processes render frames (default: every core).

## The 4K master

`--master` writes `umbrasec-brand-film-2160p60.mp4` (3840 x 2160, 60 fps) to
`tools/brand-video/out/`. That folder is git-ignored, and Pages only ever
receives `git archive HEAD` minus the folders `tools/local-deploy/stage.sh`
trims, of which `tools/brand-video` is one, so the master can be neither
committed nor served. `--master DIR` writes it elsewhere; a folder inside the
repo that git does not ignore is refused.

## The film is a dated snapshot

It shows the figures true on its render date (`facts.json`), and the KEV wall
as of the snapshot's date. When the pack, the claims, the snapshot or the
coverage map change, the site does not fail; `render.py drift` says what moved
(the snapshot's date, the tier counts, how many CVEs joined or left the wall
and which changed tier, the card's note, rule and claim count), and a re-render
is a choice (each one adds about 16 MB to the repo).

## Files

| File | What it does |
| --- | --- |
| `content.py` | every on-screen fact, checked against the repos |
| `timeline.py` | the clock: sections, cue times, sound events, motion blur windows, the camera pan |
| `draw.py` | palette, text, code lines, glow, grain, dust, light sweeps, HUD, perspective cards |
| `s1_research.py` ... `s5_end.py` | the sections; `s3x_exploited.py` is "Exploited now", between 03 and Publish |
| `compose.py` | one frame: background, sections under the camera, the dot, HUD, grain, motion blur |
| `sound.py` | the synth, mastering to -11.1 dBFS RMS under a -1 dBFS ceiling |
| `encode.py` | GStreamer: H.264 site copy and master, the size budget, poster, probe |
| `render.py` | `stills`, `film`, `sound` and `drift` |
| `fonts.py` | downloads the fonts and writes the private fontconfig |

This folder is not deployed (it is in the TRIM list of `tools/local-deploy/stage.sh`).
