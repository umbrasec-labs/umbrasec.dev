"""02 Papers, 3.0 - 6.0 s: three cases, three highlights, one technique.

Storyboard frame 02. Three case cards flip up out of the dot and fan out in
perspective; on each beat the dot runs a highlighter along one phrase and a
citation tag pops into the HUD; the highlights pull down into the
T1552.001 · Credentials In Files chip, which then flies off to the rule.
"""
from __future__ import annotations

import math
from functools import lru_cache

import cairo

import draw as d
import s1_research
import s3_query
import timeline as tl

W, H = tl.W, tl.H
PAGE_W, PAGE_H = d.cq(26), d.cq(30.5)
PAD_T, PAD_X = d.cq(1.7), d.cq(1.8)
INNER = PAGE_W - 2 * PAD_X
RADIUS = d.cq(0.7)
SRC_PX, SRC_TRACK = 18.0, 0.1     # storyboard .78cqw (15 px), raised to the 18 px floor
TTL_PX, Q_PX = d.cq(1.45), d.cq(1.18)
BAR_H = d.cq(0.5)
MARGIN = 4.0                      # clear border around a card bitmap, for smooth edges
SS = 2                            # card bitmaps are drawn at 2x and warped down
BARS = (((94, 72), (88, 64)), ((90,), (96, 82, 58)), ((86, 70), (92, 60)))
# left, top, transform origin, rotateY, rotateZ, opacity, fill, edge (storyboard .p1-.p3)
LAYOUT = (
    (d.cq(9.5), d.cq(9), (PAGE_W, PAGE_H / 2), 24.0, -4.0, 0.92, d.PAGE, d.LINE),
    (710.0, 144.0, (PAGE_W / 2, PAGE_H / 2), 0.0, 0.0, 1.0, d.PAGE_HI, d.LINE_HI),
    (d.cq(64.5), d.cq(9), (0.0, PAGE_H / 2), -24.0, 4.0, 0.92, d.PAGE, d.LINE),
)
ORDER = (0, 2, 1)                 # the centre card sits on top
FLIP = 0.42                       # a card's flip up takes this long from its flick
START_SCALE = 0.35                # cards start this small, on the dot
SWEEP = 0.36                      # a highlight sweeps for this long from its beat
EXIT = (5.55, 5.95)               # cards drop away under the chip
CONV = (((38.4, 62.4), (38.4, 68), (70, 66), (80, 69.6)),
        ((80, 60.8), (80, 63.7), (80, 66.7), (80, 69.6)),
        ((121.6, 62.4), (121.6, 68), (90, 66), (80, 69.6)))   # storyboard SVG, 160 x 90
U = W / 160
CHIP_C = (W / 2, d.cq(45.5))
CHIP_PX = d.cq(1.3)
CHIP_PAD = (d.cq(1.6), d.cq(0.85))
CHIP_DOT, CHIP_GAP = d.cq(0.85), d.cq(0.9)
HL_DOT = d.cq(1.1)                # the dot's size while it holds the highlighter


@lru_cache(maxsize=8)
def page_layout(i: int, src) -> dict:
    """Card i's content in card space, following the storyboard's CSS flow
    (margins collapse between blocks). Refuses content that overflows."""
    label = src.label.upper()
    lw, _ = d.measure(label, family=d.MONO, px=SRC_PX, weight=500, tracking=SRC_TRACK)
    if lw > INNER:
        raise ValueError(f"case label is wider than its card: {label!r}")
    y = PAD_T
    src_base = d.css_baseline(y, family=d.MONO, px=SRC_PX, line_height=1.25, weight=500)
    y += 1.25 * SRC_PX + d.cq(0.8)
    ttl = d.paragraph(src.title, width=INNER, family=d.DISPLAY, px=TTL_PX, weight=600,
                      line_height=1.15, tracking=-0.02)
    ttl_y = y
    y += ttl.height + d.cq(1.1)
    bars = []
    for wpc in BARS[i][0]:
        bars.append((PAD_X, y, INNER * wpc / 100))
        y += BAR_H + d.cq(0.65)
    y += d.cq(1.1) - d.cq(0.65)
    quote = src.before + src.mark + src.after
    mark = (len(src.before), len(src.before) + len(src.mark))
    q = d.paragraph(quote, width=INNER, family=d.DISPLAY, px=Q_PX, weight=500,
                    line_height=1.42, mark=mark, mark_color=d.TEXT)
    q_y = y
    y += q.height + d.cq(1.1)
    for wpc in BARS[i][1]:
        bars.append((PAD_X, y, INNER * wpc / 100))
        y += BAR_H + d.cq(0.65)
    if y > PAGE_H:
        raise ValueError(f"card {i + 1}'s content runs past the card")
    return dict(label=label, src_base=src_base, ttl=ttl, ttl_y=ttl_y, bars=tuple(bars),
                q=q, q_y=q_y, bands=d.band_rects(q, PAD_X, q_y))


