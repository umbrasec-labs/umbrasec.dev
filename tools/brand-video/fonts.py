"""The film's fonts, kept inside this folder.

Downloads Inter Tight and JetBrains Mono (both OFL) from Google Fonts once into
.cache/fonts and writes a private fontconfig file that lists them first. The
render then matches the site's fonts and never reads or writes the fonts or
caches in the home folder. Callers set FONTCONFIG_FILE to the returned path
before PangoCairo loads.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
FONT_DIR = CACHE / "fonts"
CONF = CACHE / "fonts.conf"
CSS_URL = ("https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600"
           "&family=JetBrains+Mono:wght@400;500")
# A plain client name: for a client it does not know, the API answers with
# whole TTF files instead of browser subsets.
USER_AGENT = "umbrasec-brand-video/1.0"
WANTED = {("Inter Tight", 400), ("Inter Tight", 500), ("Inter Tight", 600),
          ("JetBrains Mono", 400), ("JetBrains Mono", 500)}

_FACE = re.compile(r"@font-face\s*{(.*?)}", re.S)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _faces(css: str) -> list[tuple[str, int, str]]:
    out = []
    for block in _FACE.findall(css):
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
        url = re.search(r"src:\s*url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)", block).group(1)
        out.append((family, weight, url))
    return out


def _file_name(family: str, weight: int) -> str:
    return f"{family.replace(' ', '')}-{weight}.ttf"


def _conf_text() -> str:
    return f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<!-- Written by tools/brand-video/fonts.py. The film's fonts first, the
     system fonts only as a fallback for glyphs they lack. -->
<fontconfig>
  <dir>{FONT_DIR}</dir>
  <dir>/usr/share/fonts</dir>
  <cachedir>{CACHE / "fc"}</cachedir>
</fontconfig>
"""


def ensure_fonts() -> Path:
    """Download the fonts if they are missing and return the private fonts.conf."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    missing = [fw for fw in sorted(WANTED) if not (FONT_DIR / _file_name(*fw)).is_file()]
    if missing:
        faces = {(f, w): url for f, w, url in _faces(_get(CSS_URL).decode())}
        for fw in missing:
            if fw not in faces:
                raise RuntimeError(f"Google Fonts did not offer {fw[0]} {fw[1]} as TTF")
            data = _get(faces[fw])
            if data[:4] not in (b"\x00\x01\x00\x00", b"true"):
                raise RuntimeError(f"{fw[0]} {fw[1]}: the download is not a TrueType file")
            (FONT_DIR / _file_name(*fw)).write_bytes(data)
    text = _conf_text()
    if not CONF.is_file() or CONF.read_text() != text:
        CONF.write_text(text)
    return CONF
