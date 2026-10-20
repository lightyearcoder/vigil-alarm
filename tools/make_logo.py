"""Recolours the Vigil logo to the blue of the "Home" icon as seen on the panel (#6897E6) and writes the 30x30 logo of the panel firmware.

    python3 tools/make_logo.py recolor <old-icon-folder>   # brand/*.png from the original blue icons
    python3 tools/make_logo.py header                      # esphome/vigil_alarm/vigil_logo.h from brand/icon@2x.png

The recolouring keeps the white shield and the shading; only the blue changes (the gradient of the background
and the darker eye). Needs Pillow.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "custom_components/vigil_alarm/brand"
HOME_BLUE = (104, 151, 230)  # the Home icon as it looks on the panel (COL_HOME 0x5B9BF0 on the real screen)
EYE_BLUE = (0x2F, 0x66, 0xB8)
# the old gradient ran from (46, 108, 215) at the top to (28, 66, 148) at the bottom; (37, 87, 181) is its middle
OLD_MID, OLD_EYE = (37, 87, 181), (27, 63, 143)
SHADE = 0.5  # how much of the old top-to-bottom shading is kept


def _scales(old, new):
    # distance from white per channel: the antialiased edges against the white shield are mixes with white, and
    # scaling that distance keeps them correct
    return [(255 - n) / (255 - o) for o, n in zip(old, new)]


def recolor(src: Image.Image) -> Image.Image:
    bg, eye = _scales(OLD_MID, HOME_BLUE), _scales(OLD_EYE, EYE_BLUE)
    w, h = src.size
    out = src.convert("RGBA")
    px = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            fx, fy = x / w, y / h
            inside_eye = ((fx - 0.5) / 0.21) ** 2 + ((fy - 0.53) / 0.15) ** 2 < 1 and b <= 190 and r < 120
            s = eye if inside_eye else bg
            new = [255 - (255 - c) * k for c, k in zip((r, g, b), s)]
            if not inside_eye and (r, g, b) != (255, 255, 255):
                # a flatter gradient: pull the shading towards the middle colour, so the logo is the blue of the icon
                new = [m + (v - m) * SHADE for v, m in zip(new, HOME_BLUE)]
            px[x, y] = tuple(max(0, min(255, round(v))) for v in new) + (a,)
    return out


def header(icon: Image.Image) -> str:
    size = 30
    small = icon.convert("RGBA").resize((size, size), Image.LANCZOS)
    rgb, alpha = bytearray(), bytearray()
    for r, g, b, a in small.getdata():
        v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        rgb += bytes((v & 0xFF, v >> 8))
        alpha.append(a)
    data = bytes(rgb + alpha)
    rows = [", ".join(f"0x{c:02X}" for c in data[i:i + 24]) + "," for i in range(0, len(data), 24)]
    return "\n".join("    " + r for r in rows)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "recolor":
        old = Path(sys.argv[2])
        for name in ("icon.png", "icon@2x.png", "dark_icon.png", "dark_icon@2x.png"):
            recolor(Image.open(old / name)).save(BRAND / name, optimize=True)
    elif mode == "header":
        path = ROOT / "esphome/vigil_alarm/vigil_logo.h"
        text = path.read_text()
        start = text.index("LOGO_DATA[] = {") + len("LOGO_DATA[] = {")
        end = text.index("};", start)
        path.write_text(text[:start] + "\n" + header(Image.open(BRAND / "icon.png")) + "\n" + text[end:])
