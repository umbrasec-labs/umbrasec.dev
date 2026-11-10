"""01 Research, 0.0 - 3.0 s: the dot finds one signal in the noise.

Storyboard frame 01. The dot pops on; its ping sweeps the field and each
signal decodes as the ring passes it; the dot hops the five AI coding agent
CVEs, one per half beat, drawing the loop behind it; brackets lock on the
group; the camera dives through the dot into the papers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cairo

import draw as d
import timeline as tl

W, H = tl.W, tl.H
DOT = (0.50 * W, 0.44 * H)
# Storyboard positions, % of the frame, in Content.signals and
# Content.agent_cves order. The agents' order is also the hop order.
SIGNAL_AT = ((12, 22), (15, 70), (78, 15), (88, 34), (31, 84), (83, 64), (64, 80))
AGENT_AT = ((40, 33), (57, 26), (64, 46), (52, 60), (36, 53))
LINKS = (("s0", "a0"), ("s2", "a1"), ("s2", "s3"), ("s3", "a2"), ("s5", "a2"),
         ("s6", "a3"), ("s4", "a3"), ("s4", "a4"), ("s1", "a4"), ("s1", "s0"))
LOCK = (0.33 * W, 0.20 * H, 0.44 * W, 0.46 * H)
LOCK_LABEL = "Lock · hijacked AI coding agents"
U = W / 160                       # one unit of the storyboard's 160 x 90 SVG
LABEL_PX = d.cq(1.08)
NODE_D = d.cq(0.6)
RING_MIN, RING_MAX = d.cq(0.75), 820.0
TRAVEL = 0.18                     # a hop lands on its half beat after this long
BACK = (tl.HOPS[-1] + 0.05, tl.T_LOCK)   # last leg, back to the centre
CLOSE = (tl.HOPS[-1] + 0.03, tl.HOPS[-1] + 0.23)  # the loop closes
FADE = (3.0, 3.2)
LABEL_IN = (tl.HOPS[-1], tl.HOPS[-1] + 0.15)  # the lock label decodes as the loop closes,
                                      # so it reads for 0.6 s before the dive


@dataclass(frozen=True)
class Node:
    key: str
    label: str
    x: float
    y: float
    agent: bool
    reveal: float


def _pt(p: tuple[float, float]) -> tuple[float, float]:
    return p[0] / 100 * W, p[1] / 100 * H


def ring_radius(t: float) -> float:
    return tl.lerp(RING_MIN, RING_MAX, tl.ease_out_cubic(tl.prog(t, tl.T_PING, tl.PING_END)))


def reveal_time(x: float, y: float) -> float:
    """When the ping's ring reaches a point (inverse of ring_radius)."""
    f = tl.clamp01((math.dist((x, y), DOT) - RING_MIN) / (RING_MAX - RING_MIN))
    return tl.T_PING + (1 - (1 - f) ** (1 / 3)) * (tl.PING_END - tl.T_PING)


def nodes(c) -> dict[str, Node]:
    if len(c.signals) != len(SIGNAL_AT) or len(c.agent_cves) != len(AGENT_AT):
        raise ValueError("the research field needs a position for every signal")
    out = {}
    for prefix, labels, places, agent in (("s", c.signals, SIGNAL_AT, False),
                                          ("a", c.agent_cves, AGENT_AT, True)):
        for i, (label, at) in enumerate(zip(labels, places)):
            x, y = _pt(at)
            out[f"{prefix}{i}"] = Node(f"{prefix}{i}", label, x, y, agent, reveal_time(x, y))
    return out


def _legs():
    pts = [DOT] + [_pt(p) for p in AGENT_AT] + [DOT]
    spans = [(h - TRAVEL, h) for h in tl.HOPS] + [BACK]
    return pts, spans


def dot_path(t: float) -> tuple[float, float]:
    """Where the dot is in this section's space: centre, five hops, centre."""
    pts, spans = _legs()
    pos = pts[0]
    for i, (a, b) in enumerate(spans):
        if t < a:
            break
        x = tl.ease_in_out_cubic(tl.prog(t, a, b))
        pos = (tl.lerp(pts[i][0], pts[i + 1][0], x), tl.lerp(pts[i][1], pts[i + 1][1], x))
        if t < b:
            break
    return pos


def scale(t: float) -> float:
    """Camera zoom about the dot: a slow push-in, then the dive."""
    drift = 1 + 0.02 * tl.prog(t, 0.0, tl.DIVE[0])
    dive = tl.ease_in_cubic(tl.prog(t, *tl.DIVE))
    return drift * (1 + 2.4 * dive)


