PlugIQ Tools — Agent & Contributor Guide
=======================================

Purpose
-------
- Build safe, cross‑platform tools to identify USB‑C cable capabilities and measure real‑world throughput (USB 2.0/3.x/USB4/Thunderbolt, DP Alt Mode hints).
- Prioritize user safety and clarity. Never perform destructive actions.

Safety Principles
-----------------
- Never write to system/home roots; prefer user‑selected external volumes.
- Use conservative defaults (256 MB test file) and explicit preflight checks (free space, internal/network warnings).
- Delete temporary files and sync writes explicitly.
- Avoid elevated privileges. Parse OS tools read‑only (e.g., `system_profiler`, `lsusb`, `boltctl`).

Repo Overview
-------------
- `usb_cable_tester/cli.py` — CLI entry, flags, flow control.
- `usb_cable_tester/wizard.py` — guided console wizard with safety prompts.
- `usb_cable_tester/tui.py` — curses TUI wrapper around the wizard.
- `usb_cable_tester/system_info.py` — OS‑specific probes (USB/Type‑C/TB/Display).
- `usb_cable_tester/speed_test.py` — sequential write/read benchmark.
- `usb_cable_tester/classify.py` — capability heuristics.
- `usb_cable_tester/safety.py` — preflight checks and path validation.
- `usb_cable_tester/volumes.py` — volume detection across OSes.
- `usb_cable_tester/store.py` — save labeled results to `.usb_cable_results.json`.
- `usb_cable_tester/banner.py` — ASCII banners. Default: block style.
- `tests/` — pytest suite (safety, speed, classification).

UX Guidelines
-------------
- Default banner style is `block` (can override with `--banner-style` or `USBCT_BANNER_STYLE`).
- Wizard/TUI must always explain what happens next and why; show warnings clearly.
- Keep CLI output compact by default; use `--json` for structured output.

CLI Flags (summary)
-------------------
- `--wizard` / `--tui` — interactive modes (recommended).
- `--run-speed-test --test-path <dir> [--file-size-mb N]` — one‑shot test with safety checks.
- `--show-system [--json]` — print detected capabilities.
- `--label` `--save` — tag and persist results.
- `--banner-style full|compact|block` — select banner (default: block).

Adding Probes or Heuristics
---------------------------
- Keep probes read‑only, time‑bounded, and optional (handle missing tools gracefully).
- Parse outputs defensively; avoid over‑claiming capabilities.
- Add reasons to classification so users understand conclusions.
- Prefer OS‑specific modules/sections within `system_info.py` and extend `classify.py` accordingly.

Testing & CI
------------
- Add focused tests near the logic you change.
- Run locally: `pip install -e . && pip install pytest && pytest -q`.
- CI runs on 3.8–3.12 via GitHub Actions (`.github/workflows/ci.yml`).

Release Process
---------------
- Bump `__version__` and `pyproject.toml`.
- Tag `vX.Y.Z` and push.
- Create a GitHub Release and paste notes from `RELEASE_NOTES_*.md`.
- Optional PyPI publish: configure `PYPI_API_TOKEN` secret; Release will trigger workflow.

Coding Standards
----------------
- Python 3.8+ typing (`Optional`, no `|` unions for 3.8 compat).
- Small, composable modules; prefer clarity over cleverness.
- Avoid one‑letter variables; keep functions short and explicit.

Privacy & Network
-----------------
- No telemetry or external network calls. All detection is local.
- Only read OS tooling outputs; do not store device identifiers beyond what’s needed for the session and saved results at the user’s request.

Local Dev Quick Start
---------------------
```
pip install -e .
python -m usb_cable_tester --wizard
python -m usb_cable_tester --tui
pytest -q
```

Troubleshooting
---------------
- TUI requires a TTY; on Windows without curses support, use `--wizard`.
- For macOS USB/Thunderbolt details, `system_profiler` may report limited info without devices connected.
- On Linux, richer data appears if `/sys/class/typec` and/or `boltctl` are available.
