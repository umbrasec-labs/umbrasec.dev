"""The film's sound, made in code from the same cue list as the picture.

synth() plays timeline.EVENTS: a soft pad bed ducked by a kick on every beat,
and one small voice per cue kind (sonar ping, hop blips, paper flicks,
highlighter zips, key clicks, the match chime, the counter purr, whooshes,
the anvil strike on the landing). Pure Python, no dependencies. master() brings it to
the reference showreel's loudness (-11.1 dBFS mean RMS) under a -1 dBFS soft
ceiling; the last 0.15 s is silent so the loop on the site restarts cleanly.
"""
from __future__ import annotations

import math
import random
import wave
from array import array
from pathlib import Path

import timeline as tl

RATE = 48000
TAU = 2 * math.pi


def _n(seconds: float) -> int:
    return int(round(seconds * RATE))


def tone(freq: float, dur: float, decay: float, *, to: float | None = None,
         attack: float = 0.002, parts=((1.0, 1.0),), shape=None) -> list[float]:
    """Sine partials with an exponential decay; `to` glides the pitch; `shape`
    (0..1 -> gain) replaces the decay envelope."""
    n = _n(dur)
    out = [0.0] * n
    phases = [0.0] * len(parts)
    k_att = 1 / max(1, _n(attack))
    k_dec = 1 / max(1e-9, decay * RATE)
    norm = 1 / sum(a for _, a in parts)
    for i in range(n):
        x = i / n
        f = freq * (to / freq) ** x if to else freq
        s = 0.0
        for j, (m, a) in enumerate(parts):
            phases[j] += TAU * f * m / RATE
            s += a * math.sin(phases[j])
        env = shape(x) if shape else math.exp(-i * k_dec)
        out[i] = s * norm * env * min(1.0, i * k_att)
    return out


def noise(dur: float, decay: float, *, seed: int, hp: float = 0.0, lp: float = 1.0,
          shape=None) -> list[float]:
    """Filtered white noise: one-pole low-pass (lp 0..1) then high-pass (hp 0..1)."""
    rng = random.Random(seed)
    n = _n(dur)
    out = [0.0] * n
    lo = prev = hi = 0.0
    k_dec = 1 / max(1e-9, decay * RATE)
    for i in range(n):
        w = rng.uniform(-1.0, 1.0)
        lo += lp * (w - lo)
        hi = (1 - hp) * (hi + lo - prev) if hp else lo
        prev = lo
        env = shape(i / n) if shape else math.exp(-i * k_dec)
        out[i] = hi * env * min(1.0, i / 48)
    return out


def _mix(*voices) -> list[float]:
    n = max(len(v) for v in voices)
    out = [0.0] * n
    for v in voices:
        for i, s in enumerate(v):
            out[i] += s
    return out


def _later(v: list[float], seconds: float) -> list[float]:
    return [0.0] * _n(seconds) + v


def _sin2(x: float) -> float:
    return math.sin(math.pi * x) ** 2


PENTA = (523.25, 587.33, 659.25, 783.99, 880.0)

# Steel anvil modes: inharmonic ratios, each with its own ring (ratio, level,
# decay s); the upper ones die first, like struck metal.
ANVIL = ((1.0, 1.0, 0.7), (1.004, 0.5, 0.85), (1.59, 0.45, 0.45), (2.14, 0.3, 0.32),
         (2.31, 0.2, 0.28), (2.92, 0.15, 0.2), (3.5, 0.1, 0.14))


def _strike(base: float, dur: float, *, seed: int, thud: float) -> list[float]:
    """One hammer blow: a click, a small thud and the ringing steel."""
    n = _n(dur)
    ring = [0.0] * n
    norm = 1 / sum(a for _, a, _ in ANVIL)
    att = _n(0.0008)
    for m, a, d in ANVIL:
        w, k = TAU * base * m / RATE, 1 / (d * RATE)
        for i in range(n):
            ring[i] += a * norm * math.sin(w * i) * math.exp(-i * k) * min(1.0, i / att)
    return _mix([0.6 * x for x in ring],
                [0.6 * x for x in noise(0.008, 0.0018, seed=seed, hp=0.8)],
                [thud * x for x in tone(260, 0.12, 0.03, to=140)])


# The strike was tuned by ear at the first film's landing (13.5 s), and a
# voice's noise is seeded from its cue time. Pinning that seed keeps the strike
# sample for sample the same wherever the landing moves.
ANVIL_SEED = 13517


def anvil(*, seed: int) -> list[float]:
    """A light, bright smith's hammer on the landing: a G6 blow, the hammer's
    bounce a beat later, and a C major sparkle rising out of the ring."""
    hit = _strike(1567.98, 1.9, seed=seed, thud=0.25)
    bounce = _later([0.45 * x for x in _strike(1567.98, 0.9, seed=seed + 1, thud=0.0)], 0.11)
    sparkle = _mix(*(_later([0.12 * x for x in tone(f, 0.7, 0.22, parts=((1, 1), (2, 0.2)))], t)
                     for f, t in ((2637.02, 0.2), (3135.96, 0.27), (4186.01, 0.34))))
    return _mix(hit, bounce, sparkle)


