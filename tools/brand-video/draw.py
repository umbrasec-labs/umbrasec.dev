"""Drawing helpers shared by every scene: palette, text, code, glow, grain, HUD.

All sizes are film pixels (1920 x 1080). The storyboard was drawn in container
units, so cq(v) turns its cqw values into pixels (1cqw = 19.2 px).
"""
from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from typing import Callable, Sequence

import fonts

os.environ["FONTCONFIG_FILE"] = str(fonts.ensure_fonts())

import cairo  # noqa: E402
import gi  # noqa: E402

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo  # noqa: E402

import timeline as tl  # noqa: E402

READ_MIN_PX = 18
DISPLAY = "Inter Tight"
MONO = "JetBrains Mono"


def rgb(hex_: str) -> tuple[float, float, float]:
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def cq(v: float) -> float:
    """Storyboard container units to film pixels."""
    return v * tl.W / 100


# site palette (assets/umbra.css)
BG = rgb("#171717")
SOFT = rgb("#222222")
RAISED = rgb("#2a2a2a")
LINE = rgb("#525252")
LINE_HI = rgb("#686c69")
TEXT = rgb("#ccd0cf")
MUTED = rgb("#959c95")
DIM = rgb("#7d837d")
ACCENT = rgb("#f25623")
EMBER = rgb("#f56e0f")
SAGE = rgb("#88a57d")
KHAKI = rgb("#aeab94")
# surfaces the storyboard uses between the palette steps
PAGE = rgb("#1f1f1f")
PAGE_HI = rgb("#232323")
BROWSER = rgb("#1b1b1b")
EMBER_BG = rgb("#2a1a14")
TILE_EDGE = rgb("#3a3a3a")
BAR = rgb("#383838")

_WEIGHTS = {400: Pango.Weight.NORMAL, 500: Pango.Weight.MEDIUM, 600: Pango.Weight.SEMIBOLD}

_FONT_OPTIONS = cairo.FontOptions()
_FONT_OPTIONS.set_antialias(cairo.ANTIALIAS_GRAY)
_FONT_OPTIONS.set_hint_style(cairo.HINT_STYLE_NONE)
_FONT_OPTIONS.set_hint_metrics(cairo.HINT_METRICS_OFF)

_SCRATCH = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8))


def _layout(ctx: cairo.Context, s: str, family: str, px: float, weight: int,
            tracking: float, fallback: bool = True) -> Pango.Layout:
    layout = PangoCairo.create_layout(ctx)
    pctx = layout.get_context()
    PangoCairo.context_set_font_options(pctx, _FONT_OPTIONS)
    pctx.set_round_glyph_positions(False)   # sub-pixel positions: smooth motion
    layout.context_changed()
    desc = Pango.FontDescription()
    desc.set_family(family)
    desc.set_weight(_WEIGHTS[weight])
    desc.set_absolute_size(px * Pango.SCALE)
    layout.set_font_description(desc)
    attrs = Pango.AttrList()
    if tracking:
        attrs.insert(Pango.attr_letter_spacing_new(int(round(tracking * px * Pango.SCALE))))
    if not fallback:
        attrs.insert(Pango.attr_fallback_new(False))
    layout.set_attributes(attrs)
    layout.set_text(s, -1)
    return layout


def _extent(layout: Pango.Layout) -> tuple[float, float, float]:
    _, logical = layout.get_extents()
    return (logical.width / Pango.SCALE, logical.height / Pango.SCALE,
            layout.get_baseline() / Pango.SCALE)


def font_families() -> set[str]:
    return {f.get_name() for f in PangoCairo.FontMap.get_default().list_families()}


def unknown_glyphs(s: str, *, family: str, px: float, weight: int = 400) -> int:
    """Glyphs the family itself lacks (font fallback switched off)."""
    return _layout(_SCRATCH, s, family, px, weight, 0.0, fallback=False).get_unknown_glyphs_count()


