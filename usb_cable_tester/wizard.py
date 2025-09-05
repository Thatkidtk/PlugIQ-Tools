from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from .volumes import list_candidate_volumes, Volume
from .safety import preflight_checks, SafetyError
from .speed_test import run_disk_speed_test
from .classify import classify_result
from .store import save_result
from . import system_info as sysinfo
from .banner import get_banner


def _prompt_yes_no(msg: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        ans = input(f"{msg} {suffix} ").strip().lower()
        if not ans:
            return default
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"): return False


def _prompt_choice(title: str, options: List[str], allow_other: bool = True) -> Optional[int]:
    print(title)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_other:
        print("  0. Other path...")
    while True:
        sel = input("Select: ").strip()
        if not sel.isdigit():
            print("Enter a number.")
            continue
        idx = int(sel)
        if allow_other and idx == 0:
            return 0
        if 1 <= idx <= len(options):
            return idx
        print("Invalid selection.")


def _format_vol(v: Volume) -> str:
    attrs = []
    if v.is_external is True: attrs.append("external")
    if v.is_external is False: attrs.append("internal")
    if v.is_network: attrs.append("network")
    if v.fs_type: attrs.append(v.fs_type)
    label = f"{v.label} " if v.label else ""
    return f"{label}({v.mount_point})" + (" - " + ", ".join(attrs) if attrs else "")


def run_wizard(initial_info: Dict[str, Any]) -> int:
    print(get_banner())
    print()
    print("USB-C Cable Tester — Guided Wizard")
    print("This wizard helps you safely test a cable by measuring throughput and checking system data.")
    print("No destructive operations are performed; a temporary file is written to the chosen path and removed after.")
    print()

    if not _prompt_yes_no("Proceed with the guided test?", default=True):
        print("Cancelled.")
        return 0

    # Refresh system info to capture current devices
    info = initial_info or sysinfo.get_system_info()

    # Step 1: Choose a target volume
    vols = list_candidate_volumes()
    options = [ _format_vol(v) for v in vols ]
    options = options[:20]
    idx = _prompt_choice("Choose a target device (recommended: external SSD connected through the cable):", options)
    test_path: Optional[str] = None
    if idx == 0:
        test_path = input("Enter a directory path on the device: ").strip()
    elif idx is None:
        print("No selection; exiting.")
        return 1
    else:
        test_path = vols[idx-1].mount_point

    if not test_path:
        print("No path provided; exiting.")
        return 1

    # Step 2: Safety checks
    default_size = 256
    print(f"Default test file size is {default_size} MB for safety.")
    if _prompt_yes_no("Increase test size for more accurate measurement?", default=False):
        while True:
            try:
                val = int(input("Enter size in MB (e.g., 1024 for 1 GB): ").strip())
                if val <= 0:
                    print("Size must be positive.")
                    continue
                if val > 2048 and not _prompt_yes_no("This is large and may cause wear/heat. Continue?", default=False):
                    continue
                file_size_mb = val
                break
            except ValueError:
                print("Enter a valid integer.")
    else:
        file_size_mb = default_size

    try:
        ok, warnings = preflight_checks(test_path, file_size_mb)
    except SafetyError as e:
        print("Safety check failed:", str(e))
        return 2

    for w in warnings:
        print("Warning:", w)
    if warnings and not _prompt_yes_no("Acknowledge warnings and continue?", default=False):
        print("Cancelled by user.")
        return 0

    # Step 3: Optional system-only check
    if _prompt_yes_no("Run a system-only probe first (no writes)?", default=True):
        summary = classify_result(info=info, speed_result=None)
        print("System says:", summary.get("summary"))
        for r in summary.get("reasons", []):
            print(" -", r)

    # Step 4: Throughput test
    if not _prompt_yes_no("Run the write/read throughput test now?", default=True):
        print("Skipped throughput test.")
        speed = None
    else:
        print("Testing... this may take a moment.")
        speed = run_disk_speed_test(test_dir=test_path, file_size_mb=file_size_mb)
        print(f"Write: {speed['write_mb_s']:.1f} MB/s, Read: {speed['read_mb_s']:.1f} MB/s")

    # Step 5: Classification and optional save
    info2 = sysinfo.get_system_info()  # recapture in case link changed under load
    summary2 = classify_result(info=info2, speed_result=speed)
    print("Likely:", summary2.get("summary"))
    if summary2.get("reasons"):
        print("Why:")
        for r in summary2["reasons"]:
            print(" -", r)

    label = input("Optional: enter a label/name for this cable: ").strip() or None
    if _prompt_yes_no("Save this result to .usb_cable_results.json?", default=True):
        entry = {
            "label": label,
            "system": info2,
            "speed_test": speed,
            "classification": summary2,
        }
        path = save_result(entry)
        print("Saved to", path)

    print("Done. Unplug/replug another cable and run the wizard again to compare.")
    return 0
