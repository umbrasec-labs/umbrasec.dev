"""03 Build the query, 6.0 - 10.0 s: the real rule types itself and catches its trace.

Storyboard frame 03. The chip lands as the rule's tag line while the rule
types one line per 16th note, the dot stepping down the gutter beside each new
line; the synthetic event slides in from the left; the dot draws a wire from
.aws/credentials in the event to the same string in the rule; MATCH pops on
the wire and the Claims Ledger counter runs up to every executed claim.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache

import cairo

import draw as d
import timeline as tl

W, H = tl.W, tl.H
CODE_PX, CODE_LH = d.cq(1.1), 1.62   # storyboard 1.08cqw (20.7 px), raised to 21 px
LABEL_PX, LABEL_TRACK = 18.0, 0.14   # storyboard .8cqw (15 px), raised to the 18 px floor
FOOT_PX = 18.0
PAD_T, PAD_X, PAD_B = d.cq(1.3), d.cq(1.6), d.cq(1.2)
RADIUS = d.cq(0.8)
LABEL_GAP, FOOT_GAP, FOOT_PAD = d.cq(1.0), d.cq(0.9), d.cq(0.8)
# panels sit on whole pixels so their 1 px edges stay crisp
TRACE_BOX = (round(d.cq(4.5)), round(d.cq(16.5)), round(d.cq(39)))   # left, top, width
RULE_BOX = (round(d.cq(47)), round(d.cq(48.5)))                       # left, width; centred
CLAIMS_BOX = (round(d.cq(4.5)), round(d.cq(36)), round(d.cq(39)))
BIG_PX, BIG_TRACK = d.cq(3), -0.02
COL_GAP, ROW_GAP = d.cq(1.4), d.cq(0.5)
LVL_PAD, LVL_TRACK = (d.cq(0.5), d.cq(0.3)), 0.06
OK_DOT, OK_GAP = d.cq(0.55), d.cq(0.6)
MATCH_PX, MATCH_PAD = 18.0, (d.cq(0.6), d.cq(0.35))
WIRE_W = d.cq(0.17)
UNDER = d.cq(0.06)                   # a highlight's underline: its middle above the box bottom
SLIDE = d.cq(6)                      # the event slides in from this far left
CLAIMS_IN = (8.2, 8.5)
TYPE_DUR = 0.09                      # a rule line types out in about three frames
STEP_MOVE = 0.09                     # the dot's step down the gutter
TO_TRACE = (7.75, 8.0)               # the dot crosses to the event
OUT = (9.95, 10.3)                   # stand-in exit until the publish section takes the rule
DOT_GUTTER, DOT_WIRE = d.cq(0.6), d.cq(0.75)
CRED = ".aws/credentials"
AGENT = "/.local/share/claude/versions/"

_KEY = re.compile(r"([A-Za-z_][\w|]*):(.*)$")


def spans(line: str, marks) -> tuple[tuple[str, str], ...]:
    """(kind, text) spans for one excerpt line, coloured like the hero reel:
    keys, dashes, "..." cuts and _meta lines, and the marked strings."""
    body = line.lstrip(" ")
    out = [("plain", line[:len(line) - len(body)])]
    if body == "..." or body.startswith("_"):
        out.append(("c", body))
    else:
        if body.startswith("- "):
            out += [("d", "-"), ("plain", " ")]
            body = body[2:]
        m = _KEY.match(body)
        if m:
            out.append(("k", m.group(1)))
            body = ":" + m.group(2)
        while body:
            hits = [(body.find(s), s) for s in marks if s in body]
            if not hits:
                out.append(("plain", body))
                break
            i, s = min(hits)
            out += [("plain", body[:i]), ("hl", s)]
            body = body[i + len(s):]
    return tuple(sp for sp in out if sp[1])


def _w(s: str, px: float = CODE_PX, weight: int = 400, tracking: float = 0.0) -> float:
    return d.measure(s, family=d.MONO, px=px, weight=weight, tracking=tracking)[0]


def _panel(lines, marks, left: int, top: int, width: int) -> dict:
    """A Trace or Rule panel like the storyboard's .panel: label row, code,
    and a foot under a hairline. Each mark's text box is kept for the wire."""
    inner_l, inner = left + 1 + PAD_X, width - 2 - 2 * PAD_X
    label_top = top + 1 + PAD_T
    code_top = label_top + LABEL_PX + LABEL_GAP
    asc, desc = d.metrics(d.MONO, CODE_PX)
    lh = CODE_LH * CODE_PX
    rows, hl = [], {}
    for i, line in enumerate(lines):
        sp = spans(line, marks)
        base = d.css_baseline(code_top + i * lh, family=d.MONO, px=CODE_PX, line_height=CODE_LH)
        x = inner_l
        for kind, s in sp:
            if kind == "hl":
                hl.setdefault(s, (x, base - asc, _w(s), asc + desc))
            x += _w(s)
        rows.append(dict(line=line, spans=sp, base=base, mid=code_top + (i + 0.5) * lh,
                         width=x - inner_l))
    missing = [m for m in marks if m not in hl]
    if missing:
        raise ValueError(f"nothing to highlight for {missing}")
    foot_rule = round(code_top + len(lines) * lh + FOOT_GAP)
    foot_top = foot_rule + 1 + FOOT_PAD
    height = round(foot_top + 1.3 * FOOT_PX + PAD_B + 1 - top)
    return dict(left=left, top=top, width=width, height=height, bottom=top + height,
                inner_l=inner_l, inner=inner, rows=rows, hl=hl, label_top=label_top,
                label_base=d.css_baseline(label_top, family=d.MONO, px=LABEL_PX,
                                          line_height=1.0, weight=500),
                foot_rule=foot_rule,
                foot_base=d.css_baseline(foot_top, family=d.MONO, px=FOOT_PX, line_height=1.3))


