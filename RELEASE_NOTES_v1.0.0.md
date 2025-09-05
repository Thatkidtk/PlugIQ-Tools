# USB-C Cable Tester v1.0.0

First stable release with CLI + TUI, safety preflights, and cross‑platform probes.

Highlights
- CLI and full‑screen curses TUI (`--tui`) on top of a guided wizard.
- Safety preflight checks: blocks system/home roots, checks free space, warns for internal and network mounts.
- Throughput test with temporary file (fsync + cleanup).
- System probes: USB, Thunderbolt/USB4, Linux Type‑C cable identity, macOS display info (DP Alt Mode hints), Linux DRM connectors.
- Classification heuristics: USB 2.0, 3.2 Gen1/Gen2/2x2, USB4/Thunderbolt; DP Alt Mode hints.
- Results history persisted to `.usb_cable_results.json` with optional labels.

Install from source:
```
pip install .
```

Usage
```
usbct --help
usbct --tui
usbct --wizard
usbct --show-system --json
usbct --run-speed-test --test-path "/Volumes/MySSD" --file-size-mb 1024 --label "Short white USB-C" --save
```

Notes
- Use a fast external SSD to avoid the device being the bottleneck.
- Linux with `/sys/class/typec` and `boltctl` provides deeper cable/Thunderbolt insights.
- TUI requires a real terminal/TTY.