def voice(e: tl.Event) -> tuple[list[float], float]:
    """(mono samples, reverb send) for one cue."""
    k, n, s = e.kind, e.n, int(e.t * 1000) + 17
    if k == "kick":
        return tone(110, 0.35, 0.12, to=42), 0.0
    if k == "hat":
        return [0.18 * x for x in noise(0.06, 0.018, seed=s, hp=0.85)], 0.05
    if k == "pop":
        return _mix(tone(1200, 0.14, 0.035, parts=((1, 1), (2, 0.3))),
                    [0.4 * x for x in noise(0.01, 0.003, seed=s, hp=0.5)]), 0.3
    if k == "ping":
        return [0.7 * x for x in tone(1480, 1.6, 0.45, parts=((1, 1), (2.01, 0.25)))], 0.6
    if k == "hop":
        return [0.6 * x for x in tone(PENTA[n % 5], 0.2, 0.06, parts=((1, 1), (2, 0.3)))], 0.35
    if k == "lock":
        return _mix(tone(196, 0.45, 0.12, parts=((1, 1), (1.5, 0.5), (2, 0.3))),
                    [0.5 * x for x in noise(0.02, 0.006, seed=s, hp=0.4)]), 0.3
    if k == "whoosh":
        return [0.6 * x for x in noise(0.45, 1, seed=s, lp=0.25, hp=0.05, shape=_sin2)], 0.15
    if k == "impact":
        return _mix(tone(55, 0.7, 0.22, to=38),
                    [0.6 * x for x in noise(0.3, 0.06, seed=s, lp=0.15)]), 0.2
    if k == "flick":
        return [0.5 * x for x in noise(0.05, 0.012, seed=s, hp=0.6)], 0.1
    if k == "zip":
        return [0.35 * x for x in noise(0.3, 1, seed=s, hp=0.5,
                                         shape=lambda x: x * x * (1 - x) * 4)], 0.1
    if k == "cite":
        return [0.5 * x for x in tone((988, 1175, 1319)[n % 3], 0.12, 0.035,
                                      parts=((1, 1), (3, 0.15)))], 0.3
    if k == "riser":
        return [0.35 * x for x in tone(220, 0.5, 1, to=880, shape=lambda x: x * x)], 0.2
    if k == "thunk":
        return _mix(tone(98, 0.28, 0.08), [0.4 * x for x in noise(0.015, 0.004, seed=s)]), 0.1
    if k == "key":
        return _mix([0.4 * x for x in noise(0.025, 0.006, seed=s, hp=0.3)],
                    [0.25 * x for x in tone(2400, 0.02, 0.005)]), 0.05
    if k == "slide":
        return [0.5 * x for x in noise(0.35, 1, seed=s, lp=0.1, shape=_sin2)], 0.1
    if k == "wire":
        return [0.35 * x for x in tone(330, 0.42, 1, to=990, parts=((1, 1), (2, 0.2)),
                                       shape=lambda x: math.sin(math.pi * min(1, x * 0.8 + 0.1)))], 0.2
    if k == "match":
        return _mix([0.5 * x for x in tone(880, 0.8, 0.25)],
                    _later([0.5 * x for x in tone(1320, 0.8, 0.25)], 0.12)), 0.5
    if k == "purr":
        return [0.35 * x * (0.5 + 0.5 * math.sin(TAU * 32 * i / RATE))
                for i, x in enumerate(tone(140, 0.95, 1, shape=lambda x: 1 - x * x))], 0.1
    if k == "confirm":
        return [0.45 * x for x in tone(1760, 0.6, 0.2, parts=((1, 1), (1.5, 0.4)))], 0.5
    if k == "tick":
        return [0.45 * x for x in tone((1319, 1568, 1760)[n % 3], 0.12, 0.04)], 0.3
    if k == "live":
        return [0.3 * x for x in tone(659, 0.2, 0.07)], 0.3
    if k == "swell":
        return _mix([0.4 * x for x in noise(0.7, 1, seed=s, lp=0.2, shape=lambda x: x ** 3)],
                    [0.3 * x for x in tone(110, 0.7, 1, to=220, shape=lambda x: x ** 3)]), 0.3
    if k == "decode":
        return [0.2 * x for x in tone(2093 + 60 * n, 0.03, 0.008)], 0.1
    if k == "bell":
        return anvil(seed=ANVIL_SEED), 0.45
    if k == "shimmer":
        return [0.2 * x for x in tone(2093, 0.9, 1, parts=((1, 1), (1.5, 0.5)),
                                      shape=lambda x: math.sin(math.pi * x))], 0.7
    raise ValueError(f"no voice for cue kind {k!r}")


