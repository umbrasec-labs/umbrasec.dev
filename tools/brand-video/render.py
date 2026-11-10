#!/usr/bin/env python3
"""Render the UMBRASEC brand film.

Stills, to check frames against the storyboard:
    python3 tools/brand-video/render.py stills --at 0.3,1.0,2.4 --out DIR
writes one PNG per time and DIR/sheet.png.

The film, its sound, the poster and the facts it shows:
    python3 tools/brand-video/render.py film --out DIR
writes DIR/brand-film.mp4 (the site copy, 1440p, 128 kbps sound),
DIR/brand-film-poster.jpg and DIR/facts.json, and keeps facts.json here too.
Add --master to also render the 4K master, a second pass, into
tools/brand-video/out/ (git-ignored and never deployed) or the folder you
name; a folder inside the repo that git does not ignore is refused. Later:
    python3 tools/brand-video/render.py drift
lists figures on screen that have changed in the repos since that render.

Facts are read from the repos at
render time; set BRAND_VIDEO_CLAIMS to a fresh Claims Ledger predicate.json
if detections/out has none (see README.md).
"""
from __future__ import annotations

import argparse
import multiprocessing
from collections import deque
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
DETECTIONS = SITE.parent / "detections"
sys.path.insert(0, str(HERE))

import cairo  # noqa: E402

import json  # noqa: E402
from datetime import date  # noqa: E402

import compose  # noqa: E402
import content  # noqa: E402
import draw  # noqa: E402
import encode  # noqa: E402
import sound  # noqa: E402
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
    tw, th, pad, lab = tl.OUT_W // THUMB, tl.OUT_H // THUMB, 12, 30
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


FACTS = HERE / "facts.json"
FIGURES = ("claims_executed", "claims_passed", "pack_sigma", "pack_kql", "kev_total",
           "technique", "article_title",
           # "Exploited now": the snapshot's day, the tier counts, every CVE on
           # the wall, and the card
           "kev_date", "kev_days", "kev_tiers", "kev_wall", "kev_cve", "kev_tier",
           "kev_note", "kev_rule", "kev_claims")
SITE_NAME, POSTER_NAME = "brand-film.mp4", "brand-film-poster.jpg"
MASTER_DIR = HERE / "out"            # git-ignored (.gitignore) and inside a folder stage.sh trims
POSTER_T = tl.FADE_OUT[0] - 0.3      # the end card, after the light has crossed it


def master_name() -> str:
    return f"umbrasec-brand-film-{tl.MASTER_H}p{tl.FPS}.mp4"


def facts(c) -> dict:
    """The figures the film shows, and the day it was rendered (JSON types)."""
    f = {"rendered": date.today().isoformat(), **{k: getattr(c, k) for k in FIGURES}}
    return json.loads(json.dumps(f))


def check_master_dir(path: Path) -> Path:
    """The master must never be committed or served: a folder inside the
    repo has to be one git ignores. Anything outside the repo is fine."""
    path = path.resolve()
    if SITE.resolve() not in path.parents and path != SITE.resolve():
        return path
    r = subprocess.run(["git", "-C", str(SITE), "check-ignore", "-q", str(path / master_name())],
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"render: {path} is inside the repo and not git-ignored; the 4K "
                         f"master must never be committed. Use {MASTER_DIR} or a folder "
                         "outside the repo.")
    return path


_CONTENT = None


def _frame(job: tuple[int, int, int]) -> bytes:
    """Frame i at w x h. The size travels with the job, so one worker can
    render the site copy and then the master."""
    i, w, h = job
    if (tl.OUT_W, tl.OUT_H) != (w, h):
        tl.set_output(w, h)
    s = compose.frame(i / tl.FPS, _CONTENT)
    s.flush()
    return bytes(s.get_data())


def ahead(jobs: int) -> int:
    """How many frames may be rendered and waiting for the encoder at once. A
    4K frame is 33 MB, and the encoder is slower than the renderers, so
    without this bound the finished frames pile up until memory runs out."""
    return 2 * max(1, jobs)


def workers(c, jobs: int):
    """The processes that render frames, or None to render in this one. They
    are forked once, before this process draws a frame or starts a thread: a
    pool forked later (a second one for the master, say) can inherit a held
    lock and never wake."""
    global _CONTENT
    _CONTENT = c
    return multiprocessing.get_context("fork").Pool(jobs) if jobs > 1 else None


def _frames(pool, jobs: int, n: int | None = None):
    """Every frame's raw bytes at the current output size, in order. A new
    frame is only started when the encoder has taken one."""
    n = tl.FRAMES if n is None else n
    w, h = tl.OUT_W, tl.OUT_H
    waiting: deque = deque()
    nxt = 0
    try:
        for i in range(n):
            if pool is None:
                f = _frame((i, w, h))
            else:
                while nxt < n and len(waiting) < ahead(jobs):
                    waiting.append(pool.apply_async(_frame, ((nxt, w, h),)))
                    nxt += 1
                f = waiting.popleft().get()
            yield f
            if i % tl.FPS == tl.FPS - 1:
                print(f"  {i + 1}/{n} frames at {w} x {h}", file=sys.stderr, flush=True)
    finally:
        for r in waiting:   # frames already started for an encoder that stopped
            r.wait()