def _paint_card(c: cairo.Context, i: int, src, band: float) -> None:
    """Card i in card space: fill, edge, label, title, bars, quote, highlight."""
    L = page_layout(i, src)
    fill, edge = LAYOUT[i][6], LAYOUT[i][7]
    d.round_rect(c, 0.5, 0.5, PAGE_W - 1, PAGE_H - 1, RADIUS)
    c.set_source_rgb(*fill)
    c.fill_preserve()
    c.set_source_rgb(*edge)
    c.set_line_width(1.0)
    c.stroke()
    d.text(c, L["label"], PAD_X, L["src_base"], family=d.MONO, px=SRC_PX, weight=500,
           color=d.ACCENT, tracking=SRC_TRACK)
    d.draw_paragraph(c, L["ttl"], PAD_X, L["ttl_y"], color=d.TEXT)
    for bx, by, bw in L["bars"]:
        d.round_rect(c, bx, by, bw, BAR_H, BAR_H / 2)
        c.set_source_rgb(*d.BAR)
        c.fill()
    d.draw_band(c, L["bands"], band)
    d.draw_paragraph(c, L["q"], PAD_X, L["q_y"], color=d.MUTED)


_SURFACES: dict = {}


def card_surface(i: int, src, band: float) -> cairo.ImageSurface:
    key = (i, src, round(band, 4))
    if key not in _SURFACES:
        if len(_SURFACES) > 24:
            _SURFACES.clear()
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(math.ceil((PAGE_W + 2 * MARGIN) * SS)),
                               int(math.ceil((PAGE_H + 2 * MARGIN) * SS)))
        c = cairo.Context(s)
        c.scale(SS, SS)
        c.translate(MARGIN, MARGIN)
        _paint_card(c, i, src, band)
        _SURFACES[key] = s
    return _SURFACES[key]


def _flip(t: float, i: int) -> float:
    return tl.prog(t, tl.FLICKS[i], tl.FLICKS[i] + FLIP)


def _exit(t: float) -> float:
    return tl.ease_in_cubic(tl.prog(t, *EXIT))


def pose(i: int, t: float):
    """Card i's mapping to the screen at t, its opacity, and whether it is
    settled flat (then it is drawn as vectors, not warped)."""
    left, top, origin, ry, rz, opacity = LAYOUT[i][:6]
    k = _flip(t, i)
    e = tl.ease_out_cubic(k)
    up = tl.ease_out_back(k, 1.3)
    end = (left + origin[0], top + origin[1])
    dot = s1_research.DOT
    start = (dot[0] + (origin[0] - PAGE_W / 2) * START_SCALE,
             dot[1] + (origin[1] - PAGE_H / 2) * START_SCALE)
    x = _exit(t)
    anchor = (tl.lerp(start[0], end[0], e), tl.lerp(start[1], end[1], e) + 70 * x)
    rx = 75.0 * (1 - up) + 28 * x
    f = d.card(PAGE_W, PAGE_H, anchor=anchor, origin=origin, rx=rx, ry=ry * e, rz=rz * e,
               scale=tl.lerp(START_SCALE, 1.0, e))
    alpha = opacity * tl.prog(t, tl.FLICKS[i], tl.FLICKS[i] + 0.12) * (1 - x)
    flat = ry == 0 and rz == 0 and k >= 1 and x <= 0
    return f, alpha, flat


def _band(t: float, i: int) -> float:
    a = tl.SWEEPS[i][0]
    return tl.ease_in_out_cubic(tl.prog(t, a, a + SWEEP))


