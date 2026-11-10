"""06 End card, 19.0 - 22.0 s: the dot becomes the full stop.

Storyboard frame 05. "Trace the technique." and "Forge the rule" decode in
the site's own type; the dot rises out of the frame, falls back and lands as
the full stop with a ripple and a flare, the letters dipping in a wave that
runs back from it; the lockup fades up over a line that draws in; a light
crosses the title; everything fades to charcoal so the loop restarts on the
dot popping on.
"""
from __future__ import annotations

import math
from functools import lru_cache

import cairo

import draw as d
import timeline as tl

W, H = tl.W, tl.H
L1, L2 = "Trace the technique.", "Forge the rule"
LINE_PX, LINE_LH, LINE_TRACK = d.cq(7.2), 0.94, -0.045
STOP_D, STOP_GAP = d.cq(1.02), d.cq(0.3)
LOCK_TOP, BADGE, LOCK_GAP = d.cq(3.6), d.cq(3.1), d.cq(1.2)
WORD_PX, URL_PX, SEP_H = d.cq(2), d.cq(1.1), d.cq(2.2)
LIFT = d.cq(1.2)                       # the block sits this far above centre
DROP = d.cq(30)                        # the dot falls from this far above the stop
BOUNCE = (tl.T_LAND, tl.T_LAND + 0.5)  # a small hop after landing, d.cq(1.6) high
DIP, DIP_STEP, DIP_LEN = d.cq(0.55), 0.035, 0.3
RIPPLE = (tl.T_LAND, tl.T_LAND + 1.0)


def _w(s: str, px: float, weight: int, tracking: float, family: str = d.DISPLAY) -> float:
    return d.measure(s, family=family, px=px, weight=weight, tracking=tracking)[0]


@lru_cache(maxsize=1)
def layout() -> dict:
    w1 = _w(L1, LINE_PX, 600, LINE_TRACK)
    w2 = _w(L2, LINE_PX, 600, LINE_TRACK)
    word_w = _w("UMBRASEC", WORD_PX, 600, -0.01)
    url_w = _w("umbrasec.dev", URL_PX, 400, 0.06, d.MONO)
    lock_w = BADGE + LOCK_GAP + word_w + LOCK_GAP + 1 + LOCK_GAP + url_w
    width = max(w1, w2 + STOP_GAP + STOP_D, lock_w)
    lh = LINE_LH * LINE_PX
    height = 2 * lh + LOCK_TOP + BADGE
    left = (W - width) / 2
    top = (H - height) / 2 - LIFT
    b1 = d.css_baseline(top, family=d.DISPLAY, px=LINE_PX, line_height=LINE_LH, weight=600)
    b2 = b1 + lh
    lock_top = top + 2 * lh + LOCK_TOP
    stop = (left + w2 + STOP_GAP + STOP_D / 2, b2 - STOP_D / 2, STOP_D)
    # each letter's x, for the dip that runs back from the stop
    xs = [left + x for x in d.char_xs(L2, family=d.DISPLAY, px=LINE_PX, weight=600,
                                      tracking=LINE_TRACK)]
    return dict(left=left, top=top, b1=b1, b2=b2, l2_right=left + w2, l2_base=b2, stop=stop,
                xs=xs, lock_top=lock_top, word_w=word_w, url_w=url_w, lock_w=lock_w,
                w1=w1, lh=lh)


def _fade(t: float) -> float:
    return 1 - tl.ease_in_out_cubic(tl.prog(t, *tl.FADE_OUT))


def _decode(t: float, s: str, window, seed: int) -> tuple[str, float]:
    tf = int(t * tl.TICK + 1e-6) / tl.TICK   # one string per tick, so motion blur cannot ghost it
    return d.scramble(s, tl.prog(tf, *window), seed), tl.prog(t, window[0], window[0] + 0.12)


def _badge(ctx, x: float, y: float, size: float, alpha: float) -> None:
    """The U badge from assets/favicon-v2.svg, size x size at (x, y)."""
    k = size / 32
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(k, k)
    g = cairo.LinearGradient(0, 0, 32, 32)
    g.add_color_stop_rgba(0, *d.ACCENT, alpha)
    g.add_color_stop_rgba(1, *d.EMBER, alpha)
    d.round_rect(ctx, 0, 0, 32, 32, 7)
    ctx.set_source(g)
    ctx.fill()
    ctx.move_to(10.5, 9.5)
    ctx.line_to(10.5, 15.5)
    ctx.arc_negative(16, 15.5, 5.5, math.pi, 0)
    ctx.line_to(21.5, 9.5)
    ctx.set_line_width(3.4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*d.BG, alpha)
    ctx.stroke()
    ctx.restore()


