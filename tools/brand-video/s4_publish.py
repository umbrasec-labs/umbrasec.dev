"""04 Publish, 10.0 - 12.5 s: the rule folds into its tile and the write-up goes live.

Storyboard frame 04. The rule panel folds into the T1552.001 tile, which flies
into its slot in the 29-tile sigma-pack grid; three ticks land for the places a
rule change reaches; the camera pulls back to the live article; then the whole
page collapses into the orange dot.
"""
from __future__ import annotations

import math
from functools import lru_cache

import draw as d
import s3_query
import timeline as tl

W, H = tl.W, tl.H
TXT_PX, TRACK = 18.0, 0.14            # storyboard .8-.9cqw labels, raised to the 18 px floor
BROWSER_BOX = (round(d.cq(4.5)), round(d.cq(10.5)), round(d.cq(53)))   # left, top, width
BAR_H = round(d.cq(2.6))
BODY_PAD = (d.cq(2), d.cq(2.4), d.cq(2.2))   # top, sides, bottom
GAP = d.cq(0.9)
TITLE_PX, TITLE_MAX = d.cq(2.45), d.cq(42)
MINI_PX, MINI_LH, MINI_PAD = 18.0, 1.55, (d.cq(0.9), d.cq(1.1))
LIVE_DOT = d.cq(0.7)
PACK_BOX = (round(d.cq(61.5)), round(d.cq(10.5)), round(d.cq(34)))
TILE_H, TILE_GAP, TILE_PX = d.cq(2.7), d.cq(0.45), d.cq(0.7)   # tile IDs are texture (hud)
DEST_TOP, DEST_GAP, DEST_NAME = d.cq(1.7), d.cq(0.75), d.cq(9.5)
DESTS = (("umbrasec.dev", "write-up and pack"), ("umbra-blue", "skills synced"),
         ("detections", "claims relocked"))
SQUASH = (tl.FOLD[0], 10.2)           # the panel folds down to a strip
FLY = (10.2, tl.T_TILE)               # the strip flies into its slot as the tile
DOT_REST = d.cq(0.6)
DOT_END = d.cq(1.5)


def _w(s: str, px: float = TXT_PX, weight: int = 400, tracking: float = 0.0,
       family: str = d.MONO) -> float:
    return d.measure(s, family=family, px=px, weight=weight, tracking=tracking)[0]


def mini_lines(c) -> tuple[str, ...]:
    """The rule's credential selection and level, with every cut marked."""
    rule = list(c.rule_lines)
    i = rule.index("  risk_credential:")
    j = next(k for k in range(i, len(rule)) if "'.aws/credentials'" in rule[k])
    out = rule[i:j + 1]
    if j + 1 < len(rule) and rule[j + 1].strip() == "...":
        out.append(rule[j + 1])
    level = rule.index(next(ln for ln in rule if ln.startswith("level:")))
    if level != rule.index(out[-1]) + 1:
        out.append("  ...")
    out.append(rule[level])
    return tuple(out)