def _conv(ctx, t: float, width: float, alpha: float) -> None:
    """The three lines that pull the highlights down into the chip."""
    k = tl.ease_in_out_cubic(tl.prog(t, tl.GATHER[0], tl.GATHER[1] - 0.1))
    a = alpha * (1 - _exit(t))
    if k <= 0 or a <= 0:
        return
    for curve in CONV:
        pts = [(x * U, y * U) for x, y in curve]
        n = 40
        ctx.move_to(*pts[0])
        for j in range(1, n + 1):
            ctx.line_to(*d.bezier(pts, k * j / n))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*d.ACCENT, a)
    ctx.stroke()


def chip_target(c) -> tuple[float, float]:
    """Where the chip lands: the middle of the rule's tag highlight in frame 03."""
    x, y, w, h = s3_query.layout(c)["rule"]["hl"][f"attack.{c.technique.lower()}"]
    return x + w / 2, y + h / 2


def chip_pose(t: float, c):
    """(centre x, centre y, scale, alpha) of the technique chip."""
    k = tl.prog(t, tl.T_CHIP, tl.T_CHIP + 0.32)
    if k <= 0:
        return None
    s = tl.lerp(0.6, 1.0, tl.ease_out_back(k, 2.6))
    alpha = tl.prog(t, tl.T_CHIP, tl.T_CHIP + 0.08)
    fl = tl.ease_in_out_cubic(tl.prog(t, *tl.CHIP_FLIGHT))
    to = chip_target(c)
    x = tl.lerp(CHIP_C[0], to[0], fl)
    y = tl.lerp(CHIP_C[1], to[1], fl) - 60 * math.sin(math.pi * fl)
    s *= tl.lerp(1.0, 0.55, fl)
    alpha *= 1 - tl.prog(t, tl.CHIP_FLIGHT[1] - 0.1, tl.CHIP_FLIGHT[1])
    return x, y, s, alpha


def _chip_parts(c):
    tech = f"{c.technique} "
    name = f" {c.technique_name}"
    w1, _ = d.measure(tech, family=d.MONO, px=CHIP_PX, weight=500)
    w2, _ = d.measure("·", family=d.MONO, px=CHIP_PX, weight=500)
    w3, _ = d.measure(name, family=d.MONO, px=CHIP_PX, weight=500)
    width = 2 * CHIP_PAD[0] + CHIP_DOT + CHIP_GAP + w1 + w2 + w3
    height = 2 * CHIP_PAD[1] + CHIP_PX
    return tech, name, (w1, w2, w3), width, height


def chip_dot(t: float, c):
    """Where the chip's dot sits on screen, and its size."""
    pose_ = chip_pose(t, c)
    if pose_ is None:
        return None
    x, y, s, _ = pose_
    width = _chip_parts(c)[3]
    return x + s * (-width / 2 + CHIP_PAD[0] + CHIP_DOT / 2), y, CHIP_DOT * s


def _chip(ctx, t: float, c, glow_only: bool = False) -> None:
    pose_ = chip_pose(t, c)
    if pose_ is None:
        return
    x, y, s, alpha = pose_
    if alpha <= 0:
        return
    tech, name, (w1, w2, w3), width, height = _chip_parts(c)
    fl = tl.prog(t, *tl.CHIP_FLIGHT)
    shell = alpha * (1 - tl.ease_in_cubic(fl))     # the pill dissolves in flight
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    d.round_rect(ctx, -width / 2, -height / 2, width, height, height / 2)
    if glow_only:
        ctx.set_line_width(6)
        ctx.set_source_rgba(*d.ACCENT, 0.6 * shell)
        ctx.stroke()
        ctx.restore()
        return
    ctx.set_source_rgba(*d.EMBER_BG, shell)
    ctx.fill_preserve()
    ctx.set_line_width(2)
    ctx.set_source_rgba(*d.ACCENT, shell)
    ctx.stroke()
    tx = -width / 2 + CHIP_PAD[0] + CHIP_DOT + CHIP_GAP
    base = d.css_baseline(-CHIP_PX / 2, family=d.MONO, px=CHIP_PX, line_height=1.0, weight=500)
    for part, w, col in ((tech, w1, d.TEXT), ("·", w2, d.MUTED), (name, w3, d.TEXT)):
        d.text(ctx, part, tx, base, family=d.MONO, px=CHIP_PX, weight=500, color=col,
               alpha=alpha)
        tx += w
    ctx.restore()