def measure(s: str, *, family: str, px: float, weight: int = 400,
            tracking: float = 0.0) -> tuple[float, float]:
    w, h, _ = _extent(_layout(_SCRATCH, s, family, px, weight, tracking))
    return w, h


def metrics(family: str, px: float, weight: int = 400) -> tuple[float, float]:
    """(ascent, descent) in pixels."""
    _, h, base = _extent(_layout(_SCRATCH, "Hg", family, px, weight, 0.0))
    return base, h - base


def css_baseline(top: float, *, family: str, px: float, line_height: float,
                 weight: int = 400) -> float:
    """Baseline of one CSS line box whose top edge is at `top`."""
    asc, desc = metrics(family, px, weight)
    return top + (line_height * px - (asc + desc)) / 2 + asc


def text(ctx: cairo.Context, s: str, x: float, y: float, *, family: str, px: float,
         weight: int = 400, color: Sequence[float], alpha: float = 1.0,
         tracking: float = 0.0, align: str = "left", hud: bool = False,
         halo: float = 0.0) -> tuple[float, float]:
    """Draw one line with its baseline at y; return its (width, height).

    Text meant to be read is refused below READ_MIN_PX; HUD marks, tile IDs
    and other texture pass hud=True. halo strokes a background-coloured
    outline of that width under the text, like the storyboard's text-shadow,
    so lines passing behind a label do not cut it.
    """
    if px < READ_MIN_PX and not hud:
        raise ValueError(f"{px:g} px is below the {READ_MIN_PX} px floor for text "
                         f"meant to be read: {s!r}")
    layout = _layout(ctx, s, family, px, weight, tracking)
    w, h, base = _extent(layout)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if alpha > 0:
        ctx.save()
        if halo > 0:
            ctx.move_to(x, y - base)
            PangoCairo.layout_path(ctx, layout)
            ctx.set_source_rgba(*BG, 0.85 * alpha)
            ctx.set_line_width(halo)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
        ctx.set_source_rgba(*color, alpha)
        ctx.move_to(x, y - base)
        PangoCairo.show_layout(ctx, layout)
        ctx.new_path()
        ctx.restore()
    return w, h


CODE_COLORS = {"k": KHAKI, "d": MUTED, "c": MUTED, "hl": TEXT, "plain": TEXT}


def code_line(ctx: cairo.Context, spans: Sequence[tuple[str, str]], x: float, y: float, *,
              px: float, alpha: float = 1.0, hl: float = 1.0, hud: bool = False) -> float:
    """One line of code from (kind, text) spans; returns its width.

    Kinds follow the hero reel: k keys (khaki), d dashes and c comments
    (muted), hl highlighted text (orange 16 % fill with an orange underline,
    scaled by `hl`), plain text.
    """
    cx = x
    asc, desc = metrics(MONO, px)
    for kind, s in spans:
        w, _ = measure(s, family=MONO, px=px)
        if kind == "hl" and hl > 0 and alpha > 0:
            ctx.save()
            round_rect(ctx, cx - 1, y - asc, w + 2, asc + desc, cq(0.2))
            ctx.set_source_rgba(*ACCENT, 0.16 * hl * alpha)
            ctx.fill()
            ctx.rectangle(cx - 1, y + desc - cq(0.12), w + 2, cq(0.12))
            ctx.set_source_rgba(*ACCENT, hl * alpha)
            ctx.fill()
            ctx.restore()
        text(ctx, s, cx, y, family=MONO, px=px, color=CODE_COLORS[kind], alpha=alpha, hud=hud)
        cx += w
    return cx - x