@lru_cache(maxsize=4)
def layout(c) -> dict:
    left, top, width = BROWSER_BOX
    inner_l, inner = left + 1 + BODY_PAD[1], width - 2 - 2 * BODY_PAD[1]
    y = top + 1 + BAR_H + 1 + BODY_PAD[0]
    eyebrow = c.article_eyebrow.upper()
    eyebrow_base = d.css_baseline(y, family=d.MONO, px=TXT_PX, line_height=1.0, weight=500)
    y += TXT_PX + GAP
    title = d.paragraph(c.article_title, width=min(TITLE_MAX, inner), family=d.DISPLAY,
                        px=TITLE_PX, weight=600, line_height=1.06, tracking=-0.035)
    title_top = y
    y += title.height + GAP
    bars = []
    for pc in (92, 84, 61):
        bars.append((inner_l, y, inner * pc / 100))
        y += d.cq(0.5) + GAP
    y += d.cq(0.3)
    lines = mini_lines(c)
    mini_top = y
    mlh = MINI_LH * MINI_PX
    mini_h = 2 + 2 * MINI_PAD[0] + len(lines) * mlh
    rows = []
    for i, ln in enumerate(lines):
        sp = s3_query.spans(ln, ("'.aws/credentials'",))
        rows.append((sp, d.css_baseline(mini_top + 1 + MINI_PAD[0] + i * mlh, family=d.MONO,
                                        px=MINI_PX, line_height=MINI_LH), _w(ln, MINI_PX)))
    y += mini_h + GAP
    live_base = d.css_baseline(y, family=d.MONO, px=TXT_PX, line_height=1.0, weight=500)
    live_mid = y + TXT_PX / 2
    height = round(y + TXT_PX + BODY_PAD[2] + 1 - top)
    url = c.article_url
    browser = dict(
        left=left, top=top, width=width, height=height, bottom=top + height, inner_l=inner_l,
        inner=inner, eyebrow=eyebrow, eyebrow_base=eyebrow_base, title=title,
        title_top=title_top, bars=bars, mini_top=mini_top, mini_h=mini_h, rows=rows,
        live_base=live_base, live_mid=live_mid, url=url,
        url_base=d.css_baseline(top + 1 + (BAR_H - TXT_PX) / 2, family=d.MONO, px=TXT_PX,
                                line_height=1.0),
        widths=[_w(eyebrow, weight=500, tracking=TRACK), *d.line_widths(title),
                *(r[2] + 2 * MINI_PAD[1] + 2 for r in rows),
                # the address bar: its dots, gaps and URL must fit the window
                2 * d.cq(1.2) + 3 * d.cq(0.65) + 2 * d.cq(0.55) + d.cq(1.2) + _w(url)
                - (width - 2) + inner])

    pl, pt, pw = PACK_BOX
    head = ("sigma-pack", f" · {c.pack_sigma + c.pack_kql} files · {c.pack_sigma} Sigma"
                          f" · {c.pack_kql} KQL")
    head_base = d.css_baseline(pt, family=d.MONO, px=TXT_PX, line_height=1.0, weight=500)
    ty = pt + TXT_PX + d.cq(1)
    tw = (pw - 5 * TILE_GAP) / 6
    tiles = []
    for i, tech in enumerate(c.tiles):
        r, col = divmod(i, 6)
        tiles.append((tech, (pl + col * (tw + TILE_GAP), ty + r * (TILE_H + TILE_GAP), tw, TILE_H)))
    rows_n = math.ceil(len(c.tiles) / 6)
    dy = ty + rows_n * TILE_H + (rows_n - 1) * TILE_GAP + DEST_TOP
    dest = []
    lh = 1.2 * TXT_PX
    for i, (name, what) in enumerate(DESTS):
        dest.append((name, what, d.css_baseline(dy + i * (lh + DEST_GAP), family=d.MONO,
                                                px=TXT_PX, line_height=1.2)))
    tick = d.cq(0.9)
    pack = dict(
        left=pl, top=pt, width=pw, head=head, head_base=head_base, tiles=tiles,
        lit=c.tiles.index(c.technique), dest=dest, tick=tick,
        bottom=dy + 3 * lh + 2 * DEST_GAP,
        widths=[_w(head[0].upper(), weight=500, tracking=TRACK)
                + _w(head[1].upper(), weight=500, tracking=TRACK),
                *(tick + d.cq(0.8) + max(DEST_NAME, _w(n, weight=500)) + d.cq(0.8) + _w(w)
                  for n, w, _ in dest),
                *(_w(t, TILE_PX) + 4 for t, _ in tiles)])
    return dict(browser=browser, pack=pack)


# ---------------------------------------------------------------- motion

def _fold_rect(t: float, c):
    """The rule panel's box as it folds into the tile: (x, y, w, h, k), k from 0 to 1."""
    R = s3_query.layout(c)["rule"]
    P = layout(c)["pack"]
    sx, sy, sw, sh = P["tiles"][P["lit"]][1]
    k1 = tl.ease_in_out_cubic(tl.prog(t, *SQUASH))
    k2 = tl.ease_in_out_cubic(tl.prog(t, *FLY))
    cx, cy = R["left"] + R["width"] / 2, R["top"] + R["height"] / 2
    mw, mh = sw * 2.4, sh * 1.3
    x0, y0, w0, h0 = R["left"], R["top"], R["width"], R["height"]
    x1, y1 = cx - mw / 2, cy - mh / 2
    x, y = tl.lerp(x0, x1, k1), tl.lerp(y0, y1, k1)
    w, h = tl.lerp(w0, mw, k1), tl.lerp(h0, mh, k1)
    arc = -d.cq(4) * math.sin(math.pi * k2)
    x, y = tl.lerp(x, sx, k2), tl.lerp(y, sy, k2) + arc
    w, h = tl.lerp(w, sw, k2), tl.lerp(h, sh, k2)
    return x, y, w, h, 0.5 * k1 + 0.5 * k2


