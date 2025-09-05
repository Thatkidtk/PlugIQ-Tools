import argparse
import json
import os
from datetime import datetime
from typing import Optional

from . import __version__
from . import system_info as sysinfo
from .speed_test import run_disk_speed_test
from .classify import classify_result
from .store import save_result


def _human_mb_s(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:.1f} MB/s"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="USB-C Cable Tester: probe system and measure throughput to infer cable capabilities.",
    )
    parser.add_argument("--version", action="version", version=f"usb-cable-tester {__version__}")

    parser.add_argument("--show-system", action="store_true", help="Print detected USB/Type-C/Thunderbolt info and exit")
    parser.add_argument("--run-speed-test", action="store_true", help="Run a disk throughput test on the provided path")
    parser.add_argument("--test-path", type=str, default=None, help="Directory path on the target device (e.g., external SSD mount)")
    parser.add_argument("--file-size-mb", type=int, default=1024, help="Test file size in MB (default 1024)")
    parser.add_argument("--label", type=str, default=None, help="Optional human-friendly cable label to store with results")
    parser.add_argument("--save", action="store_true", help="Save results to .usb_cable_results.json in this folder")
    parser.add_argument("--json", action="store_true", help="Output JSON for programmatic use")
    parser.add_argument("--wizard", action="store_true", help="Run the guided test wizard with safety checks")
    parser.add_argument("--dry-run", action="store_true", help="Do not write any data; show what would happen")
    parser.add_argument("--tui", action="store_true", help="Launch the full-screen TUI (curses) on top of the wizard")
    banner_default = os.environ.get("USBCT_BANNER_STYLE", "full")
    parser.add_argument("--banner-style", choices=["full", "compact", "block"], default=banner_default, help="Select banner style for wizard/TUI")

    args = parser.parse_args()

    info = sysinfo.get_system_info()

    if args.show_system and not args.run_speed_test:
        if args.json:
            print(json.dumps({"system": info}, indent=2))
        else:
            print("OS:", info.get("os"))
            if info.get("usb"):
                print("\nUSB Info:")
                print(json.dumps(info["usb"], indent=2))
            if info.get("thunderbolt"):
                print("\nThunderbolt Info:")
                print(json.dumps(info["thunderbolt"], indent=2))
            if info.get("typec"):
                print("\nType-C Info:")
                print(json.dumps(info["typec"], indent=2))
        return 0

    # TUI or wizard flow short-circuits; they run their own prompts
    if args.tui:
        try:
            from .tui import run_tui
        except Exception as e:
            print("Failed to start TUI:", e)
            return 2
        return run_tui(initial_info=info, banner_style=args.banner_style)

    # Wizard flow
    if args.wizard:
        from .wizard import run_wizard

        return run_wizard(initial_info=info, banner_style=args.banner_style)

    speed_result = None
    if args.run_speed_test:
        if not args.test_path:
            parser.error("--test-path is required with --run-speed-test")
        # Safety checks
        if not args.dry_run:
            from .safety import preflight_checks, SafetyError
            try:
                ok, warnings = preflight_checks(args.test_path, args.file_size_mb)
            except SafetyError as e:
                parser.error(str(e))
            for w in warnings:
                print("Warning:", w)
        if args.dry_run:
            speed_result = {
                "file_size_mb": args.file_size_mb,
                "path": args.test_path,
                "dry_run": True,
            }
        else:
            speed_result = run_disk_speed_test(
                test_dir=args.test_path,
                file_size_mb=args.file_size_mb,
            )

    result = classify_result(info=info, speed_result=speed_result)
    now_iso = datetime.utcnow().isoformat() + "Z"

    out = {
        "timestamp": now_iso,
        "label": args.label,
        "system": info,
        "speed_test": speed_result,
        "classification": result,
    }

    if args.save:
        save_path = save_result(out)
        out["saved_to"] = save_path

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print("When:", now_iso)
        if args.label:
            print("Label:", args.label)
        if speed_result:
            print(
                f"Write: {_human_mb_s(speed_result.get('write_mb_s'))}, "
                f"Read: {_human_mb_s(speed_result.get('read_mb_s'))} "
                f"(file ~{speed_result.get('file_size_mb')} MB)"
            )
        if result:
            print("Likely:", result.get("summary") or "-")
            if result.get("reasons"):
                print("Why:")
                for r in result["reasons"]:
                    print(" -", r)
        if out.get("saved_to"):
            print("Saved:", out["saved_to"])

    return 0