def _claims_box(c) -> dict:
    """The Claims Ledger box: the big counter beside its label and detail."""
    left, top, width = CLAIMS_BOX
    inner_l, inner = left + 1 + PAD_X, width - 2 - 2 * PAD_X
    total = c.claims_executed
    big_w = d.measure(f"{total} / {total}", family=d.MONO, px=BIG_PX, weight=500,
                      tracking=BIG_TRACK)[0]
    col2_w = inner - big_w - COL_GAP
    label = "Executed claims · pass".upper()
    det = d.paragraph(f"Claims Ledger, all {c.pack_sigma + c.pack_kql} pack files, re-run in CI",
                      width=col2_w, family=d.MONO, px=FOOT_PX, line_height=1.3)
    rows_h = LABEL_PX + ROW_GAP + det.height
    content_h = max(BIG_PX, rows_h)
    ctop = top + 1 + PAD_T
    row1 = ctop + (content_h - rows_h) / 2
    height = round(2 + 2 * PAD_T + content_h)
    side = max([_w(label, LABEL_PX, 500, LABEL_TRACK), *d.line_widths(det)])
    return dict(left=left, top=top, width=width, height=height, bottom=top + height,
                inner_l=inner_l, inner=inner, col2=inner_l + big_w + COL_GAP,
                total=total, passed=c.claims_passed, label=label, det=det,
                big_base=d.css_baseline(ctop + (content_h - BIG_PX) / 2, family=d.MONO,
                                        px=BIG_PX, line_height=1.0, weight=500),
                label_base=d.css_baseline(row1, family=d.MONO, px=LABEL_PX, line_height=1.0,
                                          weight=500),
                det_top=row1 + LABEL_PX + ROW_GAP, widths=[big_w + COL_GAP + side])


