# Panel simulator

Renders the screens of the Vigil panel on a computer, without a panel: the real `vigil-panel.yaml` and the real
`vigil_panel.h`, drawn by the real LVGL, into pictures. It is how the screenshots in the handbook are made and how a
change to the look is checked before it goes to the hardware.

```
tools/panel-simulator/run.sh                    # 480x480, Dutch  -> tools/panel-simulator/out/*.png
tools/panel-simulator/run.sh out --lang en      # English (also de, fr, it, es)
tools/panel-simulator/run.sh out --size 800x480 # a wider screen (the layout follows the size)
```

Needs `esphome` (`pip install esphome`, or `ESPHOME=/path/to/esphome`), `g++`, `gcc`, `make`, `git` and Python 3 with
Pillow. The first run downloads LVGL (the version ESPHome uses) and builds it: a few minutes. After that a run takes
under a minute.

## How it works

- `make_sim.py` copies the firmware folder, replaces what a PC does not have (Wi-Fi information, the Home Assistant
  clock) and writes `sim.yaml`: an ESPHome `host` device with a memory display (`display: platform: snapshot`).
- `sim.yaml` has a script that goes through the scenes of `scenes.py`: it sets what Home Assistant would have told the
  panel (the `vigil::ctx` struct), opens the page, waits a moment and takes a picture (`snapshot.take`).
- `esphome compile --only-generate` makes the C++; `Makefile.in` builds it together with LVGL with a normal compiler.

## Add a scene

Add a line to `SCENES` in `scenes.py`: a name, the page (`main`, `keypad`, `sensors`, `info`) and the C++ that sets
`c` (the context). The pictures are numbered in the order of the list.

## What it does not show

The pictures show what LVGL draws, with the same fonts and the same layout as on the panel. They are not a photo:
the colours of the real LCD differ a little, and touch, Wi-Fi and the real clock (the simulator shows the time of the
computer) are not simulated. Memory use and speed of the ESP32 can only be seen on the panel.