def round_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    r = max(0.0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def check(ctx: cairo.Context, x: float, y: float, size: float, color: Sequence[float],
          alpha: float = 1.0, draw: float = 1.0) -> None:
    """A tick mark in a size x size box at (x, y); `draw` animates the stroke 0..1."""
    pts = [(x + 0.08 * size, y + 0.55 * size), (x + 0.38 * size, y + 0.85 * size),
           (x + 0.94 * size, y + 0.18 * size)]
    seg = [math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])]
    left = tl.clamp01(draw) * sum(seg)
    ctx.save()
    ctx.set_line_width(max(1.5, size * 0.14))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for (ax, ay), (bx, by), d in zip(pts, pts[1:], seg):
        if left <= 0:
            break
        f = min(1.0, left / d)
        ctx.line_to(ax + (bx - ax) * f, ay + (by - ay) * f)
        left -= d
    ctx.set_source_rgba(*color, alpha)
    ctx.stroke()
    ctx.restore()


def grid(ctx: cairo.Context, alpha: float, *, cell: float = 48.0, scale: float = 1.0,
         cx: float = tl.W / 2, cy: float = tl.H / 2) -> None:
    """The umbra grid in screen space: 1 px orange lines every `cell` px.

    With scale 1 the lines sit on whole pixels, so a still grid never crawls;
    scale > 1 grows it about (cx, cy) for camera pushes.
    """
    if alpha <= 0:
        return
    ctx.save()
    ctx.identity_matrix()
    ctx.set_line_width(1.0)
    step = cell * scale
    if scale == 1.0:
        xs = [k * cell - 0.5 for k in range(1, int(tl.W / cell) + 1)]
        ys = [k * cell - 0.5 for k in range(1, int(tl.H / cell) + 1)]
    else:
        x0 = cx - math.floor(cx / step) * step
        y0 = cy - math.floor(cy / step) * step
        xs = [x0 + k * step for k in range(int(tl.W / step) + 2)]
        ys = [y0 + k * step for k in range(int(tl.H / step) + 2)]
    for x in xs:
        ctx.move_to(x, 0)
        ctx.line_to(x, tl.H)
    for y in ys:
        ctx.move_to(0, y)
        ctx.line_to(tl.W, y)
    ctx.set_source_rgba(*ACCENT, alpha)
    ctx.stroke()
    ctx.restore()


def glow(ctx: cairo.Context, x: float, y: float, r: float, color: Sequence[float],
         alpha: float) -> None:
    """A soft radial glow with a Gaussian-like falloff."""
    if alpha <= 0 or r <= 0:
        return
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    for i in range(11):
        f = i / 10
        g.add_color_stop_rgba(f, *color, alpha * math.exp(-4.0 * f * f) * (1 - f))
    ctx.save()
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def dot(ctx: cairo.Context, x: float, y: float, *, d: float = cq(1.5),
        alpha: float = 1.0, halo: float = 1.0) -> None:
    """The orange dot: core, a faint ring and its glow (storyboard .dot)."""
    if alpha <= 0 or d <= 0:
        return
    r = d / 2
    k = min(1.0, d / cq(1.5))
    glow(ctx, x, y, r + cq(2.6) * k, ACCENT, 0.6 * alpha * halo)
    ctx.save()
    ctx.arc(x, y, r + cq(0.35) * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*ACCENT, 0.2 * alpha * halo)
    ctx.fill()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*ACCENT, alpha)
    ctx.fill()
    ctx.restore()


def backlight(ctx: cairo.Context, x: float, y: float, alpha: float, *,
              rx: float = cq(50), ry: float = cq(30)) -> None:
    """The storyboard's .fx-glow: a wide, faint orange wash behind a scene."""
    if alpha <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    for j in range(9):
        f = j / 8
        g.add_color_stop_rgba(0.72 * f, *ACCENT, alpha * (1 - f) ** 2)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