@lru_cache(maxsize=4)
def layout(c) -> dict:
    """Every panel at rest, the wire between the two credentials strings and
    the MATCH point on it. Widths are listed so a test can see nothing clips."""
    tag = f"attack.{c.technique.lower()}"
    rule_marks = (tag, f"'{AGENT}'", f"'{CRED}'")
    trace = _panel(c.trace_lines, (AGENT, CRED), *TRACE_BOX)
    trace.update(label=("Trace", "synthetic event · Claims Ledger"),
                 foot=f"expect: match · {c.claim_name}")
    probe = _panel(c.rule_lines, rule_marks, RULE_BOX[0], 0, RULE_BOX[1])
    rule = _panel(c.rule_lines, rule_marks, RULE_BOX[0], round((H - probe["height"]) / 2),
                  RULE_BOX[1])
    level = next(ln for ln in c.rule_lines if ln.startswith("level:"))
    rule.update(label=("Rule", None), badge=level,
                foot=c.rule_path.removeprefix("tools/sigma-pack/"))
    label_gap = d.cq(1)
    trace["widths"] = [r["width"] for r in trace["rows"]] + [
        _w("TRACE", LABEL_PX, 500, LABEL_TRACK) + label_gap
        + _w(trace["label"][1].upper(), LABEL_PX, 500, LABEL_TRACK),
        OK_DOT + OK_GAP + _w(trace["foot"], FOOT_PX)]
    rule["widths"] = [r["width"] for r in rule["rows"]] + [
        _w("RULE", LABEL_PX, 500, LABEL_TRACK) + label_gap + _badge_size(level)[0],
        _w(rule["foot"], FOOT_PX)]
    claims = _claims_box(c)

    tx, ty, tw, th = trace["hl"][CRED]
    rx, ry, rw, rh = rule["hl"][f"'{CRED}'"]
    # underline to underline: out past the closing quotes, in under the dash
    p0, p3 = (tx + tw + 1, ty + th - UNDER), (rx - 1, ry + rh - UNDER)
    k = 0.4 * (p3[0] - p0[0])
    wire = (p0, (p0[0] + k, p0[1]), (p3[0] - k, p3[1]), p3)
    gap = (trace["left"] + trace["width"] + rule["left"]) / 2
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if d.bezier(wire, mid)[0] < gap else (lo, mid)
    flashes = {("rule", tag): tl.CHIP_FLIGHT[1], ("trace", CRED): tl.WIRE[0],
               ("rule", f"'{CRED}'"): tl.WIRE[1], ("trace", AGENT): tl.T_MATCH,
               ("rule", f"'{AGENT}'"): tl.T_MATCH}
    return dict(trace=trace, rule=rule, claims=claims, wire=wire,
                match=d.bezier(wire, lo), tag=tag, flashes=flashes)


def _badge_size(s: str) -> tuple[float, float]:
    return (_w(s, LABEL_PX, 500, LVL_TRACK) + 2 * LVL_PAD[0] + 2,
            LABEL_PX + 2 * LVL_PAD[1] + 2)


# ---------------------------------------------------------------- timing

def _flash(t: float, t0: float, decay: float = 0.25) -> float:
    """A quick rise at t0 and a slow fall: a highlight lighting up."""
    if t < t0:
        return 0.0
    return tl.prog(t, t0, t0 + 0.05) * math.exp(-max(0.0, t - t0 - 0.05) / decay)


def _out(t: float) -> float:
    return 1 - tl.ease_in_cubic(tl.prog(t, *OUT))


def _trace_dx(t: float) -> float:
    return -SLIDE * (1 - tl.ease_out_cubic(tl.prog(t, *tl.TRACE_IN)))


def _poses(t: float):
    """(dx, dy, alpha) for the trace, rule and claims panels."""
    out = _out(t)
    r = tl.ease_out_cubic(tl.prog(t, *tl.RULE_IN))
    tr = tl.ease_out_cubic(tl.prog(t, *tl.TRACE_IN))
    cl = tl.ease_out_cubic(tl.prog(t, *CLAIMS_IN))
    return ((_trace_dx(t), 0.0, tr * out), (0.0, (1 - r) * d.cq(1.2), r * out),
            (0.0, (1 - cl) * d.cq(1), cl * out))


