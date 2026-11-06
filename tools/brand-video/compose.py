"""One frame of the film: background, the sections on screen, the dot, HUD, grain.

Each section module draws in its own 1920 x 1080 space and offers:
    draw(ctx, t, c)   everything it shows at time t
    glow(ctx, t, c)   only the orange parts that bloom, in the same space
    dot(t, c)         the dot in screen space, (x, y, diameter, alpha), or None
    over(ctx, t, c)   optional: drawn above every section, for what flies across a neighbour
Neighbouring sections overlap where one hands over to the next; the later
one owns the dot once it offers one.
"""
from __future__ import annotations

import cairo

import draw as d
import s1_research
import s2_papers
import s3_query
import s4_publish
import s5_end
import timeline as tl

SCENES = (
    (0.0, 3.2, s1_research),
    (2.95, 6.45, s2_papers),
    (5.85, 10.55, s3_query),
    (9.9, 12.55, s4_publish),
    (12.45, 15.0, s5_end),
)
SAMPLES = 6        # motion blur: sub-frames in the FAST windows
SHUTTER = 0.5      # the shutter is open for half a frame (180 degrees)
GRID_ALPHA = 0.05


def edge_fade(t: float) -> float:
    """Grid and HUD come up over the first 0.4 s and leave with the end
    card's fade, so the last frame meets the first."""
    return min(tl.ease_in_out_cubic(tl.prog(t, 0.0, 0.4)),
               1 - tl.ease_in_out_cubic(tl.prog(t, *tl.FADE_OUT)))


def _active(t: float):
    return [m for a, b, m in SCENES if a <= t <= b]


def _dot(t: float, c, active):
    for m in reversed(active):
        dot = m.dot(t, c)
        if dot:
            return dot
    return None


def _scene(ctx: cairo.Context, t: float, c) -> None:
    ctx.set_source_rgb(*d.BG)
    ctx.paint()
    d.grid(ctx, GRID_ALPHA * edge_fade(t))
    active = _active(t)

    def glows(g):
        for m in active:
            m.glow(g, t, c)

    d.soft_glow(ctx, glows, alpha=0.9)
    for m in active:
        m.draw(ctx, t, c)
    for m in active:
        if hasattr(m, "over"):
            m.over(ctx, t, c)
    dot = _dot(t, c, active)
    if dot:
        x, y, size, alpha = dot
        d.dot(ctx, x, y, d=size, alpha=alpha)
    d.vignette(ctx)


def frame(t: float, c, *, grain: bool = True) -> cairo.ImageSurface:
    """The finished frame at time t, motion-blurred inside the FAST windows.
    grain=False leaves out the film grain (the poster compresses better)."""
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, tl.W, tl.H)
    ctx = cairo.Context(surface)
    if tl.fast(t):
        sub = cairo.ImageSurface(cairo.FORMAT_RGB24, tl.W, tl.H)
        sctx = cairo.Context(sub)
        span = SHUTTER / tl.FPS
        for k in range(SAMPLES):
            _scene(sctx, t - span / 2 + span * (k + 0.5) / SAMPLES, c)
            ctx.set_source_surface(sub)
            ctx.paint_with_alpha(1 / (k + 1))   # running mean of the sub-frames
    else:
        _scene(ctx, t, c)
    d.hud(ctx, t, tl.section_at(t), alpha=edge_fade(t))
    if grain:
        d.grain(ctx, t)
    return surface
