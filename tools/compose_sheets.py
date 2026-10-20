"""Puts single screenshots together into the pictures of the guides (docs/images).

    python3 tools/compose_sheets.py touch <simulator-folder> <lang>     # 4 scenes of the panel simulator, 2 x 2
    python3 tools/compose_sheets.py card <folder-with-frames> <lang>    # phone-<lang>-<scene>.png / tablet-...

The touch panel pictures are 2 x 2 tiles of 418 pixels; the card pictures are the four scenes (not ready, keypad,
arming, alarm) side by side (phone) or 2 x 2 (tablet). Needs Pillow.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "docs/images"
TOUCH = {
    "states": ("01-disarmed", "02-not-ready", "03-arming", "08-triggered"),
    "modes": ("19-disarmed-five-modes", "20-armed-vacation", "21-armed-custom", "22-triggered-alarm24"),
    "pages": ("10-keypad-digits", "12-sensors", "13-info", "05-armed-away"),
}
CARD_SCENES = ("notready", "keypad", "arming", "alarm")
BG = (14, 17, 22)  # #0e1116, the background the card pictures are taken on


def touch(folder: Path, lang: str, out: Path = OUT) -> None:
    for name, scenes in TOUCH.items():
        sheet = Image.new("RGB", (836, 836))
        for i, scene in enumerate(scenes):
            tile = Image.open(folder / f"{scene}.png").convert("RGB").resize((418, 418), Image.LANCZOS)
            sheet.paste(tile, ((i % 2) * 418, (i // 2) * 418))
        sheet.save(out / f"touch-panel-{name}-{lang}.png", optimize=True)


def card(folder: Path, lang: str, out: Path = OUT) -> None:
    frames = {k: [Image.open(folder / f"{k}-{lang}-{s}.png").convert("RGB") for s in CARD_SCENES] for k in ("phone", "tablet")}
    sheet = Image.new("RGB", (1296, 689), BG)
    for i, f in enumerate(frames["phone"]):
        sheet.paste(f.crop((0, 0, 324, 689)), (i * 324, 0))
    sheet.save(out / f"card-phone-states-{lang}.png", optimize=True)
    sheet = Image.new("RGB", (1100, 837), BG)
    for i, f in enumerate(frames["tablet"]):
        f = f.resize((550, round(f.height * 550 / f.width)), Image.LANCZOS)
        sheet.paste(f.crop((0, 0, 550, min(f.height, 418))), ((i % 2) * 550, (i // 2) * 418))
    sheet.save(out / f"card-tablet-states-{lang}.png", optimize=True)


if __name__ == "__main__":
    kind, folder, lang = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    (touch if kind == "touch" else card)(folder, lang)