def bezier(pts, u: float) -> tuple[float, float]:
    """The point at u on the cubic curve through four control points."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    m = 1 - u
    return (m ** 3 * x0 + 3 * m * m * u * x1 + 3 * m * u * u * x2 + u ** 3 * x3,
            m ** 3 * y0 + 3 * m * m * u * y1 + 3 * m * u * u * y2 + u ** 3 * y3)


def bezier_part(pts, u: float):
    """The first u of a cubic curve as a cubic of its own (de Casteljau)."""
    def mix(a, b):
        return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    p0, p1, p2, p3 = pts
    a, b, c = mix(p0, p1), mix(p1, p2), mix(p2, p3)
    ab, bc = mix(a, b), mix(b, c)
    return p0, a, ab, mix(ab, bc)


def bump(t: float, t0: float, length: float) -> float:
    """A smooth 0 -> 1 -> 0 pulse starting at t0."""
    x = tl.prog(t, t0, t0 + length)
    return math.sin(math.pi * x) if 0 < x < 1 else 0.0


def _box_blur(src: cairo.ImageSurface, r: int) -> cairo.ImageSurface:
    w, h = src.get_width(), src.get_height()
    n = 2 * r + 1
    tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(tmp)
    c.set_operator(cairo.OPERATOR_ADD)
    for d in range(-r, r + 1):
        c.set_source_surface(src, d, 0)
        c.paint_with_alpha(1 / n)
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(out)
    c.set_operator(cairo.OPERATOR_ADD)
    for d in range(-r, r + 1):
        c.set_source_surface(tmp, 0, d)
        c.paint_with_alpha(1 / n)
    return out


def soft_glow(ctx: cairo.Context, draw_fn: Callable[[cairo.Context], None], *,
              down: int = 8, alpha: float = 1.0, radius: int = 2, passes: int = 2) -> None:
    """Bloom for the orange elements.

    draw_fn draws the glowing parts in film coordinates onto a surface at
    1/down size; that is blurred and added back over the frame.
    """
    if alpha <= 0:
        return
    sw, sh = tl.W // down, tl.H // down
    small = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
    sc = cairo.Context(small)
    sc.scale(1 / down, 1 / down)
    draw_fn(sc)
    for _ in range(passes):
        small = _box_blur(small, radius)
    ctx.save()
    ctx.identity_matrix()
    ctx.scale(down, down)
    pat = cairo.SurfacePattern(small)
    pat.set_filter(cairo.FILTER_BILINEAR)
    ctx.set_source(pat)
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def vignette(ctx: cairo.Context, strength: float = 0.45) -> None:
    """The storyboard's .fx-vig: clear to 55 %, black at `strength` in the corners."""
    ctx.save()
    ctx.identity_matrix()
    ctx.translate(tl.W / 2, tl.H / 2)
    ctx.scale(tl.W / 2 * math.sqrt(2), tl.H / 2 * math.sqrt(2))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0.55, 0, 0, 0, 0)
    for i in range(1, 10):
        f = 0.55 + 0.45 * i / 9
        g.add_color_stop_rgba(f, 0, 0, 0, strength * ((f - 0.55) / 0.45) ** 1.6)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


_TILE = 256
_NOISE: list[tuple[bytearray, cairo.ImageSurface]] = []


def _noise_tiles() -> list[tuple[bytearray, cairo.ImageSurface]]:
    if not _NOISE:
        rng = random.Random(1552001)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, _TILE)
        for _ in range(8):
            data = bytearray(rng.randbytes(stride * _TILE))
            surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_A8, _TILE, _TILE, stride)
            _NOISE.append((data, surf))   # keep the buffer alive with its surface
    return _NOISE


def grain(ctx: cairo.Context, t: float, amount: float = 0.03, size: float = 1.5) -> None:
    """Film grain from pre-made noise tiles: a light and a dark pass, new each frame.

    It also dithers the glows so their gradients do not band after H.264.
    """
    if amount <= 0:
        return
    tiles = _noise_tiles()
    f = int(round(t * tl.FPS))
    rng = random.Random(f * 7919 + 17)
    ctx.save()
    ctx.identity_matrix()
    ctx.scale(size, size)
    for shade, k in ((1.0, f), (0.0, f + 3)):
        surf = tiles[k % len(tiles)][1]
        pat = cairo.SurfacePattern(surf)
        pat.set_extend(cairo.EXTEND_REPEAT)
        pat.set_filter(cairo.FILTER_BILINEAR)
        m = cairo.Matrix(x0=rng.uniform(0, _TILE), y0=rng.uniform(0, _TILE))
        pat.set_matrix(m)
        ctx.set_source_rgba(shade, shade, shade, amount)
        ctx.mask(pat)
    ctx.restore()