def _collapse(t: float):
    return tl.ease_in_cubic(tl.prog(t, *tl.COLLAPSE))


def _dot_pos(t: float, c):
    """(x, y, size) of the dot in this section, before the collapse moves it."""
    sx, sy, sw, sh = layout(c)["pack"]["tiles"][layout(c)["pack"]["lit"]][1]
    x0, y0, s0, _ = s3_query.dot(tl.FOLD[0], c)
    if t < tl.T_TILE:
        fx, fy, fw, fh, _ = _fold_rect(t, c)
        tx, ty = fx + fw, fy
        k = tl.ease_in_out_cubic(tl.prog(t, tl.FOLD[0], SQUASH[1]))
        return tl.lerp(x0, tx, k), tl.lerp(y0, ty, k), tl.lerp(s0, DOT_REST, k)
    return sx + sw, sy, DOT_REST


def _anchor(t: float, c):
    """Where the page collapses to: the dot, travelling to the frame's centre."""
    x, y, _ = _dot_pos(min(t, tl.COLLAPSE[0]), c)
    k = tl.ease_in_out_cubic(tl.prog(t, *tl.COLLAPSE))
    return (x, y), (tl.lerp(x, W / 2, k), tl.lerp(y, H / 2, k))


# ---------------------------------------------------------------- drawing

def _browser(ctx, t: float, B) -> None:
    k = tl.ease_out_cubic(tl.prog(t, *tl.BROWSER_IN))
    if k <= 0:
        return
    s = tl.lerp(1.25, 1.0, k)
    cx, cy = B["left"] + B["width"] / 2, B["top"] + B["height"] / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.translate(-cx, -cy)
    ctx.push_group()

    def box(g):
        d.round_rect(g, B["left"], B["top"], B["width"], B["height"], d.cq(0.8))
        g.fill()
    d.soft_shadow(ctx, box, dy=d.cq(2), alpha=0.5)
    l, tp, w, h = B["left"], B["top"], B["width"], B["height"]
    d.round_rect(ctx, l + 0.5, tp + 0.5, w - 1, h - 1, d.cq(0.8))
    ctx.set_source_rgb(*d.BROWSER)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.rectangle(l, tp, w, BAR_H + 1)
    ctx.set_source_rgb(*d.RAISED)
    ctx.fill()
    ctx.move_to(l, tp + 1 + BAR_H + 0.5)
    ctx.line_to(l + w, tp + 1 + BAR_H + 0.5)
    ctx.set_line_width(1)
    ctx.set_source_rgb(*d.LINE)
    ctx.stroke()
    ctx.restore()
    ctx.set_line_width(1)
    ctx.set_source_rgb(*d.LINE_HI)
    ctx.stroke()
    x = l + 1 + d.cq(1.2)
    for _ in range(3):
        ctx.arc(x + d.cq(0.325), tp + 1 + BAR_H / 2, d.cq(0.325), 0, 2 * math.pi)
        ctx.set_source_rgb(*d.LINE)
        ctx.fill()
        x += d.cq(0.65) + d.cq(0.55)
    d.text(ctx, B["url"], x - d.cq(0.55) + d.cq(1.2), B["url_base"], family=d.MONO, px=TXT_PX,
           color=d.MUTED)
    il = B["inner_l"]
    d.text(ctx, B["eyebrow"], il, B["eyebrow_base"], family=d.MONO, px=TXT_PX, weight=500,
           color=d.ACCENT, tracking=TRACK)
    d.draw_paragraph(ctx, B["title"], il, B["title_top"], color=d.TEXT)
    for bx, by, bw in B["bars"]:
        d.round_rect(ctx, bx, by, bw, d.cq(0.5), d.cq(0.25))
        ctx.set_source_rgb(*d.BAR)
        ctx.fill()
    d.round_rect(ctx, il + 0.5, round(B["mini_top"]) + 0.5, B["inner"] - 1, B["mini_h"] - 1,
                 d.cq(0.5))
    ctx.set_source_rgb(*d.BG)
    ctx.fill_preserve()
    ctx.set_source_rgb(*d.LINE)
    ctx.stroke()
    for sp, base, _ in B["rows"]:
        d.code_line(ctx, sp, il + 1 + MINI_PAD[1], base, px=MINI_PX)
    lk = tl.prog(t, tl.T_LIVE, tl.T_LIVE + 0.15)
    if lk > 0:
        r = LIVE_DOT / 2
        cxl, cyl = il + r, B["live_mid"]
        ring = ((t - tl.T_LIVE) % 0.8) / 0.8
        ctx.arc(cxl, cyl, r + d.cq(1.2) * ring, 0, 2 * math.pi)
        ctx.set_source_rgba(*d.SAGE, 0.6 * (1 - ring) * lk)
        ctx.fill()
        ctx.arc(cxl, cyl, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*d.SAGE, lk)
        ctx.fill()
        d.text(ctx, "LIVE", il + LIVE_DOT + d.cq(0.6), B["live_base"], family=d.MONO,
               px=TXT_PX, weight=500, color=d.SAGE, alpha=lk, tracking=TRACK)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(k)
    ctx.restore()


