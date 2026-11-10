"""One clock for picture and sound.

Every cue time lives here as a named constant. The scenes animate to these
names and the synth plays EVENTS, which is built from the same names, so the
picture and the sound cannot drift apart. 120 BPM: one beat is 0.5 s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from content import RULE_LINES

W, H, FPS, DURATION, BPM = 1920, 1080, 60, 22.0, 120
# What steps instead of moving (film grain, scrambled letters) changes this
# often, whatever FPS is: at 60 fps every second frame then differs only where
# something moves, which is what keeps the site copy inside its size budget.
TICK = 30
# Scenes draw in a W x H layout space; frames are rendered at OUT_W x OUT_H
# (1440p) by scaling that space up, so the layout and the intro's numbers in
# umbra.js do not change with the output size.
OUT_W, OUT_H = 2560, 1440
SCALE = OUT_W / W
MASTER_W, MASTER_H = 3840, 2160   # the optional 4K master (render.py film --master)
BEAT = 60.0 / BPM
FRAMES = round(DURATION * FPS)


def set_output(w: int, h: int) -> None:
    """Render at another frame size. The layout space stays W x H."""
    global OUT_W, OUT_H, SCALE
    if w * H != h * W:
        raise ValueError(f"{w} x {h} is not {W}:{H}")
    OUT_W, OUT_H, SCALE = w, h, w / W


@dataclass(frozen=True)
class Section:
    key: str
    label: str
    start: float
    end: float


SECTIONS = (
    Section("research", "Research", 0.0, 3.0),
    Section("papers", "Papers", 3.0, 6.0),
    Section("query", "Build the query", 6.0, 10.0),
    Section("exploited", "Exploited now", 10.0, 14.5),
    Section("publish", "Publish", 14.5, 19.0),
    Section("end", "End card", 19.0, 22.0),
)


def section_at(t: float) -> Section:
    for s in SECTIONS:
        if t < s.end:
            return s
    return SECTIONS[-1]


# 01 research
T_POP = 0.0                       # the dot pops on
T_PING = 0.5                      # sonar ring reveals the field
PING_END = 1.6
HOPS = (1.25, 1.5, 1.75, 2.0, 2.25)   # dot lands on each agent CVE
T_LOCK = 2.5                      # brackets snap shut
DIVE = (2.9, 3.2)                 # camera dives through the dot into the lock
# 02 papers
FLICKS = (3.0, 3.125, 3.25)       # pages flip up: left, centre, right
SWEEPS = ((3.5, 4.0), (4.0, 4.5), (4.5, 5.0))   # highlighter per page
CITES = (4.0, 4.5, 5.0)           # [1] [2] [3] land in the top bar
GATHER = (5.0, 5.5)               # highlights pull into the chip
T_CHIP = 5.5
CHIP_FLIGHT = (6.0, 6.375)        # chip flies to the rule's tag line, landing as it types
# 03 build the query
RULE_IN = (5.9, 6.2)
TYPE_START, TYPE_STEP = 6.125, 0.125  # one rule line per 16th note
TRACE_IN = (7.5, 7.875)
WIRE = (8.0, 8.4)                 # the dot draws the wire
T_MATCH = 8.5
COUNT = (8.5, 9.5)
T_CONFIRM = 9.5
# 04 exploited now
PAN_OUT = (9.95, 10.45)           # the camera whips right, from the rule to the KEV wall
WALL_IN = (10.2, 10.7)            # the wall's cells come up
SCAN = (10.75, 11.75)             # a beam reads the wall, top to bottom
SCAN_TICKS = tuple(SCAN[0] + i * 0.125 for i in range(8))   # a tick per 16th note
TO_LOCK = (11.75, 12.0)           # the dot crosses to the CVE the pack has work on
T_KEV_LOCK = 12.0                 # brackets snap on it
CARD_IN = (12.0, 12.4)            # its card: product, note, rule file, claims
T_TIER = 12.5                     # the tier badge stamps on
PAN_BACK = (13.95, 14.45)         # the camera whips back to the rule
# 05 publish
FOLD = (14.45, 15.0)              # rule panel folds into its tile
T_TILE = 15.0
BROWSER_IN = (15.1, 15.6)
TICKS = (15.5, 16.0, 16.5)        # umbrasec.dev, umbra-blue, detections
READ = (16.75, 17.5)              # the page is read: its text bars fill
T_LIVE = 17.5
COLLAPSE = (18.5, 19.0)           # everything pulls into the dot
# 06 end card
DECODE_1 = (19.0, 19.5)
DECODE_2 = (19.25, 19.75)
DOT_UP = (19.0, 19.35)
DOT_FALL = (19.65, 20.0)
T_LAND = 20.0
LOCKUP_IN = (20.3, 20.6)
SWEEP = (20.6, 21.3)              # a light crosses the title
FADE_OUT = (21.7, 22.0)


def _rule_line_times() -> tuple[float, ...]:
    """When each rule line appears: typed lines one per 16th note, a "..."
    line together with the line above it."""
    out, k = [], 0
    for i, ln in enumerate(RULE_LINES):
        if ln.strip() == "..." and i > 0:
            out.append(out[-1])
        else:
            out.append(TYPE_START + k * TYPE_STEP)
            k += 1
    return tuple(out)


RULE_LINE_T = _rule_line_times()

# windows that get sub-frame motion blur
FAST = ((1.05, 2.52), (2.85, 3.25), (5.0, 5.55), (6.0, 6.4), (7.5, 8.45),
        (PAN_OUT[0], PAN_OUT[1] + 0.1), (TO_LOCK[0], TO_LOCK[1] + 0.05),
        (PAN_BACK[0], FOLD[1] + 0.05), (COLLAPSE[0], COLLAPSE[1] + 0.05),
        (DOT_UP[0], DOT_UP[1] + 0.05), (DOT_FALL[0] - 0.05, T_LAND + 0.05))


def pan(t: float) -> float:
    """The camera's sideways move for "Exploited now": 0 on the rule, 1 on the
    KEV wall one frame width to its right."""
    return ease_in_out_cubic(prog(t, *PAN_OUT)) - ease_in_out_cubic(prog(t, *PAN_BACK))


@dataclass(frozen=True)
class Event:
    t: float
    kind: str
    pan: float = 0.0
    gain: float = 1.0
    n: int = 0


def _events() -> tuple[Event, ...]:
    ev: list[Event] = []
    add = ev.append
    # the bed: a soft kick on every beat up to the collapse, hats from 3.0 to
    # the end of "Exploited now"
    for i in range(int(COLLAPSE[0] / BEAT) + 1):
        t = i * BEAT
        add(Event(t, "kick", 0.0, 1.0 if i % 4 == 0 else 0.62))
    for i in range(int(3.0 / BEAT), int(SECTIONS[3].end / BEAT)):
        add(Event(i * BEAT + BEAT / 2, "hat", 0.25 if i % 2 else -0.25, 0.5))
    add(Event(T_POP, "pop"))
    add(Event(T_PING, "ping"))
    for i, t in enumerate(HOPS):
        add(Event(t, "hop", (-0.4, 0.15, 0.3, 0.05, -0.3)[i], 0.9, i))
    add(Event(T_LOCK, "lock"))
    add(Event(DIVE[0], "whoosh", 0.0, 1.0, 0))
    add(Event(3.0, "impact", 0.0, 0.7))
    for i, t in enumerate(FLICKS):
        add(Event(t, "flick", (-0.6, 0.0, 0.6)[i]))
    for i, (a, _) in enumerate(SWEEPS):
        add(Event(a, "zip", (-0.5, 0.0, 0.5)[i]))
    for i, t in enumerate(CITES):
        add(Event(t, "cite", (-0.5, 0.0, 0.5)[i], 0.8, i))
    add(Event(GATHER[0], "riser"))
    add(Event(T_CHIP, "thunk"))
    add(Event(CHIP_FLIGHT[0], "whoosh", 0.3, 0.6, 1))
    for i, (t, ln) in enumerate(zip(RULE_LINE_T, RULE_LINES)):
        if ln.strip() != "...":
            add(Event(t, "key", 0.3, 0.55, i))
    add(Event(TRACE_IN[0], "slide", -0.4))
    add(Event(WIRE[0], "wire", 0.0))
    add(Event(T_MATCH, "match"))
    add(Event(COUNT[0] + 0.02, "purr"))
    add(Event(T_CONFIRM, "confirm"))
    # exploited now: voices from the kit above, nothing new
    add(Event(PAN_OUT[0], "whoosh", 0.5, 0.7, 3))
    add(Event(WALL_IN[0] + 0.05, "slide", 0.3, 0.6))
    for i, t in enumerate(SCAN_TICKS):
        add(Event(t, "hop", -0.4 + 0.1 * i, 0.5, i % 5))
    add(Event(T_KEV_LOCK, "lock", 0.0, 0.8))
    add(Event(CARD_IN[0] + 0.02, "slide", 0.4, 0.6))
    add(Event(T_TIER, "tick", 0.4, 0.8, 1))
    add(Event(PAN_BACK[0], "whoosh", -0.4, 0.7, 4))
    add(Event(FOLD[0], "whoosh", 0.4, 0.8, 2))
    add(Event(T_TILE, "impact", 0.3, 1.0))
    for i, t in enumerate(TICKS):
        add(Event(t + 0.02, "tick", 0.45, 0.8, i))
    add(Event(BROWSER_IN[0], "slide", -0.3, 0.7))
    add(Event(T_LIVE, "live", -0.2, 0.7))
    add(Event(COLLAPSE[0] - 0.2, "swell"))
    for i in range(12):
        add(Event(DECODE_1[0] + i * 0.0625, "decode", (-0.3 + 0.05 * i), 0.5, i))
    add(Event(T_LAND, "bell"))
    add(Event(LOCKUP_IN[0], "shimmer", 0.0, 0.5))
    ev.sort(key=lambda e: (e.t, e.kind))
    return tuple(ev)


EVENTS = _events()


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def prog(t: float, t0: float, t1: float) -> float:
    """Where t sits between t0 and t1, clamped to 0..1."""
    return clamp01((t - t0) / (t1 - t0))


def lerp(a: float, b: float, x: float) -> float:
    return a + (b - a) * x


def ease_in_out_cubic(x: float) -> float:
    x = clamp01(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_cubic(x: float) -> float:
    return 1 - (1 - clamp01(x)) ** 3


def ease_in_cubic(x: float) -> float:
    return clamp01(x) ** 3


def ease_out_back(x: float, s: float = 1.70158) -> float:
    x = clamp01(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out_expo(x: float) -> float:
    x = clamp01(x)
    return 1.0 if x == 1.0 else 1 - 2 ** (-10 * x)


def timecode(t: float) -> str:
    f = int(round(t * FPS))
    s, ff = divmod(f, FPS)
    m, ss = divmod(s, 60)
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def fast(t: float) -> bool:
    return any(a <= t <= b for a, b in FAST)


def spring(x: float, freq: float = 3.0, decay: float = 6.0) -> float:
    """0 -> 1 with a damped overshoot, for pops and landings."""
    x = clamp01(x)
    return 1 - math.exp(-decay * x) * math.cos(freq * math.pi * x)