_SCRAMBLE_KEEP = set(" -.:/·,|'\"()[]$")
_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_LOWER = "abcdefghijklmnopqrstuvwxyz"
_DIGIT = "0123456789"


def scramble(s: str, x: float, seed: int) -> str:
    """The decode effect: the first x of the string is resolved, the rest is noise.

    Punctuation and spaces always hold, so the shape of the line reads from
    the first frame; the same seed gives the same noise.
    """
    done = int(tl.clamp01(x) * len(s) + 1e-9)
    rng = random.Random(seed)
    out = []
    for i, ch in enumerate(s):
        if i < done or ch in _SCRAMBLE_KEEP:
            out.append(ch)
        elif ch.isdigit():
            out.append(rng.choice(_DIGIT))
        elif ch.islower():
            out.append(rng.choice(_LOWER))
        else:
            out.append(rng.choice(_UPPER))
    return "".join(out)


# ---------------------------------------------------------------- HUD

HUD_PX = cq(1.05)
HUD_TRACK = 0.14


def _hud_text(ctx, s, x, y, color, alpha, align="left"):
    return text(ctx, s.upper(), x, y, family=MONO, px=HUD_PX, weight=500, color=color,
                alpha=alpha, tracking=HUD_TRACK, align=align, hud=True)


def _cites(ctx: cairo.Context, t: float, alpha: float) -> None:
    """CITED [1] [2] [3], centred in the top bar; each tag pops on its beat."""
    pad_x, pad_y, gap = cq(0.45), cq(0.3), cq(0.6)
    lw, _ = measure("CITED", family=MONO, px=HUD_PX, weight=500, tracking=HUD_TRACK)
    tw, _ = measure("[1]", family=MONO, px=HUD_PX, weight=500, tracking=HUD_TRACK)
    bw, bh = tw + 2 * pad_x, HUD_PX + 2 * pad_y
    x = tl.W / 2 - (lw + 3 * (gap + bw)) / 2
    top = cq(2.6)
    base = css_baseline(top + pad_y, family=MONO, px=HUD_PX, line_height=1.0, weight=500)
    _hud_text(ctx, "Cited", x, base, MUTED, alpha)
    x += lw + gap
    for i, tc in enumerate(tl.CITES):
        k = tl.prog(t, tc, tc + 0.2)
        if k > 0:
            e = tl.ease_out_back(k, 2.0)
            a = alpha * min(1.0, k * 4)
            cx, cy = x + bw / 2, top + bh / 2
            ctx.save()
            ctx.translate(cx, cy + tl.lerp(cq(1.2), 0.0, e))
            ctx.scale(tl.lerp(0.8, 1.0, e), tl.lerp(0.8, 1.0, e))
            ctx.translate(-cx, -cy)
            round_rect(ctx, x + 0.5, top + 0.5, bw - 1, bh - 1, cq(0.3))
            ctx.set_line_width(1.0)
            ctx.set_source_rgba(*LINE_HI, a)
            ctx.stroke()
            _hud_text(ctx, f"[{i + 1}]", x + pad_x, base, TEXT, a)
            ctx.restore()
        x += bw + gap


