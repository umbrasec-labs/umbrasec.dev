"""H.264 encoding with GStreamer: one pass makes the master and the site copy,
both with sound (the site starts muted and has a sound button), plus the poster
JPEG. Uses only gst-launch-1.0 and gst-discoverer-1.0 with stock plugins
(openh264, voaacenc, mp4mux).
"""
from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Iterable

import timeline as tl

MASTER_BPS, SITE_BPS = 8_000_000, 4_000_000
MASTER_AUDIO_BPS, SITE_AUDIO_BPS = 256_000, 128_000


def _h264(bps: int) -> str:
    return (f"openh264enc bitrate={bps} rate-control=bitrate complexity=high "
            f"enable-frame-skip=false gop-size={tl.FPS * 2} ! h264parse")


def film(frames: Iterable[bytes], wav: Path, master: Path, site: Path) -> None:
    """Encode raw BGRx frames (cairo RGB24 data, W x H) to both files."""
    w, h = tl.W, tl.H
    q = shlex.quote
    pipeline = (
        f"fdsrc fd=0 blocksize={w * h * 4} ! rawvideoparse format=bgrx width={w} height={h} "
        f"framerate={tl.FPS}/1 ! videoconvert ! video/x-raw,format=I420 ! tee name=t "
        f"t. ! queue max-size-buffers=8 ! {_h264(MASTER_BPS)} ! queue ! mux. "
        f"filesrc location={q(str(wav))} ! wavparse ! audioconvert ! audioresample ! tee name=a "
        f"a. ! queue ! voaacenc bitrate={MASTER_AUDIO_BPS} ! queue ! mux. "
        f"mp4mux name=mux faststart=true ! filesink location={q(str(master))} "
        f"t. ! queue max-size-buffers=8 ! {_h264(SITE_BPS)} ! queue ! site. "
        f"a. ! queue ! voaacenc bitrate={SITE_AUDIO_BPS} ! queue ! site. "
        f"mp4mux name=site faststart=true ! filesink location={q(str(site))}")
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


POSTER_MAX = 200_000   # bytes


def poster(png: Path, jpg: Path) -> None:
    """The PNG as a JPEG at the best quality from 85 down that fits POSTER_MAX."""
    for q in range(85, 40, -5):
        subprocess.run(["gst-launch-1.0", "-q", "filesrc", f"location={png}", "!", "pngdec",
                        "!", "videoconvert", "!", "jpegenc", f"quality={q}", "!", "filesink",
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
