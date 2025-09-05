from __future__ import annotations

import os
from typing import Optional, Tuple
from .volumes import list_candidate_volumes


class SafetyError(Exception):
    pass


def is_path_external(test_path: str) -> Optional[bool]:
    # Best-effort: compare against known external volumes list
    candidates = list_candidate_volumes()
    for v in candidates:
        try:
            if os.path.commonpath([os.path.abspath(test_path), os.path.abspath(v.mount_point)]) == os.path.abspath(v.mount_point):
                return v.is_external
        except Exception:
            continue
    return None


def is_path_network(test_path: str) -> Optional[bool]:
    candidates = list_candidate_volumes()
    for v in candidates:
        try:
            if os.path.commonpath([os.path.abspath(test_path), os.path.abspath(v.mount_point)]) == os.path.abspath(v.mount_point):
                return v.is_network
        except Exception:
            continue
    return None


def preflight_checks(test_path: str, file_size_mb: int) -> Tuple[bool, list[str]]:
    """
    Returns (ok, warnings). Does not raise unless path is clearly unsafe.
    """
    warnings: list[str] = []
    ap = os.path.abspath(test_path)
    if not os.path.isdir(ap):
        raise SafetyError("Test path is not a directory")
    # Prevent obvious system roots
    disallowed = ["/", "/System", "/Windows", "/Users", os.path.expanduser("~")] if os.name != "nt" else [os.path.expanduser("~")]
    for bad in disallowed:
        if os.path.abspath(bad) == ap:
            raise SafetyError("Refusing to write to a system or home root directory")

    ext = is_path_external(ap)
    if ext is False:
        warnings.append("Selected path appears to be on an internal drive. Consider using an external device to avoid wear.")
    if ext is None:
        warnings.append("Could not confirm if the selected path is external. Proceed with caution.")

    net = is_path_network(ap)
    if net:
        warnings.append("Selected path appears to be a network mount; throughput will reflect network speed, not cable.")

    if file_size_mb > 8192:
        warnings.append("File size exceeds 8 GB; this may be slow and cause unnecessary wear.")
    if file_size_mb > 2048:
        warnings.append("Large test file; ensure adequate free space and device cooling.")

    # Check free space
    try:
        st = os.statvfs(ap)
        free = st.f_bavail * st.f_frsize
        if free < file_size_mb * 1024 * 1024 * 1.2:
            raise SafetyError("Insufficient free space for requested test size with safety margin")
        if free < 2 * 1024 * 1024 * 1024:
            warnings.append("Less than 2 GB free on the target volume.")
    except Exception:
        warnings.append("Could not determine free space; proceeding best-effort.")

    return True, warnings