def _camera(ctx, t):
    s = scale(t)
    ctx.translate(*DOT)
    ctx.scale(s, s)
    ctx.translate(-DOT[0], -DOT[1])


def _alpha(t: float) -> float:
    return 1 - tl.ease_in_out_cubic(tl.prog(t, *FADE))


def _on(t: float, i: int) -> float:
    """0 -> 1 as the dot lands on agent i."""
    return tl.ease_out_cubic(tl.prog(t, tl.HOPS[i] - 0.03, tl.HOPS[i] + 0.06))


def _hot_segments(t: float):
    """The orange loop: (from, to, drawn 0..1) for each of its five sides."""
    pts, spans = _legs()
    agents = pts[1:-1]
    segs = []
    for i in range(1, 5):
        a, b = spans[i]
        segs.append((agents[i - 1], agents[i], tl.ease_in_out_cubic(tl.prog(t, a, b))))
    segs.append((agents[4], agents[0], tl.ease_in_out_cubic(tl.prog(t, *CLOSE))))
    return segs


def _stroke_part(ctx, p, q, f):
    if f <= 0:
        return False
    ctx.move_to(*p)
    ctx.line_to(tl.lerp(p[0], q[0], f), tl.lerp(p[1], q[1], f))
    return True


def _brackets(ctx, t, a, width):
    k = tl.prog(t, tl.T_LOCK, tl.T_LOCK + 0.22)
    if k <= 0:
        return
    x, y, w, h = LOCK
    s = tl.lerp(1.16, 1.0, tl.ease_out_back(k, 2.2))
    cx, cy = x + w / 2, y + h / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.translate(-cx, -cy)
    arm = d.cq(2.4)
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        px = x + w * sx
        py = y + h * sy
        dx = arm if sx == 0 else -arm
        dy = arm if sy == 0 else -arm
        ctx.move_to(px + dx, py)
        ctx.line_to(px, py)
        ctx.line_to(px, py + dy)
    ctx.restore()
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_SQUARE)  # like CSS borders
    ctx.set_source_rgba(*d.ACCENT, a * tl.prog(t, tl.T_LOCK, tl.T_LOCK + 0.06))
    ctx.stroke()


