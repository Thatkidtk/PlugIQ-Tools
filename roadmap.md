Here’s a polished, GitHub-ready ROADMAP.md you can drop into the repo. It frames PlugIQ as a modular, cross-platform I/O intelligence suite, includes a clean milestone plan, CLI/TUI structure, testing/CI, and sample AI config scaffolding (for OpenAI/“codex”-style models and Claude) you can keep in ai/ for future helpers.

⸻

PlugIQ Toolkit — Roadmap

Tagline: Cross-platform I/O intelligence suite for cables, ports, docks, and throughput.

PlugIQ starts with a smart USB-C cable tester and grows into a focused toolkit for verifying claims, mapping bottlenecks, and labeling your gear with evidence. Everything is CLI/TUI-first, scriptable, and safe by default.

⸻

0. Guiding Principles
   • Evidence over vibes: Prefer measurable signals (descriptors, link speed, EDID, PD profiles, iperf/fio runs). Clearly separate inferred vs guaranteed capabilities.
   • Cross-platform, best-effort: macOS, Linux, Windows. If an OS hides details, say so loudly and degrade gracefully.
   • Safety first: Never write to internal system volumes by default. Use temp dirs; show preflight checks; confirm destructive ops.
   • Human + machine UX: Rich CLI/TUI with --json for automation and --diagnostics for explainability.
   • Reproducibility: Deterministic benchmarks, pinned workloads, and a minimal test matrix captured in artifacts.

⸻

1. Core Modules (v1.x → v2.x)

✅ M1 — USB-C Cable Tester (current)
• Detect/Infer: USB speed tier (USB 2.0 → USB4/TB), TB link status, limited e-marker hints (when available), DisplayPort Alt Mode heuristics, active/passive hints via TB data (platform-dependent).
• Measure: Disk throughput on a chosen mount path with safety checks; save labeled results.
• UX: Wizard + full-screen TUI (--wizard, --tui).
• Output: Human-readable + --json dump; local results DB (see §5).

🚧 M2 — PowerIQ (USB-PD Inspector)
• Parse/display USB-Power Delivery capabilities where surfaced (Linux typec/ sysfs; selected controllers on macOS/Windows when accessible).
• Report source/ sink profiles, PPS support (voltage/current ranges), negotiated contract if available.
• CLI: plugiq pd --list, plugiq pd --monitor, plugiq pd --details <port>

🚧 M3 — PortMap (Topology & Bandwidth Map)
• Map USB host controllers, TB/USB4 fabrics, PCIe lanes for NVMe, and port ownership.
• Identify shared bandwidth domains (e.g., two ports on same controller).
• CLI: plugiq portmap --tree, plugiq portmap --json, plugiq portmap --watch

🚧 M4 — DockIQ (Dock/Hub Profiler)
• Enumerate dock functions: downstream USB, NICs, audio, display paths.
• Detect likely bottlenecks (e.g., USB3 x1 lane shared by NIC + SSD).
• Quick stress micro-benchmarks (USB storage, NIC throughput smoke).
• CLI: plugiq dock --profile, plugiq dock --bench quick

🚧 M5 — DisplayIQ (EDID & Mode Verifier)
• Read EDID; report max resolution/refresh, color formats, DSC, HDR flags.
• Attempt a temporary mode set + revert (“does this mode actually work?”) where safe/allowed.
• CLI: plugiq display --edid, plugiq display --modes, plugiq display --verify 4k120

🚧 M6 — NetBlast (Network Throughput)
• iperf3 wrapper + native sockets fallback; LAN/Wi-Fi quick tests.
• Peer role: client/server with QR code to simplify pairing.
• CLI: plugiq net --server, plugiq net --client HOST --duration 10 --json

🚧 M7 — DiskBurn (Drive Benchmark)
• Standalone storage tester (sequential/4k random; read/write; file or raw device with explicit opt-in).
• Profiles compatible with fio-like semantics.
• CLI: plugiq disk --profile quick|full --path /mnt/ssd --json

🚧 M8 — Hotplug Monitor
• Real-time attach/detach event stream; optional logging; flakiness tracker.
• CLI/TUI: plugiq watch --usb, plugiq watch --thunderbolt, plugiq watch --typec

🚀 Stretch — Latency Lab & EMI Sniffer
• Latency Lab: simple device polling/ping jitter for peripherals over hubs.
• EMI Sniffer: optional SDR integration to compare shielding quality (advanced users).