def _shown(t: float, i: int, line: str):
    """Characters of rule line i on screen at t: 0 before it types, None once
    it is whole. A "..." cut appears whole with the line above it."""
    t0 = tl.RULE_LINE_T[i]
    if t < t0:
        return 0
    body = line.lstrip(" ")
    if body == "...":
        return None
    n = math.ceil(len(body) * tl.prog(t, t0, t0 + TYPE_DUR))
    return None if n >= len(body) else len(line) - len(body) + n


def _wire_u(t: float) -> float:
    return tl.ease_in_out_cubic(tl.prog(t, *tl.WIRE))


# ---------------------------------------------------------------- drawing

def _shell(ctx, p, at, *, edge, edge_a=1.0, fill=d.SOFT, fill_a=0.94) -> None:
    dx, dy, a = at
    if a <= 0:
        return
    d.round_rect(ctx, p["left"] + dx + 0.5, p["top"] + dy + 0.5, p["width"] - 1,
                 p["height"] - 1, RADIUS)
    ctx.set_source_rgba(*fill, fill_a * a)
    ctx.fill_preserve()
    ctx.set_line_width(1.0)
    ctx.set_source_rgba(*edge, edge_a * a)
    ctx.stroke()


def _head(ctx, p, at) -> None:
    """Label row and foot of a Trace or Rule panel."""
    dx, dy, a = at
    x, right = p["inner_l"] + dx, p["inner_l"] + p["inner"] + dx
    left_s, right_s = p["label"]
    d.text(ctx, left_s.upper(), x, p["label_base"] + dy, family=d.MONO, px=LABEL_PX,
           weight=500, color=d.TEXT, alpha=a, tracking=LABEL_TRACK)
    if right_s:
        d.text(ctx, right_s.upper(), right, p["label_base"] + dy, family=d.MONO, px=LABEL_PX,
               weight=500, color=d.MUTED, alpha=a, tracking=LABEL_TRACK, align="right")
    if p.get("badge"):
        bw, bh = _badge_size(p["badge"])
        top = p["label_top"] + LABEL_PX / 2 - bh / 2 + dy
        d.round_rect(ctx, right - bw + 0.5, round(top) + 0.5, bw - 1, bh - 1, d.cq(0.3))
        ctx.set_source_rgba(*d.EMBER, 0.08 * a)
        ctx.fill_preserve()
        ctx.set_line_width(1.0)
        ctx.set_source_rgba(*d.EMBER, 0.5 * a)
        ctx.stroke()
        base = d.css_baseline(round(top) + 1 + LVL_PAD[1], family=d.MONO, px=LABEL_PX,
                              line_height=1.0, weight=500)
        d.text(ctx, p["badge"], right - bw + 1 + LVL_PAD[0], base, family=d.MONO,
               px=LABEL_PX, weight=500, color=d.EMBER, alpha=a, tracking=LVL_TRACK)
    y = p["foot_rule"] + 0.5 + dy
    ctx.move_to(x, y)
    ctx.line_to(right, y)
    ctx.set_line_width(1.0)
    ctx.set_source_rgba(*d.LINE, 0.6 * a)
    ctx.stroke()
    fx = x
    if p is not None and p["label"][0] == "Trace":
        ctx.arc(x + OK_DOT / 2, p["foot_base"] + dy - OK_DOT / 2, OK_DOT / 2, 0, 2 * math.pi)
        ctx.set_source_rgba(*d.SAGE, a)
        ctx.fill()
        fx += OK_DOT + OK_GAP
    d.text(ctx, p["foot"], fx, p["foot_base"] + dy, family=d.MONO, px=FOOT_PX,
           color=d.MUTED, alpha=a)