def hud(ctx: cairo.Context, t: float, section: tl.Section, *, alpha: float = 1.0) -> None:
    """Corner ticks, title, timecode, section label and progress bar.

    The title and section label leave for the end card; the section label
    decodes on every section change.
    """
    if alpha <= 0:
        return
    W, H = tl.W, tl.H
    ctx.save()
    ctx.identity_matrix()
    # corner ticks
    k, m = cq(1.5), cq(1.5)
    ctx.set_line_width(1.0)
    ctx.set_source_rgba(*LINE_HI, alpha)
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x = m + 0.5 if sx == 0 else W - m - 0.5
        y = m + 0.5 if sy == 0 else H - m - 0.5
        dx = k if sx == 0 else -k
        dy = k if sy == 0 else -k
        ctx.move_to(x + dx, y)
        ctx.line_to(x, y)
        ctx.line_to(x, y + dy)
    ctx.stroke()
    top = css_baseline(cq(3.0), family=MONO, px=HUD_PX, line_height=1.0, weight=500)
    bottom = css_baseline(H - cq(3.0) - HUD_PX, family=MONO, px=HUD_PX, line_height=1.0, weight=500)
    end = section.key == "end"
    leave = 1.0 - tl.ease_in_out_cubic(tl.prog(t, 12.5, 12.8)) if end else 1.0
    # title
    if leave > 0:
        _hud_text(ctx, "UMBRASEC · trace → rule", cq(3.4), top, DIM, alpha * leave)
    # papers: the citation tags pop into the top bar on their beats
    cites = min(tl.prog(t, tl.FLICKS[0], tl.FLICKS[0] + 0.3), 1 - tl.prog(t, 6.0, 6.25))
    if cites > 0:
        _cites(ctx, t, alpha * cites)
    # timecode with the orange dot
    tw, _ = _hud_text(ctx, tl.timecode(t), W - cq(3.4), top, MUTED, alpha, align="right")
    d = cq(0.62)
    ctx.arc(W - cq(3.4) - tw - cq(0.7) - d / 2, top - HUD_PX * 0.36, d / 2, 0, 2 * math.pi)
    ctx.set_source_rgba(*ACCENT, alpha)
    ctx.fill()
    # section label, decoding after each change
    if leave > 0:
        n = tl.SECTIONS.index(section) + 1
        label = scramble(section.label.upper(), tl.prog(t, section.start, section.start + 0.3),
                         int(t * tl.FPS))
        nw, _ = _hud_text(ctx, f"{n:02d}", cq(3.4), bottom, ACCENT, alpha * leave)
        _hud_text(ctx, f" · {label}", cq(3.4) + nw, bottom, MUTED, alpha * leave)
    # progress bar
    bw, bh = cq(9), cq(0.16)
    bx, by = W - cq(3.4) - bw, H - cq(3.45) - bh
    ctx.rectangle(bx, by, bw, bh)
    ctx.set_source_rgba(*LINE, alpha)
    ctx.fill()
    ctx.rectangle(bx, by, bw * tl.clamp01(t / tl.DURATION), bh)
    ctx.set_source_rgba(*ACCENT, alpha)
    ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- paragraphs

@dataclass(frozen=True)
class Para:
    """A wrapped paragraph laid out once and drawn line by line.

    lines are (Pango.LayoutLine, baseline from the top); marks are the marked
    range's boxes per line, (x, top, width, height), from the paragraph's
    top-left.
    """
    layout: object
    lines: tuple
    height: float
    marks: tuple
    px: float


