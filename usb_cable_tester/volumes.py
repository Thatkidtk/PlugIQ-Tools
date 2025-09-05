from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional


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


@dataclass
class Volume:
    mount_point: str
    label: Optional[str] = None
    is_external: Optional[bool] = None
    fs_type: Optional[str] = None
    is_network: Optional[bool] = None
    size_gb: Optional[float] = None
    free_gb: Optional[float] = None


def list_candidate_volumes() -> List[Volume]:
    osname = platform.system().lower()
    if osname == "darwin":
        return _mac_list_volumes()
    if osname == "linux":
        return _linux_list_volumes()
    if osname == "windows":
        return _windows_list_volumes()
    return []


def _mac_list_volumes() -> List[Volume]:
    vols: List[Volume] = []
    # Use diskutil to discover volumes and their mount points
    code, out, _ = _run("diskutil info -all")
    if code != 0 or not out:
        return vols
    current = {}
    for line in out.splitlines():
        if not line.strip():
            if current:
                mnt = current.get("Mount Point")
                if mnt and mnt != "Not Mounted":
                    is_ext = current.get("Device Location") == "External"
                    fs = current.get("Type (Bundle)") or current.get("File System Personality")
                    label = current.get("Volume Name")
                    size = _parse_size_gb(current.get("Disk Size"))
                    free = _parse_size_gb(current.get("Free Space"))
                    vols.append(Volume(mount_point=mnt, label=label, is_external=is_ext, fs_type=fs, is_network=False, size_gb=size, free_gb=free))
            current = {}
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            current[k.strip()] = v.strip()
    # Remove obvious system volumes
    filtered = []
    for v in vols:
        if v.mount_point in ("/", "/System", "/System/Volumes/Data"):
            continue
        filtered.append(v)
    return filtered


def _parse_size_gb(field: Optional[str]) -> Optional[float]:
    if not field:
        return None
    # Examples: 500.3 GB (500,277,790,720 Bytes)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*GB", field)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def _linux_list_volumes() -> List[Volume]:
    vols: List[Volume] = []
    code, out, _ = _run("lsblk -J -o NAME,TYPE,MOUNTPOINT,RM,RO,TRAN,FSTYPE,LABEL,SIZE")
    if code == 0 and out.strip():
        try:
            data = json.loads(out)
            def walk(node):
                name = node.get("name")
                mnt = node.get("mountpoint")
                if mnt:
                    rm = bool(node.get("rm"))
                    tran = (node.get("tran") or "").lower()
                    fst = node.get("fstype")
                    lbl = node.get("label")
                    size = node.get("size")
                    vols.append(Volume(mount_point=mnt, label=lbl, is_external=(rm or tran in ("usb", "thunderbolt")), fs_type=fst, is_network=(fst in ("nfs", "cifs", "smb"))))
                for ch in node.get("children", []) or []:
                    walk(ch)
            for blk in data.get("blockdevices", []) or []:
                walk(blk)
            return vols
        except Exception:
            pass
    # Fallback: parse /proc/mounts and mark as unknown
    try:
        with open("/proc/mounts", "r", encoding="utf-8") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 3:
                    mnt = parts[1]
                    fstype = parts[2]
                    if mnt.startswith("/run") or mnt.startswith("/proc") or mnt.startswith("/sys"):
                        continue
                    vols.append(Volume(mount_point=mnt, label=None, is_external=None, fs_type=fstype, is_network=(fstype in ("nfs", "cifs", "smb"))))
    except Exception:
        pass
    return vols


def _windows_list_volumes() -> List[Volume]:
    vols: List[Volume] = []
    ps = (
        "powershell -NoProfile -Command "
        "\"Get-Volume | Select DriveLetter,FileSystemLabel,DriveType,FileSystem | Format-Table -HideTableHeaders\""
    )
    code, out, _ = _run(ps)
    if code == 0 and out.strip():
        for line in out.splitlines():
            s = line.strip()
            if not s:
                continue
            parts = s.split()
            if len(parts) >= 4:
                drive, label, dtype, fstype = parts[0], parts[1], parts[2], parts[3]
                if len(drive) == 1:
                    mnt = f"{drive}:\\"
                    is_network = dtype.lower() == "network"
                    is_external = True if dtype.lower() in ("removable",) else None
                    vols.append(Volume(mount_point=mnt, label=label if label != "-" else None, is_external=is_external, fs_type=fstype, is_network=is_network))
    return vols

