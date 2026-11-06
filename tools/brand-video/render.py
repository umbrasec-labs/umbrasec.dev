#!/usr/bin/env python3
"""Render the UMBRASEC brand film.

Stills, to check frames against the storyboard:
    python3 tools/brand-video/render.py stills --at 0.3,1.0,2.4 --out DIR
writes one PNG per time and DIR/sheet.png. Facts are read from the repos at
render time; set BRAND_VIDEO_CLAIMS to a fresh Claims Ledger predicate.json
if detections/out has none (see README.md).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
DETECTIONS = SITE.parent / "detections"
sys.path.insert(0, str(HERE))

import cairo  # noqa: E402

import compose  # noqa: E402
import content  # noqa: E402
import draw  # noqa: E402
import timeline as tl  # noqa: E402

THUMB = 3   # contact sheet thumbnails are a third of the frame


def still_name(t: float) -> str:
    return f"t{t:06.3f}.png"


def stills(times: list[float], out: Path) -> list[Path]:
    c = content.load(SITE, DETECTIONS)
    out.mkdir(parents=True, exist_ok=True)
    shots, paths = [], []
    for t in times:
        s = compose.frame(t, c)
        path = out / still_name(t)
        s.write_to_png(str(path))
        shots.append((t, s))
        paths.append(path)
    sheet(shots, out / "sheet.png")
    return paths


def sheet(shots, dest: Path, cols: int = 3) -> None:
    tw, th, pad, lab = tl.W // THUMB, tl.H // THUMB, 12, 30
    n_cols = min(cols, len(shots))
    rows = (len(shots) + cols - 1) // cols
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, pad + n_cols * (tw + pad),
                              pad + rows * (th + lab + pad))
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.06, 0.06, 0.06)
    ctx.paint()
    for i, (t, s) in enumerate(shots):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + lab + pad)
        ctx.save()
        ctx.translate(x, y + lab)
        ctx.scale(1 / THUMB, 1 / THUMB)
        pat = cairo.SurfacePattern(s)
        pat.set_filter(cairo.FILTER_GOOD)
        ctx.set_source(pat)
        ctx.paint()
        ctx.restore()
        draw.text(ctx, f"{t:.2f} s   {tl.timecode(t)}   {tl.section_at(t).label}", x, y + 20,
                  family=draw.MONO, px=16, color=draw.MUTED, hud=True)
    surf.write_to_png(str(dest))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("stills", help="render chosen frames and a contact sheet")
    st.add_argument("--at", required=True, help="times in seconds, comma separated")
    st.add_argument("--out", required=True, type=Path)
    args = p.parse_args(argv)
    if args.cmd == "stills":
        for path in stills([float(x) for x in args.at.split(",") if x.strip()], args.out):
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