def draw(ctx, t: float, c) -> None:
    a = _alpha(t)
    if a <= 0:
        return
    frame = int(t * tl.TICK + 1e-6)
    ns = nodes(c)
    ctx.save()
    _camera(ctx, t)

    # the ambient glow comes up with the ping
    g = 0.13 * a * tl.ease_in_out_cubic(tl.prog(t, tl.T_PING - 0.05, tl.T_PING + 0.5))
    if g > 0:
        ctx.save()
        ctx.translate(*DOT)
        ctx.scale(d.cq(50), d.cq(30))
        grad = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        for i in range(9):
            f = i / 8
            grad.add_color_stop_rgba(0.72 * f, *d.ACCENT, g * (1 - f) ** 2)
        ctx.set_source(grad)
        ctx.paint()
        ctx.restore()

    # faint links, drawn out from whichever end the ring reached first
    ctx.set_line_width(0.16 * U)
    for k1, k2 in LINKS:
        n1, n2 = sorted((ns[k1], ns[k2]), key=lambda n: n.reveal)
        f = tl.ease_out_cubic(tl.prog(t, n2.reveal, n2.reveal + 0.3))
        if _stroke_part(ctx, (n1.x, n1.y), (n2.x, n2.y), f):
            ctx.set_source_rgba(*d.MUTED, 0.22 * a)
            ctx.stroke()

    # dashed spokes from the centre to each agent as the dot lands on it
    ctx.save()
    ctx.set_dash([0.8 * U, 0.8 * U])
    for i in range(5):
        n = ns[f"a{i}"]
        f = tl.ease_out_cubic(tl.prog(t, tl.HOPS[i], tl.HOPS[i] + 0.16))
        if _stroke_part(ctx, DOT, (n.x, n.y), f):
            ctx.set_source_rgba(*d.ACCENT, 0.38 * a)
            ctx.stroke()
    ctx.restore()

    # the loop the hops draw
    ctx.set_line_width(0.32 * U)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    drew = False
    for p, q, f in _hot_segments(t):
        drew = _stroke_part(ctx, p, q, f) or drew
    if drew:
        ctx.set_source_rgba(*d.ACCENT, a)
        ctx.stroke()

    # the ping's rings: the reveal sweep, a softer echo, and a short one at the lock
    for t0, t1, rmax, alpha in ((tl.T_PING, tl.PING_END, RING_MAX, 0.95),
                                (tl.T_PING + 0.12, tl.PING_END, RING_MAX * 0.62, 0.6),
                                (tl.T_LOCK, tl.T_LOCK + 0.45, d.cq(14), 0.8)):
        x = tl.prog(t, t0, t1)
        if 0 < x < 1:
            r = tl.lerp(RING_MIN, rmax, tl.ease_out_cubic(x))
            ctx.arc(DOT[0], DOT[1], r, 0, 2 * math.pi)
            ctx.set_line_width(1.5)
            ctx.set_source_rgba(*d.ACCENT, 0.85 * alpha * a * (1 - x) ** 1.3)
            ctx.stroke()

    # nodes and their labels, decoding as the ring passes
    for i, n in enumerate(ns.values()):
        shown = tl.ease_out_cubic(tl.prog(t, n.reveal, n.reveal + 0.12))
        if shown <= 0:
            continue
        on = _on(t, int(n.key[1])) if n.agent else 0.0
        pop = 1 + (0.9 * (1 - tl.prog(t, tl.HOPS[int(n.key[1])], tl.HOPS[int(n.key[1])] + 0.3)) ** 3
                   if n.agent and t >= tl.HOPS[int(n.key[1])] else 0.0)
        r = NODE_D / 2 * pop * tl.lerp(0.4, 1.0, shown)
        if on > 0:
            d.glow(ctx, n.x, n.y, d.cq(1.6), d.ACCENT, 0.7 * on * a)
        col = tuple(tl.lerp(p, q, on) for p, q in zip(d.DIM, d.ACCENT))
        ctx.arc(n.x, n.y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, a * shown)
        ctx.fill()
        label = d.scramble(n.label, tl.prog(t, n.reveal, n.reveal + 0.4), frame * 31 + i * 7)
        lcol = tuple(tl.lerp(p, q, on) for p, q in zip(d.DIM, d.TEXT))
        base = d.css_baseline(n.y - LABEL_PX / 2, family=d.MONO, px=LABEL_PX, line_height=1.0,
                              weight=500)
        d.text(ctx, label, n.x + d.cq(0.3) + d.cq(0.75), base, family=d.MONO, px=LABEL_PX,
               weight=500, color=lcol, alpha=a * shown, tracking=0.03, halo=d.cq(0.5))

    # the lock
    _brackets(ctx, t, a, 2.0)
    k = tl.prog(t, LABEL_IN[0], LABEL_IN[0] + 0.06)
    if k > 0:
        px = d.cq(0.95)
        base = d.css_baseline(LOCK[1] - d.cq(2.4), family=d.MONO, px=px, line_height=1.0, weight=500)
        d.text(ctx, d.scramble(LOCK_LABEL, tl.prog(t, *LABEL_IN), frame * 13),
               LOCK[0], base, family=d.MONO, px=px, weight=500, color=d.ACCENT,
               alpha=a * k, tracking=0.14)
    ctx.restore()


def glow(ctx, t: float, c) -> None:
    """The parts that bloom: the loop, the lit agent dots and the brackets."""
    a = _alpha(t)
    if a <= 0:
        return
    ns = nodes(c)
    ctx.save()
    _camera(ctx, t)
    ctx.set_line_width(0.32 * U * 2.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    drew = False
    for p, q, f in _hot_segments(t):
        drew = _stroke_part(ctx, p, q, f) or drew
    if drew:
        ctx.set_source_rgba(*d.ACCENT, 0.9 * a)
        ctx.stroke()
    for i in range(5):
        on = _on(t, i)
        if on > 0:
            n = ns[f"a{i}"]
            ctx.arc(n.x, n.y, NODE_D, 0, 2 * math.pi)
            ctx.set_source_rgba(*d.ACCENT, on * a)
            ctx.fill()
    _brackets(ctx, t, a, 5.0)
    ctx.restore()


def dot(t: float, c):
    """The dot in screen space: (x, y, diameter, alpha)."""
    if t > FADE[1]:
        return None
    px, py = dot_path(t)
    s = scale(t)
    x, y = DOT[0] + s * (px - DOT[0]), DOT[1] + s * (py - DOT[1])
    size = d.cq(1.5) * tl.spring(tl.prog(t, tl.T_POP, tl.T_POP + 0.4))
    size *= 1 + 0.3 * d.bump(t, tl.T_PING, 0.24) + 0.3 * d.bump(t, tl.T_LOCK, 0.24)
    return x, y, size, 1.0