def paragraph(s: str, *, width: float, family: str, px: float, weight: int = 400,
              line_height: float = 1.4, tracking: float = 0.0,
              mark: tuple[int, int] | None = None,
              mark_color: Sequence[float] | None = None) -> Para:
    """Lay out s wrapped at width, CSS-like: each line box is line_height x px
    with the text centred in it. mark is a (start, end) character range."""
    if px < READ_MIN_PX:
        raise ValueError(f"{px:g} px is below the {READ_MIN_PX} px floor: {s[:30]!r}")
    layout = _layout(_SCRATCH, s, family, px, weight, tracking)
    if mark and mark_color:
        b0, b1 = len(s[:mark[0]].encode()), len(s[:mark[1]].encode())
        attrs = layout.get_attributes() or Pango.AttrList()
        a = Pango.attr_foreground_new(*(int(v * 65535) for v in mark_color))
        a.start_index, a.end_index = b0, b1
        attrs.insert(a)
        layout.set_attributes(attrs)
    layout.set_width(int(width * Pango.SCALE))
    layout.set_wrap(Pango.WrapMode.WORD)
    asc, desc = metrics(family, px, weight)
    lh = line_height * px
    half = (lh - (asc + desc)) / 2
    lines = tuple((layout.get_line_readonly(i), i * lh + half + asc)
                  for i in range(layout.get_line_count()))
    marks = []
    if mark:
        b2c, bi = {}, 0
        for ci, ch in enumerate(s):
            b2c[bi] = ci
            bi += len(ch.encode())
        b2c[bi] = len(s)
        c2b = {v: k for k, v in b2c.items()}
        for line, base in lines:
            l0, l1 = b2c[line.start_index], b2c[line.start_index + line.length]
            o0, o1 = max(mark[0], l0), min(mark[1], l1)
            while o1 > o0 and s[o1 - 1] == " ":   # a wrap's trailing space is not marked
                o1 -= 1
            if o0 >= o1:
                continue
            x0 = line.index_to_x(c2b[o0], False) / Pango.SCALE
            x1 = line.index_to_x(c2b[o1 - 1], True) / Pango.SCALE
            marks.append((x0, base - asc, x1 - x0, asc + desc))
    return Para(layout, lines, len(lines) * lh, tuple(marks), px)


def line_widths(para: Para) -> tuple[float, ...]:
    """The width of each wrapped line."""
    return tuple(line.get_extents()[1].width / Pango.SCALE for line, _ in para.lines)


def draw_paragraph(ctx: cairo.Context, para: Para, x: float, y: float, *,
                   color: Sequence[float], alpha: float = 1.0) -> None:
    ctx.save()
    ctx.set_source_rgba(*color, alpha)
    for line, base in para.lines:
        ctx.move_to(x, y + base)
        PangoCairo.show_layout_line(ctx, line)
    ctx.new_path()
    ctx.restore()


def band_rects(para: Para, x: float, y: float) -> tuple:
    """The highlighter band per marked line, like the storyboard's mark: 58 %
    of the text box high, low in the box, padded 0.1 em each side."""
    pad = 0.1 * para.px
    out = []
    for mx, top, w, bh in para.marks:
        hb = 0.58 * bh
        out.append((x + mx - pad, y + top + (bh - hb) * 0.88, w + 2 * pad, hb))
    return tuple(out)


def draw_band(ctx: cairo.Context, rects, progress: float, *, alpha: float = 0.42) -> None:
    """The band swept to `progress` (0..1) along the marked lines in order."""
    left = tl.clamp01(progress) * sum(r[2] for r in rects)
    for bx, by, bw, bh in rects:
        if left <= 0:
            break
        ctx.rectangle(bx, by, min(bw, left), bh)
        left -= bw
    ctx.set_source_rgba(*ACCENT, alpha)
    ctx.fill()


def band_edge(rects, progress: float) -> tuple[float, float]:
    """Where the band's leading edge is at `progress`: (x, middle of the band)."""
    left = tl.clamp01(progress) * sum(r[2] for r in rects)
    for bx, by, bw, bh in rects:
        if left <= bw:
            return bx + left, by + bh / 2
        left -= bw
    bx, by, bw, bh = rects[-1]
    return bx + bw, by + bh / 2


# ---------------------------------------------------------------- perspective cards

def card(w: float, h: float, *, anchor: tuple[float, float], origin: tuple[float, float],
         rx: float = 0.0, ry: float = 0.0, rz: float = 0.0, scale: float = 1.0,
         persp: float = cq(90)) -> Callable[[float, float], tuple[float, float]]:
    """Map card space (u, v) to the screen like CSS `perspective(p) rotateY(ry)
    rotateZ(rz)` about `origin`, after a flip of rx degrees about the bottom
    edge (positive tips the top away). `anchor` is where the origin lands."""
    ox, oy = origin
    ax, ay = anchor
    cx_, sx_ = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    cy_, sy_ = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    cz_, sz_ = math.cos(math.radians(rz)), math.sin(math.radians(rz))

    def f(u: float, v: float) -> tuple[float, float]:
        x = (u - ox) * scale
        y = (h + (v - h) * cx_ - oy) * scale
        z = (v - h) * sx_ * scale
        x, y = x * cz_ - y * sz_, x * sz_ + y * cz_
        x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_
        k = persp / (persp - z)
        return ax + x * k, ay + y * k
    return f