def _code(ctx, t: float, p, at, name: str, flashes, typed: bool) -> None:
    dx, dy, a = at
    if a <= 0:
        return
    for i, row in enumerate(p["rows"]):
        n = _shown(t, i, row["line"]) if typed else None
        if n == 0:
            continue
        h = 1.0 + sum(1.6 * _flash(t, flashes.get((name, s), math.inf))
                      for kind, s in row["spans"] if kind == "hl")
        x, base = p["inner_l"] + dx, row["base"] + dy
        ctx.save()
        if n is not None:
            ctx.rectangle(x - 2, base - CODE_PX * 1.3, _w(row["line"][:n]) + 2, CODE_PX * 1.9)
            ctx.clip()
        d.code_line(ctx, row["spans"], x, base, px=CODE_PX, alpha=a, hl=h)
        ctx.restore()


def _claims(ctx, t: float, C, at) -> None:
    dx, dy, a = at
    if a <= 0:
        return
    total = C["total"]
    n = int(C["passed"] * tl.ease_out_cubic(tl.prog(t, *tl.COUNT)))
    d.text(ctx, f"{n:>{len(str(total))}} / {total}", C["inner_l"] + dx, C["big_base"] + dy,
           family=d.MONO, px=BIG_PX, weight=500, color=d.SAGE, alpha=a, tracking=BIG_TRACK)
    d.text(ctx, C["label"], C["col2"] + dx, C["label_base"] + dy, family=d.MONO, px=LABEL_PX,
           weight=500, color=d.SAGE, alpha=a, tracking=LABEL_TRACK)
    d.draw_paragraph(ctx, C["det"], C["col2"] + dx, C["det_top"] + dy, color=d.MUTED, alpha=a)


def _wire(ctx, t: float, L, alpha: float, width: float) -> None:
    u = _wire_u(t)
    if u <= 0 or alpha <= 0:
        return
    p = d.bezier_part(L["wire"], u)
    ctx.move_to(*p[0])
    ctx.curve_to(*p[1], *p[2], *p[3])
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*d.ACCENT, alpha)
    ctx.stroke()


def _match(ctx, t: float, L, alpha: float, glow_only: bool = False) -> None:
    k = tl.prog(t, tl.T_MATCH, tl.T_MATCH + 0.18)
    if k <= 0 or alpha <= 0:
        return
    s = tl.lerp(0.5, 1.0, tl.ease_out_back(k, 2.6))
    a = alpha * tl.prog(t, tl.T_MATCH, tl.T_MATCH + 0.06)
    tw = _w("Match", MATCH_PX, 500, LABEL_TRACK)
    bw, bh = tw + 2 * MATCH_PAD[0], MATCH_PX + 2 * MATCH_PAD[1]
    ctx.save()
    ctx.translate(*L["match"])
    ctx.scale(s, s)
    d.round_rect(ctx, -bw / 2, -bh / 2, bw, bh, d.cq(0.3))
    ctx.set_source_rgba(*d.ACCENT, a)
    ctx.fill()
    if not glow_only:
        base = d.css_baseline(-MATCH_PX / 2, family=d.MONO, px=MATCH_PX, line_height=1.0,
                              weight=500)
        d.text(ctx, "Match", -tw / 2, base, family=d.MONO, px=MATCH_PX, weight=500,
               color=d.BG, alpha=a, tracking=LABEL_TRACK)
    ctx.restore()


