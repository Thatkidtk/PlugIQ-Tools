from __future__ import annotations

import json
import os
import platform
import re
import shlex
import subprocess
from typing import Any, Dict
import shutil


def _run(cmd: str, timeout: float = 10.0) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or ""


def _which(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def get_system_info() -> Dict[str, Any]:
    os_name = platform.system().lower()
    info: Dict[str, Any] = {"os": os_name}

    if os_name == "darwin":  # macOS
        info["usb"] = _mac_usb_info()
        info["thunderbolt"] = _mac_thunderbolt_info()
        info["display"] = _mac_display_info()
        # macOS does not generally expose Type-C cable identity; skip.
    elif os_name == "linux":
        info["usb"] = _linux_usb_info()
        info["thunderbolt"] = _linux_thunderbolt_info()
        info["typec"] = _linux_typec_info()
        info["display"] = _linux_display_info()
    elif os_name == "windows":
        info["usb"] = _windows_usb_info()
        info["thunderbolt"] = _windows_thunderbolt_info()
        info["display"] = _windows_display_info()
        # Windows Type-C identity not generally available.
    else:
        info["note"] = f"Unsupported OS: {os_name}"

    return info


# ------------------------- macOS -------------------------


def _mac_usb_info() -> Dict[str, Any]:
    # Prefer JSON output (macOS 10.13+). Fallback to text parsing.
    code, out, _ = _run("system_profiler SPUSBDataType -json")
    if code == 0:
        try:
            data = json.loads(out)
            return {"source": "system_profiler_json", "data": data.get("SPUSBDataType", [])}
        except json.JSONDecodeError:
            pass

    code, out, _ = _run("system_profiler SPUSBDataType")
    if code == 0:
        # Extract lines mentioning speed, location, product
        speeds = []
        for line in out.splitlines():
            m = re.search(r"Speed:\s*(.+)", line)
            if m:
                speeds.append(m.group(1).strip())
        return {"source": "system_profiler_text", "speeds": speeds, "raw": out[:10000]}
    return {"error": "failed to read USB info"}


def _mac_thunderbolt_info() -> Dict[str, Any]:
    # Try Thunderbolt JSON; fallback to text.
    code, out, _ = _run("system_profiler SPThunderboltDataType -json")
    if code == 0 and out.strip():
        try:
            data = json.loads(out)
            return {
                "source": "system_profiler_json",
                "data": data.get("SPThunderboltDataType", []),
            }
        except json.JSONDecodeError:
            pass
    code, out, _ = _run("system_profiler SPThunderboltDataType")
    if code == 0:
        # Extract link speeds if present
        links = []
        for line in out.splitlines():
            m = re.search(r"Link Status:\s*(.+)", line)
            if m:
                links.append(m.group(1).strip())
        return {"source": "system_profiler_text", "links": links, "raw": out[:10000]}
    return {"error": "failed to read Thunderbolt info"}


def _mac_display_info() -> Dict[str, Any]:
    code, out, _ = _run("system_profiler SPDisplaysDataType -json")
    if code == 0 and out.strip():
        try:
            data = json.loads(out)
            return {"source": "system_profiler_json", "data": data.get("SPDisplaysDataType", [])}
        except json.JSONDecodeError:
            pass
    code, out, _ = _run("system_profiler SPDisplaysDataType")
    if code == 0:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        return {"source": "system_profiler_text", "lines": lines[:256]}
    return {"error": "failed to read Displays info"}


# ------------------------- Linux -------------------------


def _linux_usb_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    code, out, _ = _run("lsusb -t")
    if code == 0:
        # Tree view with speeds
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        info["lsusb_tree"] = lines[:256]
    code, out, _ = _run("lsusb -v | head -n 200")
    if code == 0:
        info["lsusb_verbose_head"] = out
    return info


def _linux_thunderbolt_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    code, out, _ = _run("which boltctl && boltctl list")
    if code == 0 and out.strip():
        info["boltctl"] = out.splitlines()[:256]
    # Also check sysfs
    tb_root = "/sys/bus/thunderbolt/devices"
    if os.path.isdir(tb_root):
        devs = []
        for name in sorted(os.listdir(tb_root)):
            path = os.path.join(tb_root, name)
            if os.path.isdir(path):
                dev_info = {"name": name}
                for f in ("vendor_name", "device_name", "speed", "authorized", "unique_id"):
                    fp = os.path.join(path, f)
                    if os.path.exists(fp):
                        try:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                                dev_info[f] = fh.read().strip()
                        except Exception:
                            pass
                devs.append(dev_info)
        info["sysfs"] = devs[:128]
    return info


def _linux_typec_info() -> Dict[str, Any]:
    root = "/sys/class/typec"
    result: Dict[str, Any] = {}
    if not os.path.isdir(root):
        return result
    ports = []
    for entry in sorted(os.listdir(root)):
        if not entry.startswith("port"):
            continue
        ppath = os.path.join(root, entry)
        port_info: Dict[str, Any] = {"port": entry}
        # Role/status
        for f in ("power_role", "data_role", "port_type", "orientation"):
            fp = os.path.join(ppath, f)
            if os.path.exists(fp):
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        port_info[f] = fh.read().strip()
                except Exception:
                    pass
        # Cable identity
        cable_dir = os.path.join(ppath, "cable")
        if os.path.isdir(cable_dir):
            cinfo: Dict[str, Any] = {}
            identity_dir = os.path.join(cable_dir, "identity")
            if os.path.isdir(identity_dir):
                for fname in os.listdir(identity_dir):
                    fp = os.path.join(identity_dir, fname)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            cinfo[fname] = fh.read().strip()
                    except Exception:
                        pass
            for f in ("active", "plug_type", "speed", "certified"):
                fp = os.path.join(cable_dir, f)
                if os.path.exists(fp):
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            cinfo[f] = fh.read().strip()
                    except Exception:
                        pass
            if cinfo:
                port_info["cable"] = cinfo
        ports.append(port_info)
    result["ports"] = ports
    return result


def _linux_display_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    # Check DRM connectors
    root = "/sys/class/drm"
    conns = []
    try:
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                if not (name.endswith("-DP-1") or name.endswith("-DP-2") or name.startswith("card")):
                    # we'll just take all connectors with 'status'
                    pass
                path = os.path.join(root, name)
                status_fp = os.path.join(path, "status")
                if os.path.isfile(status_fp):
                    try:
                        with open(status_fp, "r", encoding="utf-8", errors="ignore") as fh:
                            status = fh.read().strip()
                    except Exception:
                        status = None
                    entry = {"name": name, "status": status}
                    ctype_fp = os.path.join(path, "connector_type")
                    if os.path.isfile(ctype_fp):
                        try:
                            with open(ctype_fp, "r", encoding="utf-8", errors="ignore") as fh:
                                entry["connector_type"] = fh.read().strip()
                        except Exception:
                            pass
                    conns.append(entry)
    except Exception:
        pass
    if conns:
        info["drm_connectors"] = conns[:64]
    # xrandr fallback
    code, out, _ = _run("xrandr --listmonitors")
    if code == 0 and out.strip():
        info["xrandr"] = out.splitlines()[:64]
    return info


# ------------------------- Windows -------------------------


def _windows_usb_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    ps = (
        "powershell -NoProfile -Command "
        "\"Get-PnpDevice -Class USB | Select-Object -Property Name,Status,InstanceId | Format-Table -HideTableHeaders\""
    )
    code, out, _ = _run(ps)
    if code == 0 and out.strip():
        info["pnp"] = out.splitlines()[:256]
    return info


def _windows_thunderbolt_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    # No universal CLI; attempt registry query via PowerShell for common vendors is out-of-scope here.
    return info


def _windows_display_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    ps = (
        "powershell -NoProfile -Command "
        "\"Get-CimInstance -Namespace root\cimv2 -ClassName Win32_DesktopMonitor | Select Name,PNPDeviceID | Format-Table -HideTableHeaders\""
    )
    code, out, _ = _run(ps)
    if code == 0 and out.strip():
        info["monitors"] = out.splitlines()[:128]
    return info
