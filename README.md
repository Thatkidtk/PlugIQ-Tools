USB-C Cable Tester (MVP)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![CI](https://github.com/Thatkidtk/PlugIQ-Tools/actions/workflows/ci.yml/badge.svg)

```
▄▖▜     ▄▖▄▖  
▙▌▐ ▌▌▛▌▐ ▌▌  
▌ ▐▖▙▌▙▌▟▖█▌  
      ▄▌   ▘
```
PlugIQ Cable Tester

A cross‑platform CLI to help identify USB‑C cable capabilities and measure real‑world throughput using a connected device.

What it can do now:
- Probe system information (macOS, Linux; best‑effort on Windows) to infer cable/port capabilities like USB speeds and Thunderbolt link status.
- Run a disk throughput test against a selected mount path to estimate the effective speed through the cable.
- Classify likely cable standard from observed data (e.g., USB 2.0, USB 3.2 Gen1/Gen2, USB4/Thunderbolt).
- Save labeled results locally to track which cable is which.
- Guided wizard with safety checks and volume selection.
- Extra protocol hints: DisplayPort Alt Mode detection heuristics; Linux Type‑C cable identity when available; basic active/passive hints via Thunderbolt data.
 - Full-screen TUI on top of the wizard (`--tui`).

Limitations:
- Many OSes don’t expose full USB‑C e‑marker details publicly; some capabilities (like DP Alt Mode, passive vs active) may only be available on certain platforms (e.g., Linux typec sysfs, Thunderbolt tools). The app reports what it can find.
- Throughput tests depend on the connected device. Use a fast external SSD to avoid the device being the bottleneck.

Quick Start
===========

Requirements: Python 3.8+

Install (from source):
```
pip install .
plugiq --help
```

Run help:
```
python -m usb_cable_tester --help
```

Probe system info:
```
plugiq --show-system
```
or:
```
python -m usb_cable_tester --show-system
```

Safe guided run (recommended):
```
plugiq --wizard
```

Run a speed test against an external drive mount, label the cable, and save the result:
```
python -m usb_cable_tester --run-speed-test \
  --test-path "/Volumes/MySSD" \
  --file-size-mb 1024 \
  --label "Short white USB-C" \
  --save
```

Guided wizard (recommended):
```
python -m usb_cable_tester --wizard
```
The wizard helps you pick a safe test path (preferably an external SSD), runs preflight safety checks, offers a conservative default test size (256 MB), and lets you store the result with a label.

TUI mode:
```
plugiq --tui
```
Use arrow keys and on-screen shortcuts to navigate.

Banner style:
```
# full | compact | block
python -m usb_cable_tester --wizard --banner-style block

# or set an env var (applies to TUI/wizard)
USBCT_BANNER_STYLE=block python -m usb_cable_tester --tui
```
Default banner is the block style shown above.

Safety notes:
- macOS: Use a fast external SSD connected through the cable under test. If you have Thunderbolt, the Thunderbolt report may include link status (e.g., 40 Gb/s) and sometimes cable details.
- Linux: If your kernel exposes Type‑C sysfs (`/sys/class/typec`), the tool will parse cable identity (including active/passive and max speed) when available. `boltctl` is used when present for Thunderbolt details.
- Windows: Basic USB/Thunderbolt listing is attempted via PowerShell; depth depends on OS support.
 - The throughput test writes a temporary file to the selected path and removes it afterwards. The wizard blocks obviously unsafe targets (e.g., system root), warns when testing on internal drives, checks free space with margin, and limits default test size to reduce device wear and heat.

What PlugIQ infers vs guarantees
================================
- Some cable details (e.g., e‑marker, DP Alt Mode, active/passive) aren’t always exposed by the OS. PlugIQ reports what it can infer from system probes and observed throughput. Use a fast external SSD to avoid underestimating the cable.

Saved results format (example)
==============================
```
[
  {
    "timestamp": "2025-09-05T01:43:51.358Z",
    "label": "Short white USB-C",
    "system": { "os": "darwin", "thunderbolt": { "source": "system_profiler_json", "data": ["..."] } },
    "speed_test": { "file_size_mb": 1024, "write_mb_s": 920.1, "read_mb_s": 980.4, "path": "/Volumes/MySSD" },
    "classification": { "summary": "USB 3.2 Gen 2 (10 Gb/s)", "reasons": ["USB bus advertises up to 10 Gb/s"] }
  }
]
```

Roadmap
=======
- Add explicit DP Alt Mode detection when available per‑OS.
- Add active vs passive detection on macOS/Windows where possible.
- Add guided test flows (storage, network loopback, display) to cover more protocols.

Packaging
=========
Install from source:
```
pip install .
```
Then run `usbct --help`.

License
=======
MIT — see the LICENSE file.
