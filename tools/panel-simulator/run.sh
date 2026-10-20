#!/usr/bin/env bash
# Render the panel screens on a PC, without a panel: builds the firmware screen for a "host" device with a memory
# display and takes a picture of every scene in scenes.py.
#
#   tools/panel-simulator/run.sh [output folder] [--lang nl|en|de|fr|it|es] [--size 480x480]
#
# Needs: esphome (pip install esphome; or set ESPHOME=/path/to/esphome), g++, gcc, make, git and python3 with Pillow.
# The first run downloads LVGL (the version ESPHome uses, 9.5.0) and compiles it: a few minutes. Later runs are fast.
# The pictures are what LVGL draws from the real YAML and the real vigil_panel.h; fonts and anti-aliasing match the
# panel, but colours on the real LCD can differ a little, and touch, Wi-Fi and the real clock are not simulated.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
out="${1:-$here/out}"
shift || true
work="${SIM_WORK:-$here/.work}"
esphome_bin="${ESPHOME:-esphome}"
lvgl_version="${LVGL_VERSION:-v9.5.0}"
mkdir -p "$work" "$out"
if [ ! -d "$work/lvgl-src" ]; then
  git clone --depth 1 --branch "$lvgl_version" https://github.com/lvgl/lvgl.git "$work/lvgl-src"
fi
python3 "$here/make_sim.py" "$repo/esphome/vigil_alarm" "$work" "$@"
cp "$here/Makefile.in" "$work/Makefile"
cd "$work"
"$esphome_bin" compile --only-generate sim.yaml >/dev/null
# LVGL has to be built again when its configuration changed (another widget in use, another font)
conf=".esphome/build/vigil-panel-hallway/src/lv_conf.h"
new="$(md5sum < "$conf")"
if [ "$new" != "$(cat obj/.conf 2>/dev/null || true)" ]; then rm -rf obj/lv; fi
# the generated headers (the number of components, the features in use) are not in the Makefile dependencies:
# build ESPHome's own code again when they changed, or components are silently left out
defs="$(md5sum < .esphome/build/vigil-panel-hallway/src/esphome/core/defines.h)"
if [ "$defs" != "$(cat obj/.defines 2>/dev/null || true)" ]; then rm -rf obj/esphome obj/main.o; fi
make -s -j"$(nproc)" LVGL="$work/lvgl-src"
mkdir -p obj; echo "$new" > obj/.conf; echo "$defs" > obj/.defines
rm -f shots/*; mkdir -p shots
ESPHOME_SNAPSHOT_DIR="$work/shots" timeout 120 ./sim >run.log 2>&1 || { tail -20 run.log; exit 1; }
python3 - "$work/shots" "$out" <<'PY'
import glob, os, sys
from PIL import Image
src, out = sys.argv[1:3]
for f in sorted(glob.glob(src + "/*.bmp")):
    Image.open(f).convert("RGB").save(os.path.join(out, os.path.basename(f)[:-4] + ".png"))
print("pictures in", out)
PY