def _wav(path: Path) -> None:
    l, r = sound.master(*sound.synth(tl.EVENTS, tl.DURATION))
    sound.write_wav(path, l, r)


def film(out: Path, *, jobs: int = 1, master: Path | None = None) -> dict:
    if master is not None:
        master = check_master_dir(master)
    c = content.load(SITE, DETECTIONS)
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "brand-film.wav"
    _wav(wav)
    size = (tl.OUT_W, tl.OUT_H)
    pool = workers(c, jobs)
    try:
        encode.film(_frames(pool, jobs), wav, out / SITE_NAME, bps=encode.SITE_BPS,
                    audio_bps=encode.SITE_AUDIO_BPS)
        weight = (out / SITE_NAME).stat().st_size
        if weight > encode.SITE_MAX_BYTES:
            raise SystemExit(f"render: {SITE_NAME} is {weight:,} bytes, over the "
                             f"{encode.SITE_MAX_BYTES:,} byte budget; lower encode.SITE_BPS")
        png = out / "brand-film-poster.png"
        compose.frame(POSTER_T, c, grain=False).write_to_png(str(png))
        encode.poster(png, out / POSTER_NAME)
        png.unlink()
        # the facts belong to the site copy: written before the optional master
        f = facts(c)
        text = json.dumps(f, indent=2) + "\n"
        (out / "facts.json").write_text(text)
        FACTS.write_text(text)
        if master is not None:
            master.mkdir(parents=True, exist_ok=True)
            tl.set_output(tl.MASTER_W, tl.MASTER_H)
            encode.film(_frames(pool, jobs), wav, master / master_name(), bps=encode.MASTER_BPS,
                        audio_bps=encode.MASTER_AUDIO_BPS)
    finally:
        if pool:
            pool.terminate()
            pool.join()
        tl.set_output(*size)
        wav.unlink(missing_ok=True)
    return f


def resound(out: Path, master: Path = MASTER_DIR) -> list[Path]:
    """New sound for the last render: the site copy in `out`, and the master
    if there is one, keep their picture (no figures change) and get a fresh
    soundtrack."""
    wav = out / "brand-film.wav"
    _wav(wav)
    done = []
    for src, bps in ((out / SITE_NAME, encode.SITE_AUDIO_BPS),
                     (master / master_name(), encode.MASTER_AUDIO_BPS)):
        if not src.is_file():
            continue
        tmp = src.with_name(src.name + ".tmp")
        encode.resound(src, wav, tmp, bps)
        tmp.replace(src)
        done.append(src)
    wav.unlink()
    if not done:
        raise SystemExit(f"render: no {SITE_NAME} in {out}")
    return done


def _short(v) -> str:
    s = json.dumps(v)
    return s if len(s) <= 90 else f"{s[:87]}..."


def drift() -> list[str]:
    """Figures on screen that no longer match the repos. For the wall it names
    the CVEs that joined or left it, or changed tier."""
    then = json.loads(FACTS.read_text())
    now = facts(content.load(SITE, DETECTIONS))
    out = []
    for k in FIGURES:
        if then.get(k) == now[k]:
            continue
        if k == "kev_wall" and isinstance(then.get(k), list):
            was, new = dict(map(tuple, then[k])), dict(map(tuple, now[k]))
            parts = [f"{len(new.keys() - was.keys())} joined", f"{len(was.keys() - new.keys())} left"]
            moved = sorted(c for c in was.keys() & new.keys() if was[c] != new[c])
            parts += [f"{c} is {new[c]} now, was {was[c]}" for c in moved]
            if list(was) != list(new) and not (new.keys() ^ was.keys()):
                parts.append("the order changed")
            out.append(f"kev_wall: {', '.join(parts)}")
        else:
            out.append(f"{k}: film shows {_short(then.get(k))}, repos now say {_short(now[k])}")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("stills", help="render chosen frames and a contact sheet")
    st.add_argument("--at", required=True, help="times in seconds, comma separated")
    st.add_argument("--out", required=True, type=Path)
    fm = sub.add_parser("film", help="render the film, sound, poster and facts.json")
    fm.add_argument("--out", required=True, type=Path)
    fm.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                    help="processes that render frames (default: every core)")
    fm.add_argument("--master", nargs="?", type=Path, const=MASTER_DIR, default=None,
                    metavar="DIR", help=f"also render the 4K master, into DIR "
                                        f"(default {MASTER_DIR.relative_to(SITE)}, git-ignored)")
    sd = sub.add_parser("sound", help="swap only the soundtrack of the films in --out")
    sd.add_argument("--out", required=True, type=Path)
    sub.add_parser("drift", help="list figures that changed since the last render")
    args = p.parse_args(argv)
    if args.cmd == "film":
        f = film(args.out, jobs=args.jobs, master=args.master)
        print(json.dumps({k: v for k, v in f.items() if k != "kev_wall"}, indent=2))
    if args.cmd == "sound":
        for path in resound(args.out):
            print(path)
    if args.cmd == "drift":
        changed = drift()
        print("\n".join(changed) if changed else
              f"no drift since the render of {json.loads(FACTS.read_text())['rendered']}")
        return 1 if changed else 0
    if args.cmd == "stills":
        for path in stills([float(x) for x in args.at.split(",") if x.strip()], args.out):
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
