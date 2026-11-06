"""One clock for picture and sound.

Every cue time lives here as a named constant. The scenes animate to these
names and the synth plays EVENTS, which is built from the same names, so the
picture and the sound cannot drift apart. 120 BPM: one beat is 0.5 s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from content import RULE_LINES

W, H, FPS, DURATION, BPM = 1920, 1080, 30, 15.0, 120
BEAT = 60.0 / BPM
FRAMES = int(DURATION * FPS)


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
    Section("publish", "Publish", 10.0, 12.5),
    Section("end", "End card", 12.5, 15.0),
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
DIVE = (2.72, 3.18)               # camera dives into the lock
# 02 papers
FLICKS = (3.0, 3.125, 3.25)       # pages flip up: left, centre, right
SWEEPS = ((3.5, 4.0), (4.0, 4.5), (4.5, 5.0))   # highlighter per page
CITES = (4.0, 4.5, 5.0)           # [1] [2] [3] land in the top bar
GATHER = (5.0, 5.5)               # highlights pull into the chip
T_CHIP = 5.5
CHIP_FLIGHT = (5.85, 6.2)         # chip flies to the rule's tag line
# 03 build the query
RULE_IN = (5.9, 6.2)
TYPE_START, TYPE_STEP = 6.125, 0.125  # one rule line per 16th note
TRACE_IN = (7.5, 7.875)
WIRE = (8.0, 8.4)                 # the dot draws the wire
T_MATCH = 8.5
COUNT = (8.5, 9.5)
T_CONFIRM = 9.5
# 04 publish
FOLD = (9.95, 10.5)               # rule panel folds into its tile
T_TILE = 10.5
TICKS = (10.5, 10.75, 11.0)       # umbrasec.dev, umbra-blue, detections
BROWSER_IN = (10.6, 11.1)
T_LIVE = 11.25
COLLAPSE = (12.0, 12.5)           # everything pulls into the dot
# 05 end card
DECODE_1 = (12.5, 13.0)
DECODE_2 = (12.75, 13.25)
DOT_UP = (12.5, 12.85)
DOT_FALL = (13.15, 13.5)
T_LAND = 13.5
LOCKUP_IN = (13.8, 14.1)
FADE_OUT = (14.7, 15.0)

# windows that get sub-frame motion blur
FAST = ((1.2, 2.3), (2.7, 3.25), (5.0, 5.55), (5.85, 6.2), (8.0, 8.45),
        (9.95, 10.55), (12.0, 12.55), (12.5, 12.9), (13.1, 13.55))


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
    # the bed: a soft kick on every beat up to the collapse, hats from 3.0 to 10.0
    for i in range(int(COLLAPSE[0] / BEAT) + 1):
        t = i * BEAT
        add(Event(t, "kick", 0.0, 1.0 if i % 4 == 0 else 0.62))
    for i in range(int(3.0 / BEAT), int(10.0 / BEAT)):
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
    for i in range(len(RULE_LINES)):
        add(Event(TYPE_START + i * TYPE_STEP, "key", 0.3, 0.55, i))
    add(Event(TRACE_IN[0], "slide", -0.4))
    add(Event(WIRE[0], "wire", 0.0))
    add(Event(T_MATCH, "match"))
    add(Event(COUNT[0] + 0.02, "purr"))
    add(Event(T_CONFIRM, "confirm"))
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