⸻

2. CLI/TUI Structure

plugiq
├─ cable # current USB-C tester (alias: plugiq usb)
├─ pd # PowerIQ (USB-PD)
├─ portmap # topology mapping
├─ dock # dock/hub profiler
├─ display # EDID/mode verification
├─ net # iperf3-like
├─ disk # storage benchmark
├─ watch # hotplug monitor
├─ wizard # guided flow across modules
└─ about / doctor / version

Common flags: --json, --diagnostics, --quiet, --log-level, --save, --label, --tui.
TUI: footer hints (←/→ tabs ↑/↓ select Enter run Q quit), mini-banner, progress bars/sparklines.

⸻

3. Platform Support Matrix (living doc)

Module Linux macOS Windows Notes
cable ✅ ✅ 🟡 Windows: limited descriptor/PD access; be explicit about gaps
pd ✅ 🟡 🟡 Linux typec sysfs; macOS/Win best-effort
portmap ✅ ✅ ✅ Data richness varies; prefer --diagnostics
dock ✅ ✅ ✅ Subject to OS/driver visibility
display ✅ ✅ ✅ EDID access differs; mode-set verification gated by safety
net ✅ ✅ ✅ iperf3 recommended; fallback available
disk ✅ ✅ ✅ Raw device ops require explicit opt-in
watch ✅ ✅ 🟡 Event feeds vary on Windows

Legend: ✅ full; 🟡 partial/best-effort.

⸻

4. Safety & Reproducibility
   • Preflight: confirm target path is removable/explicit; show planned file sizes; dry-run mode.
   • Caps & disclaimers: clearly mark inferred vs guaranteed results.
   • Profiles: store test profiles (quick, balanced, full) with fixed sizes and durations.
   • Artifacts: save raw logs + JSON results alongside human summary.

⸻

5. Data & Results

Directory: ~/.config/plugiq/ (Linux/macOS) or %APPDATA%\PlugIQ\ (Windows).
• results/ — JSON records per run
• labels/ — cable/device labels (ID ↔ human name)
• profiles/ — benchmark profiles
• log/ — module logs

Result schema (example):

{
"module": "cable",
"version": "1.1.0",
"timestamp": "2025-09-05T18:35:11Z",
"host": {"os":"Linux","kernel":"6.9","cpu":"12th Gen..."},
"port": {"controller":"xHCI","tb_link":"active","usb_gen":"USB 3.2 Gen2"},
"cable": {"label":"Desk_TB4_0.8m","length_m":0.8,"inference":"USB4/TB4 (inferred)"},
"tests": {
"disk": {"path":"/mnt/t7","profile":"quick","write_MBps":912,"read_MBps":1046}
},
"notes": "DP Alt Mode likely; PD 20V/5A advertised (Linux typec)"
}

⸻

6. Packaging & Commands
   • Binary name: plugiq (optional alias usbct for cable subcmd).
   • Install: pipx install . or pip install .
   • Entry points: [project.scripts] plugiq = "plugiq.**main**:main"

⸻

7. Testing & CI
   • Unit tests: classification logic, parsers (EDID, PD, TB), safety checks.
   • Fixture sims: synthetic sysfs/IOReg/Device Manager snapshots to test platform logic.
   • Smoke tests: parse flags, dry-run flows, JSON output validity.
   • Benchmark harness: optional nightly “hardware lab” run (self-hosted runner) with a known SSD/cable set.
   • CI: GitHub Actions
   • lint (ruff/flake8), type (mypy/pyright), test (pytest), build (wheel/sdist)
   • Release workflow on tag → PyPI + GitHub Release artifacts.

⸻

8. Documentation
   • User Guide: install, quickstart, common flows per module, OS caveats.
   • Capability Matrix: which OS exposes what (update as APIs evolve).
   • Troubleshooting: permissions, missing tools (iperf3), device quirks.
   • Examples: “Verify a 100W cable,” “Check 4K120 HDR path,” “Find a dock bottleneck.”

⸻

9. Security & Privacy
   • Local-only by default.
   • No telemetry unless explicit --opt-in-telemetry. If added: anonymized metrics, clear toggle, documented schema.
   • Log redaction for serials where appropriate.

⸻