def _affine(src, dst) -> cairo.Matrix:
    """The affine map taking triangle src onto triangle dst."""
    (x1, y1), (x2, y2), (x3, y3) = src
    det = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)

    def solve(p1, p2, p3):
        return ((p1 * (y2 - y3) + p2 * (y3 - y1) + p3 * (y1 - y2)) / det,
                (p1 * (x3 - x2) + p2 * (x1 - x3) + p3 * (x2 - x1)) / det,
                (p1 * (x2 * y3 - x3 * y2) + p2 * (x3 * y1 - x1 * y3)
                 + p3 * (x1 * y2 - x2 * y1)) / det)
    a, b, c = solve(*(p[0] for p in dst))
    e, f, g = solve(*(p[1] for p in dst))
    return cairo.Matrix(xx=a, yx=e, xy=b, yy=f, x0=c, y0=g)


def warp(ctx: cairo.Context, src: cairo.ImageSurface,
         f: Callable[[float, float], tuple[float, float]], *, w: float, h: float,
         margin: float, ss: float, cells: int = 10, alpha: float = 1.0) -> None:
    """Draw a card bitmap through the mapping f, in small triangles.

    src holds a w x h card at ss pixels per unit inside `margin` units of
    clear border; the triangles are clipped without antialiasing, so they
    meet without seams, and their aliased outer edges fall in the clear
    border while the card's own edge stays smooth.
    """
    if alpha <= 0:
        return
    us = [-margin + (w + 2 * margin) * i / cells for i in range(cells + 1)]
    vs = [-margin + (h + 2 * margin) * j / cells for j in range(cells + 1)]
    scr = [[f(u, v) for u in us] for v in vs]

    def sp(i, j):
        return (us[i] + margin) * ss, (vs[j] + margin) * ss
    pat = cairo.SurfacePattern(src)
    pat.set_filter(cairo.FILTER_BILINEAR)
    ctx.save()
    ctx.push_group()
    ctx.set_antialias(cairo.ANTIALIAS_NONE)
    for j in range(cells):
        for i in range(cells):
            for tri in (((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1))):
                s3 = [sp(a, b) for a, b in tri]
                ctx.save()
                ctx.transform(_affine(s3, [scr[b][a] for a, b in tri]))
                ctx.move_to(*s3[0])
                ctx.line_to(*s3[1])
                ctx.line_to(*s3[2])
                ctx.close_path()
                ctx.clip()
                ctx.set_source(pat)
                ctx.paint()
                ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def soft_shadow(ctx: cairo.Context, draw_fn: Callable[[cairo.Context], None], *,
                dx: float = 0.0, dy: float = 0.0, down: int = 16, alpha: float = 0.5,
                radius: int = 2, passes: int = 2) -> None:
    """A blurred drop shadow of whatever draw_fn fills (it fills with the
    current source, which is black)."""
    if alpha <= 0:
        return
    small = cairo.ImageSurface(cairo.FORMAT_ARGB32, tl.W // down + 1, tl.H // down + 1)
    sc = cairo.Context(small)
    sc.scale(1 / down, 1 / down)
    sc.translate(dx, dy)
    sc.set_source_rgba(0, 0, 0, 1)
    draw_fn(sc)
    for _ in range(passes):
        small = _box_blur(small, radius)
    ctx.save()
    ctx.identity_matrix()
    ctx.scale(down, down)
    pat = cairo.SurfacePattern(small)
    pat.set_filter(cairo.FILTER_BILINEAR)
    ctx.set_source(pat)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