def _tile(ctx, tech: str, rect, *, lit: float, alpha: float) -> None:
    x, y, w, h = rect
    d.round_rect(ctx, x + 0.5, y + 0.5, w - 1, h - 1, d.cq(0.35))
    fill = tuple(tl.lerp(a, b, lit) for a, b in zip(d.SOFT, d.EMBER_BG))
    edge = tuple(tl.lerp(a, b, lit) for a, b in zip(d.TILE_EDGE, d.ACCENT))
    ctx.set_source_rgba(*fill, alpha)
    ctx.fill_preserve()
    ctx.set_line_width(1)
    ctx.set_source_rgba(*edge, alpha)
    ctx.stroke()
    col = tuple(tl.lerp(a, b, lit) for a, b in zip(d.DIM, d.TEXT))
    base = d.css_baseline(y + (h - TILE_PX) / 2, family=d.MONO, px=TILE_PX, line_height=1.0)
    d.text(ctx, tech, x + w / 2, base, family=d.MONO, px=TILE_PX, color=col, alpha=alpha,
           align="center", hud=True)


def _pack(ctx, t: float, P) -> None:
    a = tl.ease_out_cubic(tl.prog(t, tl.FOLD[0], tl.FOLD[0] + 0.3))
    if a <= 0:
        return
    x = P["left"]
    hw = d.text(ctx, P["head"][0].upper(), x, P["head_base"], family=d.MONO, px=TXT_PX,
                weight=500, color=d.TEXT, alpha=a, tracking=TRACK)[0]
    d.text(ctx, P["head"][1].upper(), x + hw, P["head_base"], family=d.MONO, px=TXT_PX,
           weight=500, color=d.MUTED, alpha=a, tracking=TRACK)
    for i, (tech, rect) in enumerate(P["tiles"]):
        ta = tl.ease_out_cubic(tl.prog(t, tl.FOLD[0] + 0.012 * i, tl.FOLD[0] + 0.012 * i + 0.2))
        if i == P["lit"]:
            if t < tl.T_TILE:   # the empty slot waits for the folding rule
                rx, ry, rw, rh = rect
                ctx.save()
                ctx.set_dash([4, 4])
                d.round_rect(ctx, rx + 0.5, ry + 0.5, rw - 1, rh - 1, d.cq(0.35))
                ctx.set_line_width(1)
                ctx.set_source_rgba(*d.LINE, ta)
                ctx.stroke()
                ctx.restore()
                continue
            k = tl.prog(t, tl.T_TILE, tl.T_TILE + 0.3)
            s = 1 + 0.12 * math.sin(math.pi * k) * (1 - k)
            rx, ry, rw, rh = rect
            ctx.save()
            ctx.translate(rx + rw / 2, ry + rh / 2)
            ctx.scale(s, s)
            ctx.translate(-(rx + rw / 2), -(ry + rh / 2))
            _tile(ctx, tech, rect, lit=1.0, alpha=1.0)
            ctx.restore()
        else:
            _tile(ctx, tech, rect, lit=0.0, alpha=ta)
    for i, (name, what, base) in enumerate(P["dest"]):
        t0 = tl.TICKS[i]
        k = tl.ease_out_cubic(tl.prog(t, t0, t0 + 0.2))
        if k <= 0:
            continue
        dx = -d.cq(1) * (1 - k)
        tk = P["tick"]
        d.check(ctx, x + dx, base - TXT_PX * 0.72, tk * 0.8, d.SAGE, alpha=k,
                draw=tl.prog(t, t0, t0 + 0.25))
        nx = x + dx + tk + d.cq(0.8)
        d.text(ctx, name, nx, base, family=d.MONO, px=TXT_PX, weight=500, color=d.TEXT,
               alpha=k)
        nw = max(DEST_NAME, _w(name, weight=500))
        d.text(ctx, what, nx + nw + d.cq(0.8), base, family=d.MONO, px=TXT_PX,
               color=d.MUTED, alpha=k)


