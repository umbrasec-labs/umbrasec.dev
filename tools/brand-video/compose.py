"""One frame of the film: background, the sections on screen, the dot, HUD, grain.

Each section module draws in its own 1920 x 1080 layout space (scaled to the
output frame) and offers:
    draw(ctx, t, c)   everything it shows at time t
    glow(ctx, t, c)   only the orange parts that bloom, in the same space
    dot(t, c)         the dot in its own space, (x, y, diameter, alpha), or None
    over(ctx, t, c)   optional: drawn above every section, for what flies across a neighbour
Neighbouring sections overlap where one hands over to the next; the later
one owns the dot once it offers one.

The camera: for "Exploited now" it pans one frame width to the right and back
(timeline.pan). The rule and the KEV wall sit side by side in that wider
world, the grid behind them moves less and the dust in front moves more.
"""
from __future__ import annotations

import cairo

import draw as d
import s1_research
import s2_papers
import s3_query
import s3x_exploited
import s4_publish
import s5_end
import timeline as tl

SCENES = (
    (0.0, 3.2, s1_research),
    (2.95, 6.45, s2_papers),
    (5.85, tl.FOLD[1] + 0.05, s3_query),
    (tl.PAN_OUT[0], tl.PAN_BACK[1], s3x_exploited),
    (tl.FOLD[0] - 0.05, tl.COLLAPSE[1] + 0.05, s4_publish),
    (tl.DECODE_1[0] - 0.05, tl.DURATION, s5_end),
)
SAMPLES = 6        # motion blur: sub-frames in the FAST windows
SHUTTER = 0.5      # the shutter is open for half a frame (180 degrees)
GRID_ALPHA = 0.05
GRID_DEPTH = 0.35  # how far the grid moves with a pan, against 1 for the sections
DUST_DEPTH = 1.5   # and the dust in front of them
DUST_ALPHA = 0.16


def edge_fade(t: float) -> float:
    """Grid and HUD come up over the first 0.4 s and leave with the end
    card's fade, so the last frame meets the first."""
    return min(tl.ease_in_out_cubic(tl.prog(t, 0.0, 0.4)),
               1 - tl.ease_in_out_cubic(tl.prog(t, *tl.FADE_OUT)))


def shift(m, t: float) -> float:
    """Where the camera puts a section, in layout pixels to the right."""
    if m is s3_query:
        return -tl.pan(t) * tl.W
    if m is s3x_exploited:
        return (1 - tl.pan(t)) * tl.W
    return 0.0


def _active(t: float):
    """The sections on screen at t, each with its camera shift."""
    out = []
    for a, b, m in SCENES:
        if a <= t <= b:
            dx = shift(m, t)
            if abs(dx) < tl.W:
                out.append((m, dx))
    return out


def dot_at(t: float, c):
    """The dot in screen space, from the latest section that offers one."""
    for m, dx in reversed(_active(t)):
        dot = m.dot(t, c)
        if dot:
            return dot[0] + dx, dot[1], dot[2], dot[3]
    return None


def _scene(ctx: cairo.Context, t: float, c) -> None:
    d.scene(ctx)
    ctx.set_source_rgb(*d.BG)
    ctx.paint()
    pan = tl.pan(t) * tl.W
    d.grid(ctx, GRID_ALPHA * edge_fade(t), dx=-GRID_DEPTH * pan)
    active = _active(t)

    def glows(g):
        for m, dx in active:
            g.save()
            g.translate(dx, 0)
            m.glow(g, t, c)
            g.restore()

    d.soft_glow(ctx, glows, alpha=0.9)
    for m, dx in active:
        d.scene(ctx, dx)
        m.draw(ctx, t, c)
    for m, dx in active:
        if hasattr(m, "over"):
            d.scene(ctx, dx)
            m.over(ctx, t, c)
    d.scene(ctx)
    dot = dot_at(t, c)
    if dot:
        x, y, size, alpha = dot
        d.dot(ctx, x, y, d=size, alpha=alpha)
    d.dust(ctx, t, DUST_ALPHA * edge_fade(t), dx=-DUST_DEPTH * pan)
    d.vignette(ctx)


def frame(t: float, c, *, grain: bool = True) -> cairo.ImageSurface:
    """The finished frame at time t, motion-blurred inside the FAST windows.
    grain=False leaves out the film grain (the poster compresses better)."""
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, tl.OUT_W, tl.OUT_H)
    ctx = cairo.Context(surface)
    d.screen(ctx)
    if tl.fast(t):
        sub = cairo.ImageSurface(cairo.FORMAT_RGB24, tl.OUT_W, tl.OUT_H)
        sctx = cairo.Context(sub)
        d.screen(sctx)
        span = SHUTTER / tl.FPS
        for k in range(SAMPLES):
            _scene(sctx, t - span / 2 + span * (k + 0.5) / SAMPLES, c)
            ctx.save()
            ctx.identity_matrix()
            ctx.set_source_surface(sub)
            ctx.paint_with_alpha(1 / (k + 1))   # running mean of the sub-frames
            ctx.restore()
    else:
        _scene(ctx, t, c)
    d.hud(ctx, t, tl.section_at(t), alpha=edge_fade(t))
    if grain:
        d.grain(ctx, t)
    return surface