def _bg_glow(ctx, t: float) -> None:
    d.backlight(ctx, W / 2, 0.6 * H, 0.13 * min(tl.prog(t, 3.0, 3.4), 1 - tl.prog(t, 5.8, 6.2)))


def _quad(ctx, f) -> None:
    ctx.move_to(*f(0, 0))
    for u, v in ((PAGE_W, 0), (PAGE_W, PAGE_H), (0, PAGE_H)):
        ctx.line_to(*f(u, v))
    ctx.close_path()


def draw(ctx, t: float, c) -> None:
    if t < tl.FLICKS[0] or t > tl.CHIP_FLIGHT[1] + 0.05:
        return
    _bg_glow(ctx, t)
    _conv(ctx, t, 0.28 * U, 1.0)
    poses = {i: pose(i, t) for i in range(3)}

    def shadows(sc):
        for i in ORDER:
            f, alpha, _ = poses[i]
            if alpha > 0:
                _quad(sc, f)
                sc.fill()
    d.soft_shadow(ctx, shadows, dy=d.cq(2.2), alpha=0.5)
    for i in ORDER:
        f, alpha, flat = poses[i]
        if alpha <= 0:
            continue
        band = _band(t, i)
        if flat:
            left, top = LAYOUT[i][:2]
            ctx.save()
            ctx.translate(left, top)
            ctx.push_group()
            _paint_card(ctx, i, c.sources[i], band)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha)
            ctx.restore()
        else:
            d.warp(ctx, card_surface(i, c.sources[i], band), f, w=PAGE_W, h=PAGE_H,
                   margin=MARGIN, ss=SS, alpha=alpha)


def over(ctx, t: float, c) -> None:
    """The chip, above the rule panel it flies across."""
    if t < tl.FLICKS[0] or t > tl.CHIP_FLIGHT[1] + 0.05:
        return
    _chip(ctx, t, c)


def glow(ctx, t: float, c) -> None:
    if t < tl.FLICKS[0] or t > tl.CHIP_FLIGHT[1] + 0.05:
        return
    _conv(ctx, t, 0.28 * U * 3, 0.9)
    _chip(ctx, t, c, glow_only=True)


def _mark_point(c, i: int, t: float, p: float) -> tuple[float, float]:
    """The highlighter's leading edge on card i, on screen."""
    f = pose(i, t)[0]
    return f(*d.band_edge(page_layout(i, c.sources[i])["bands"], p))


def _between(a, b, k):
    return tl.lerp(a[0], b[0], k), tl.lerp(a[1], b[1], k)


def dot(t: float, c):
    """The dot leads each highlighter, then settles in the chip."""
    if t < tl.FLICKS[0] or t > tl.CHIP_FLIGHT[1] + 0.05:
        return None
    starts = [a for a, _ in tl.SWEEPS]
    size = tl.lerp(d.cq(1.5), HL_DOT, tl.ease_in_out_cubic(tl.prog(t, 3.0, 3.45)))
    if t < starts[0]:
        k = tl.ease_in_out_cubic(tl.prog(t, 3.02, starts[0] - 0.04))
        x, y = _between(s1_research.DOT, _mark_point(c, 0, t, 0.0), k)
        return x, y, size, 1.0
    for i, a in enumerate(starts):
        if t < a + SWEEP:
            x, y = _mark_point(c, i, t, _band(t, i))
            return x, y, size, 1.0
        nxt = starts[i + 1] if i + 1 < len(starts) else None
        if nxt is not None and t < nxt:
            k = tl.ease_in_out_cubic(tl.prog(t, a + SWEEP, nxt - 0.02))
            x, y = _between(_mark_point(c, i, t, 1.0), _mark_point(c, i + 1, t, 0.0), k)
            return x, y, size, 1.0
    if t < tl.T_CHIP:
        settled = chip_dot(tl.T_CHIP + 0.32, c)
        k = tl.ease_in_out_cubic(tl.prog(t, tl.GATHER[0], tl.T_CHIP))
        x, y = _between(_mark_point(c, 2, t, 1.0), settled[:2], k)
        return x, y, tl.lerp(size, CHIP_DOT, k), 1.0
    x, y, size = chip_dot(t, c)
    return x, y, size, 1.0