def _fold(ctx, t: float, c, glow_only: bool = False) -> None:
    if not (tl.FOLD[0] <= t < tl.T_TILE):
        return
    x, y, w, h, k = _fold_rect(t, c)
    fill = tuple(tl.lerp(a, b, k) for a, b in zip(d.SOFT, d.EMBER_BG))
    edge = tuple(tl.lerp(a, b, k) for a, b in zip(d.LINE_HI, d.ACCENT))
    d.round_rect(ctx, x, y, w, h, tl.lerp(d.cq(0.8), d.cq(0.35), k))
    if glow_only:
        ctx.set_line_width(5)
        ctx.set_source_rgba(*d.ACCENT, k)
        ctx.stroke()
        return
    ctx.set_source_rgba(*fill, 0.94)
    ctx.fill_preserve()
    ctx.set_line_width(1)
    ctx.set_source_rgb(*edge)
    ctx.stroke()
    ta = tl.prog(k, 0.55, 0.85)
    if ta > 0:
        base = d.css_baseline(y + (h - TILE_PX) / 2, family=d.MONO, px=TILE_PX, line_height=1.0)
        d.text(ctx, c.technique, x + w / 2, base, family=d.MONO, px=TILE_PX, color=d.TEXT,
               alpha=ta, align="center", hud=True)


def _scene(ctx, t: float, c) -> None:
    L = layout(c)
    _pack(ctx, t, L["pack"])
    _browser(ctx, t, L["browser"])
    _fold(ctx, t, c)


def _collapsed(ctx, t: float, c, fn) -> None:
    """Run fn under the collapse: the page shrinks into the travelling dot."""
    k = _collapse(t)
    if k <= 0:
        fn(ctx)
        return
    (x0, y0), (x1, y1) = _anchor(t, c)
    s = 1 - k
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x1, y1)
    ctx.scale(s, s)
    ctx.translate(-x0, -y0)
    ctx.push_group()
    fn(ctx)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(1 - tl.ease_in_cubic(tl.prog(t, 12.2, tl.COLLAPSE[1])))
    ctx.restore()


def draw(ctx, t: float, c) -> None:
    if t < tl.FOLD[0] or t > tl.COLLAPSE[1]:
        return
    a = tl.prog(t, tl.FOLD[0], tl.FOLD[0] + 0.5) * (1 - tl.prog(t, 12.0, 12.4))
    d.backlight(ctx, 0.62 * W, 0.4 * H, 0.13 * a)   # storyboard --gx:62% --gy:40%
    _collapsed(ctx, t, c, lambda g: _scene(g, t, c))


def glow(ctx, t: float, c) -> None:
    if t < tl.FOLD[0] or t > tl.COLLAPSE[1]:
        return

    def fn(g):
        _fold(g, t, c, glow_only=True)
        if t >= tl.T_TILE:
            P = layout(c)["pack"]
            x, y, w, h = P["tiles"][P["lit"]][1]
            d.round_rect(g, x, y, w, h, d.cq(0.35))
            g.set_line_width(6)
            g.set_source_rgba(*d.ACCENT, 0.7 + 0.3 * math.exp(-(t - tl.T_TILE) / 0.3))
            g.stroke()
    _collapsed(ctx, t, c, fn)


def dot(t: float, c):
    """The dot rides the folding rule into its tile, waits there through the
    ticks, then carries the collapsing page to the frame's centre."""
    if t < tl.FOLD[0] or t > tl.COLLAPSE[1] + 0.05:
        return None
    x, y, size = _dot_pos(min(t, tl.COLLAPSE[0]), c)
    pulse = 0.3 * sum(d.bump(t, tk, 0.3) for tk in tl.TICKS)
    size *= 1 + pulse
    if t >= tl.COLLAPSE[0]:
        _, (x, y) = _anchor(t, c)
        size = tl.lerp(DOT_REST, DOT_END, tl.ease_in_out_cubic(tl.prog(t, *tl.COLLAPSE)))
    return x, y, size, 1.0