10. Milestones & Releases
    • v1.1.0: --json, diagnostics mode, improved labels DB, entrypoint plugiq.
    • v1.2.0: PowerIQ (PD), baseline PortMap.
    • v1.3.0: DockIQ profile + quick benches.
    • v1.4.0: DisplayIQ EDID/mode verify.
    • v2.0.0: Unified wizard across modules, history dashboard TUI.

Semantic versioning. Keep CHANGELOG.md current. Release candidates for big module drops.

⸻

11. Repo Layout (proposed)

PlugIQ-Tools/
├─ plugiq/ # python package (namespace)
│ ├─ **init**.py
│ ├─ **main**.py # CLI router (Typer/argparse)
│ ├─ cable/ # M1: USB-C tester
│ ├─ pd/ # M2: PowerIQ
│ ├─ portmap/ # M3
│ ├─ dock/ # M4
│ ├─ display/ # M5
│ ├─ net/ # M6
│ ├─ disk/ # M7
│ ├─ watch/ # M8
│ ├─ tui/ # Shared TUI widgets (Rich/Textual)
│ ├─ core/ # shared utils: os probes, parsers, io, profiles
│ └─ data/ # static resources (EDID samples, icons)
├─ tests/
│ ├─ unit/
│ ├─ fixtures/ # sysfs/IOReg/DM snapshots
│ └─ smoke/
├─ ai/ # assistant configs (optional; see below)
│ ├─ openai.config.example.json
│ ├─ claude.config.example.json
│ └─ prompts/
├─ docs/
├─ scripts/
├─ pyproject.toml
├─ README.md
├─ ROADMAP.md
└─ CHANGELOG.md

⸻

12. Assistant Configs (Optional Helpers)

Keep these as examples so devs can wire in local scripts that ask an assistant to, say, draft a new parser or generate tests from samples. Store API keys via env only.

ai/openai.config.example.json

{
"provider": "openai",
"model": "gpt-4o-mini",
"endpoint": "https://api.openai.com/v1",
"temperature": 0.2,
"max_tokens": 1200,
"system_prompt": "You are PlugIQ's code copilot. Generate minimal, typed Python, add tests, and never invent OS capabilities. If a platform hides a field, mark it as inferred or unsupported."
}

ai/claude.config.example.json

{
"provider": "anthropic",
"model": "claude-3-5-sonnet-latest",
"endpoint": "https://api.anthropic.com",
"temperature": 0.2,
"max_tokens": 1200,
"system_prompt": "You are PlugIQ's code copilot. Prefer deterministic outputs, small diffs, and precise comments. If uncertain, emit TODO with a reproducible probe."
}

Minimal prompt template (shared), ai/prompts/generate_parser.md:

Task: Implement a parser for <SOURCE> that extracts <FIELDS>.
Constraints:

- No network calls.
- Do not assume fields if not present; return None and add a note to diagnostics.
- Provide unit tests using fixtures in tests/fixtures/<SOURCE>.
  Output:

1. parser code (Python)
2. tests
3. update to core diagnostics docstring summarizing signals and caveats

Env usage pattern (pseudo):

export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
python scripts/ai_helper.py --provider openai --task prompts/generate_parser.md

(Ship these as examples; keep helpers opt-in to avoid bundling any vendor code.)

⸻

13. Bench & Methodology (Appendix)
    • Disk: file-backed tests sized to exceed device cache; record temp/FS info.
    • Net: fixed duration (≥10s), warm-up 2s, pin CPU governor where possible.
    • Display: EDID parse first; mode-set attempts behind --allow-mode-switch.
    • PD: poll cadence documented; show last negotiated profile vs advertised menu.

⸻

14. Branding Bits
    • Binary: plugiq
    • Mini banner: 🔌⚡ PlugIQ
    • ASCII banner: the large one you’re using for full screens / README top.
    • Labels: export to text/QR; optional CSV for lab inventory.

⸻

Immediate Next Steps 1. Add plugiq entrypoint and --json/--diagnostics to the current cable module. 2. Stand up PortMap skeleton (tree view + JSON dump) to unify diagnostics across modules. 3. Drop the ai/ config examples and ROADMAP.md into the repo. 4. Add CI: lint/type/test/build on PR; tag-based release packaging.

When you’re ready, I can generate: a Typer-based **main**.py router with subcommands stubbed, a PortMap skeleton that compiles on all three OSes, and a minimal GitHub Actions workflow wired to pytest + ruff.