def _bloom(g, t: float, L, poses, confirm: float) -> None:
    """The glows, drawn over the panels' fills and under their text, so the
    orange on top stays the site's exact orange."""
    trace_at, rule_at, claims_at = poses
    out = _out(t)
    _wire(g, t, L, out, WIRE_W * 4)
    _match(g, t, L, out, glow_only=True)
    for (name, mark), t0 in L["flashes"].items():
        dx, dy, a = trace_at if name == "trace" else rule_at
        f = _flash(t, t0) * a
        if f > 0:
            x, y, w, h = L[name]["hl"][mark]
            g.rectangle(x + dx - 3, y + dy - 3, w + 6, h + 6)
            g.set_source_rgba(*d.ACCENT, f)
            g.fill()
    C = L["claims"]
    if confirm > 0 and claims_at[2] > 0:
        d.round_rect(g, C["left"], C["top"] + claims_at[1], C["width"], C["height"], RADIUS)
        g.set_line_width(8)
        g.set_source_rgba(*d.SAGE, confirm * claims_at[2])
        g.stroke()


def draw(ctx, t: float, c) -> None:
    if t < tl.RULE_IN[0] or t > OUT[1]:
        return
    L = layout(c)
    poses = _poses(t)
    trace_at, rule_at, claims_at = poses
    confirm = _flash(t, tl.T_CONFIRM, 0.35)
    d.backlight(ctx, 0.46 * W, 0.52 * H, 0.13 * min(tl.prog(t, 6.0, 6.5), _out(t)))
    _shell(ctx, L["trace"], trace_at, edge=d.LINE)
    _shell(ctx, L["rule"], rule_at, edge=d.LINE_HI)
    _shell(ctx, L["claims"], claims_at, edge=d.SAGE, edge_a=0.45 + 0.55 * confirm,
           fill=d.SAGE, fill_a=0.06 + 0.08 * confirm)
    d.soft_glow(ctx, lambda g: _bloom(g, t, L, poses, confirm), alpha=0.9)
    for p, at, name, typed in ((L["trace"], trace_at, "trace", False),
                               (L["rule"], rule_at, "rule", True)):
        if at[2] > 0:
            _head(ctx, p, at)
            _code(ctx, t, p, at, name, L["flashes"], typed)
    _claims(ctx, t, L["claims"], claims_at)
    _wire(ctx, t, L, _out(t), WIRE_W)
    _match(ctx, t, L, _out(t))


def glow(ctx, t: float, c) -> None:
    """Nothing under the panels: this section's glows are drawn over them in draw()."""


def _gutter(c):
    """(time, point) for each typed rule line from the tag line on."""
    rule = layout(c)["rule"]
    gx = rule["left"] + 1 + PAD_X / 2
    return [(tl.RULE_LINE_T[i], (gx, row["mid"])) for i, row in enumerate(rule["rows"])
            if row["line"].strip() != "..." and tl.RULE_LINE_T[i] >= tl.CHIP_FLIGHT[1]]


def dot(t: float, c):
    """The dot lands with the chip, steps down the gutter as the rule types,
    crosses to the event and draws the wire, then rests on the match."""
    if t < tl.CHIP_FLIGHT[1] or t > OUT[1]:
        return None
    import s2_papers   # the dot arrives with the chip (s2_papers imports this module)
    L = layout(c)
    x, y, size = s2_papers.chip_dot(tl.CHIP_FLIGHT[1], c)
    for t0, (gx, gy) in _gutter(c):
        if t < t0:
            break
        k = tl.ease_out_cubic(tl.prog(t, t0, t0 + STEP_MOVE))
        x, y, size = tl.lerp(x, gx, k), tl.lerp(y, gy, k), tl.lerp(size, DOT_GUTTER, k)
    if t >= TO_TRACE[0]:
        p0 = L["wire"][0]
        k = tl.ease_in_out_cubic(tl.prog(t, *TO_TRACE))
        x, y = tl.lerp(x, p0[0] + _trace_dx(t), k), tl.lerp(y, p0[1], k)
        size = tl.lerp(size, DOT_WIRE, k)
    if t >= tl.WIRE[0]:
        x, y = d.bezier(L["wire"], _wire_u(t))
    pulse = 0.35 * (d.bump(t, tl.T_MATCH, 0.3) + d.bump(t, tl.T_CONFIRM, 0.3))
    return x, y, size * (1 + pulse), 1.0
