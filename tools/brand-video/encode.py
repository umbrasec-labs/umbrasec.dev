"""H.264 encoding with GStreamer: the site copy and the optional 4K master,
both with sound (the site starts muted and has a sound button), plus the poster
JPEG. Uses only gst-launch-1.0 and gst-discoverer-1.0 with stock plugins
(openh264, voaacenc, mp4mux).

The site copy has a hard ceiling: Cloudflare Pages refuses any file over
25 MiB, and the film plays on every visit. SITE_MAX_BYTES is the budget and
SITE_BPS is chosen to stay under it for timeline.DURATION (test_encode checks
both the arithmetic and the committed file).
"""
from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Iterable

import timeline as tl

MASTER_BPS, SITE_BPS = 45_000_000, 6_500_000
MASTER_AUDIO_BPS, SITE_AUDIO_BPS = 256_000, 128_000
SITE_MAX_BYTES = 20_000_000          # our budget for the site copy
PAGES_MAX_BYTES = 25 * 1024 * 1024   # Cloudflare Pages refuses anything larger


def site_bytes_estimate() -> float:
    """What the site copy weighs if the encoder holds its bitrate, with 1% for the container."""
    return (SITE_BPS + SITE_AUDIO_BPS) * tl.DURATION / 8 * 1.01


def _h264(bps: int) -> str:
    return (f"openh264enc bitrate={bps} rate-control=bitrate complexity=high "
            f"enable-frame-skip=false gop-size={tl.FPS * 2} ! h264parse")


def film(frames: Iterable[bytes], wav: Path, dest: Path, *, bps: int, audio_bps: int) -> None:
    """Encode raw BGRx frames (cairo RGB24 data, OUT_W x OUT_H as timeline has
    them now) and the sound to one MP4."""
    w, h = tl.OUT_W, tl.OUT_H
    q = shlex.quote
    pipeline = (
        f"fdsrc fd=0 blocksize={w * h * 4} ! rawvideoparse format=bgrx width={w} height={h} "
        f"framerate={tl.FPS}/1 ! videoconvert ! video/x-raw,format=I420 ! "
        f"queue max-size-buffers=8 ! {_h264(bps)} ! queue ! mux. "
        f"filesrc location={q(str(wav))} ! wavparse ! audioconvert ! audioresample ! "
        f"voaacenc bitrate={audio_bps} ! queue ! mux. "
        f"mp4mux name=mux faststart=true ! filesink location={q(str(dest))}")
    proc = subprocess.Popen(["gst-launch-1.0", "-q", "-e", *shlex.split(pipeline)],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    try:
        for f in frames:
            if len(f) != w * h * 4:
                raise ValueError(f"a frame has {len(f)} bytes, expected {w * h * 4}")
            proc.stdin.write(f)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"gst-launch failed ({code}): {err[-800:]}")


def resound(src: Path, wav: Path, dst: Path, audio_bps: int) -> None:
    """Copy src's picture untouched and give it a new AAC track from wav."""
    q = shlex.quote
    pipeline = (
        f"filesrc location={q(str(src))} ! qtdemux name=d "
        f"d.video_0 ! queue ! h264parse ! mux. "
        f"filesrc location={q(str(wav))} ! wavparse ! audioconvert ! audioresample ! "
        f"voaacenc bitrate={audio_bps} ! queue ! mux. "
        f"mp4mux name=mux faststart=true ! filesink location={q(str(dst))}")
    r = subprocess.run(["gst-launch-1.0", "-q", "-e", *shlex.split(pipeline)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(f"gst-launch failed ({r.returncode}): "
                           f"{r.stderr.decode(errors='replace')[-800:]}")


POSTER_MAX = 350_000   # bytes
POSTER_W, POSTER_H = 2560, 1440


def poster(png: Path, jpg: Path) -> None:
    """The PNG as a JPEG at the best quality from 85 down that fits POSTER_MAX,
    at 1440p like the site copy: it shows until the film plays."""
    for q in range(85, 40, -5):
        subprocess.run(["gst-launch-1.0", "-q", "filesrc", f"location={png}", "!", "pngdec",
                        "!", "videoconvert", "!", "videoscale", "method=lanczos", "!",
                        f"video/x-raw,width={POSTER_W},height={POSTER_H}", "!", "jpegenc", f"quality={q}", "!", "filesink",
                        f"location={jpg}"], check=True, capture_output=True)
        if jpg.stat().st_size <= POSTER_MAX:
            return
    raise RuntimeError(f"{jpg} is over {POSTER_MAX} bytes even at quality {q}")


def probe(path: Path) -> dict:
    """Duration, size, frame rate, video codec and audio layout, from gst-discoverer."""
    out = subprocess.run(["gst-discoverer-1.0", "-v", str(path)], check=True,
                         capture_output=True, text=True).stdout
    def find(pat, cast=str, default=None):
        m = re.search(pat, out)
        return cast(m.group(1)) if m else default
    dur = find(r"Duration: (\d+:\d+:[\d.]+)")
    hh, mm, ss = dur.split(":") if dur else ("0", "0", "0")
    has_audio = re.search(r"^\s*audio #\d+:", out, re.M) is not None
    return dict(
        duration=int(hh) * 3600 + int(mm) * 60 + float(ss),
        width=find(r"Width: (\d+)", int), height=find(r"Height: (\d+)", int),
        fps=find(r"Frame rate: (\d+/\d+)"),
        video=find(r"video codec: ([^\n]+)", default=""),
        audio_channels=find(r"Channels: (\d+)", int) if has_audio else None,
        audio_rate=find(r"Sample rate: (\d+)", int) if has_audio else None)