def _pad(n: int, kicks: list[float]) -> list[float]:
    """A low chord under everything, ducked by each kick; it lifts to the end
    card's chord as the end card starts."""
    a = ((55.0, 0.5), (110.0, 0.35), (164.81, 0.2), (220.0, 0.15), (329.63, 0.06))
    b = ((65.41, 0.5), (130.81, 0.35), (196.0, 0.2), (261.63, 0.15), (392.0, 0.06))
    out = [0.0] * n
    pa, pb = [0.0] * 5, [0.0] * 5
    duck = [1.0] * n
    for tk in kicks:
        i0 = _n(tk)
        for i in range(i0, min(n, i0 + _n(0.5))):
            duck[i] = min(duck[i], 1 - 0.55 * math.exp(-(i - i0) / (0.12 * RATE)))
    x0, x1 = _n(tl.DECODE_1[0] - 0.2), _n(tl.DECODE_1[0] + 0.2)
    for i in range(n):
        mix = 0.0 if i < x0 else 1.0 if i >= x1 else (i - x0) / (x1 - x0)
        s = 0.0
        if mix < 1:
            for j, (f, g) in enumerate(a):
                pa[j] += TAU * f / RATE
                s += (1 - mix) * g * math.sin(pa[j])
        if mix > 0:
            for j, (f, g) in enumerate(b):
                pb[j] += TAU * f / RATE
                s += mix * g * math.sin(pb[j])
        lfo = 0.85 + 0.15 * math.sin(TAU * 0.25 * i / RATE)
        out[i] = 0.35 * s * lfo * duck[i] * min(1.0, i / RATE)
    return out


def _reverb(x: list[float]) -> list[float]:
    """A small Schroeder reverb: four combs in parallel, two all-passes in series."""
    n = len(x)
    out = [0.0] * n
    for d, fb in ((1693, 0.78), (1759, 0.77), (1621, 0.79), (1549, 0.8)):
        buf = [0.0] * d
        k = 0
        for i in range(n):
            y = buf[k]
            buf[k] = x[i] + fb * y
            out[i] += 0.25 * y
            k = k + 1 if k + 1 < d else 0
    for d, g in ((605, 0.5), (245, 0.5)):
        buf = [0.0] * d
        k = 0
        for i in range(n):
            b = buf[k]
            v = out[i] + g * b
            out[i] = b - g * v
            buf[k] = v
            k = k + 1 if k + 1 < d else 0
    return out


def synth(events, duration: float) -> tuple[array, array]:
    """Stereo float samples for the whole film."""
    n = _n(duration)
    left, right, send = [0.0] * n, [0.0] * n, [0.0] * n
    for e in events:
        samples, wet = voice(e)
        p = (max(-1.0, min(1.0, e.pan)) + 1) * math.pi / 4
        gl, gr = math.cos(p) * e.gain, math.sin(p) * e.gain
        i0 = _n(e.t)
        for j, v in enumerate(samples):
            i = i0 + j
            if i >= n:
                break
            left[i] += gl * v
            right[i] += gr * v
            send[i] += wet * e.gain * v
    pad = _pad(n, [e.t for e in events if e.kind == "kick"])
    wet = _reverb(send)
    lag = 23   # a few samples between the sides widens the room
    f0, f1 = _n(duration - 0.45), _n(duration - 0.15)
    out_l, out_r = array("f", bytes(4 * n)), array("f", bytes(4 * n))
    for i in range(n):
        g = 1.0 if i < f0 else 0.0 if i >= f1 else 0.5 + 0.5 * math.cos(math.pi * (i - f0) / (f1 - f0))
        g *= min(1.0, i / _n(0.005))
        out_l[i] = g * (left[i] + pad[i] + 0.35 * wet[i])
        out_r[i] = g * (right[i] + pad[i] + 0.35 * (wet[i - lag] if i >= lag else 0.0))
    return out_l, out_r


def _rms(l, r) -> float:
    m = (sum(x * x for x in l) + sum(x * x for x in r)) / (len(l) + len(r))
    return 10 * math.log10(m) if m > 0 else -200.0


def levels(l, r) -> tuple[float, float]:
    """(peak dBFS, RMS dBFS) over both channels."""
    peak = max(max(abs(x) for x in l), max(abs(x) for x in r))
    return (20 * math.log10(peak) if peak > 0 else -200.0), _rms(l, r)


def master(l, r, *, rms_db: float = -11.1, peak_db: float = -1.0) -> tuple[array, array]:
    """Gain to the target RMS through a tanh soft limiter that never passes the ceiling."""
    ceil = 10 ** (peak_db / 20) * 0.999
    gain = 10 ** ((rms_db - _rms(l, r)) / 20)
    for _ in range(8):
        ol = array("f", (ceil * math.tanh(gain * x / ceil) for x in l))
        orr = array("f", (ceil * math.tanh(gain * x / ceil) for x in r))
        miss = rms_db - _rms(ol, orr)
        if abs(miss) < 0.3:
            break
        gain *= 10 ** (miss / 20)
    return ol, orr


def write_wav(path: Path, l, r) -> None:
    """16-bit stereo PCM at RATE."""
    data = array("h", bytes(4 * len(l)))
    for i, (a, b) in enumerate(zip(l, r)):
        data[2 * i] = int(max(-1.0, min(1.0, a)) * 32767)
        data[2 * i + 1] = int(max(-1.0, min(1.0, b)) * 32767)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