def draw(ctx, t: float, c) -> None:
    if t < tl.DECODE_1[0]:
        return
    L = layout()
    fade = _fade(t)
    if fade <= 0:
        return
    d.backlight(ctx, 0.5 * W, 0.48 * H, 0.13 * tl.prog(t, *tl.DECODE_1) * fade)
    tick = int(t * tl.TICK + 1e-6)
    s1, a1 = _decode(t, L1, tl.DECODE_1, tick)
    d.text(ctx, s1, L["left"], L["b1"], family=d.DISPLAY, px=LINE_PX, weight=600,
           color=d.TEXT, alpha=a1 * fade, tracking=LINE_TRACK)
    s2, a2 = _decode(t, L2, tl.DECODE_2, tick + 7)
    if s2 == L2:   # resolved: letters dip one by one, running back from the stop
        n = len(L2)
        for i, ch in enumerate(L2):
            t0 = tl.T_LAND + (n - 1 - i) * DIP_STEP
            dy = DIP * d.bump(t, t0, DIP_LEN)
            d.text(ctx, ch, L["xs"][i], L["b2"] + dy, family=d.DISPLAY, px=LINE_PX,
                   weight=600, color=d.ACCENT, alpha=a2 * fade, tracking=LINE_TRACK)
    else:
        d.text(ctx, s2, L["left"], L["b2"], family=d.DISPLAY, px=LINE_PX, weight=600,
               color=d.ACCENT, alpha=a2 * fade, tracking=LINE_TRACK)
    # a light crosses both lines once the lockup is in
    def lit(g):
        d.text(g, L1, L["left"], L["b1"], family=d.DISPLAY, px=LINE_PX, weight=600,
               color=(1.0, 1.0, 1.0), alpha=0.7 * fade, tracking=LINE_TRACK)
        d.text(g, L2, L["left"], L["b2"], family=d.DISPLAY, px=LINE_PX, weight=600,
               color=(1.0, 0.82, 0.62), alpha=0.75 * fade, tracking=LINE_TRACK)
    d.light_sweep(ctx, tl.ease_in_out_cubic(tl.prog(t, *tl.SWEEP)),
                  (L["left"] - d.cq(1), L["top"] - d.cq(1),
                   max(L["w1"], L["l2_right"] - L["left"]) + d.cq(3), 2 * L["lh"] + d.cq(3)),
                  lit, width=d.cq(11))
    # the ripple from the landing
    k = tl.prog(t, *RIPPLE)
    if 0 < k < 1:
        x, y, _ = L["stop"]
        e = tl.ease_out_cubic(k)
        ctx.arc(x, y, tl.lerp(d.cq(0.5), d.cq(4.5), e), 0, 2 * math.pi)
        ctx.set_line_width(1.0)
        ctx.set_source_rgba(*d.ACCENT, 0.9 * (1 - k) * fade)
        ctx.stroke()
        # and its flare: a hairline through the stop that opens and dies
        d.streak(ctx, x, y, d.cq(30) * tl.ease_out_cubic(tl.prog(k, 0, 0.45)),
                 0.85 * (1 - tl.prog(k, 0, 0.45)) ** 2 * fade, width=1.5)
    # the lockup
    lk = tl.ease_out_cubic(tl.prog(t, *tl.LOCKUP_IN))
    if lk > 0:
        a = lk * fade
        y0 = L["lock_top"] + (1 - lk) * d.cq(1)
        x = L["left"]
        _badge(ctx, x, y0, BADGE, a)
        x += BADGE + LOCK_GAP
        mid = y0 + BADGE / 2
        base = d.css_baseline(mid - WORD_PX / 2, family=d.DISPLAY, px=WORD_PX, line_height=1.0,
                              weight=600)
        d.text(ctx, "UMBRASEC", x, base, family=d.DISPLAY, px=WORD_PX, weight=600,
               color=d.TEXT, alpha=a, tracking=-0.01)
        x += L["word_w"] + LOCK_GAP
        ctx.rectangle(round(x), mid - SEP_H / 2, 1, SEP_H)
        ctx.set_source_rgba(*d.LINE, a)
        ctx.fill()
        x += 1 + LOCK_GAP
        base = d.css_baseline(mid - URL_PX / 2, family=d.MONO, px=URL_PX, line_height=1.0)
        d.text(ctx, "umbrasec.dev", x, base, family=d.MONO, px=URL_PX, color=d.MUTED, alpha=a,
               tracking=0.06)
        # a hairline under the lockup draws in from the badge
        u = tl.ease_out_cubic(tl.prog(t, tl.LOCKUP_IN[0], tl.LOCKUP_IN[1] + 0.4))
        ctx.rectangle(L["left"], round(y0 + BADGE + d.cq(1.0)), L["lock_w"] * u, 1)
        ctx.set_source_rgba(*d.ACCENT, 0.55 * a)
        ctx.fill()


def glow(ctx, t: float, c) -> None:
    """The second line's orange blooms once it resolves; the landing throws a flare."""
    if t < tl.DECODE_2[1]:
        return
    L = layout()
    a = 0.35 * _fade(t)
    if a > 0:
        d.text(ctx, L2, L["left"], L["b2"], family=d.DISPLAY, px=LINE_PX, weight=600,
               color=d.ACCENT, alpha=a, tracking=LINE_TRACK)
    k = tl.prog(t, tl.T_LAND, tl.T_LAND + 0.45)
    if 0 < k < 1:
        x, y, _ = L["stop"]
        d.streak(ctx, x, y, d.cq(34) * tl.ease_out_cubic(k), (1 - k) ** 2, width=6)


def dot(t: float, c):
    """From the centre the dot rises out of the frame, falls back as the full
    stop, hops once and settles; it fades with the card."""
    if t < tl.DOT_UP[0]:
        return None
    x, y, size = layout()["stop"]
    sx, sy = W / 2, H / 2
    if t < tl.DOT_FALL[0]:
        k = tl.ease_in_cubic(tl.prog(t, *tl.DOT_UP))
        return sx, tl.lerp(sy, -d.cq(4), k), d.cq(1.5), 1.0
    if t < tl.T_LAND:
        k = tl.ease_in_cubic(tl.prog(t, *tl.DOT_FALL))
        return x, tl.lerp(y - DROP, y, k), tl.lerp(d.cq(1.5), size, k), 1.0
    k = tl.prog(t, *BOUNCE)
    hop = d.cq(1.6) * math.sin(math.pi * k) if k < 1 else 0.0
    return x, y - hop, size, _fade(t)
