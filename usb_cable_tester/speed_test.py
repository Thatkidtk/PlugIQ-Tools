from __future__ import annotations

import os
import time
from typing import Dict, Any


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Directory does not exist: {path}")


def _has_space_for(path: str, size_bytes: int) -> bool:
    try:
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        return free > size_bytes * 1.2  # safety margin
    except Exception:
        return True  # Best effort


def run_disk_speed_test(test_dir: str, file_size_mb: int = 1024) -> Dict[str, Any]:
    """
    Sequential write and read test using a temporary file on the target directory.
    Returns dict with write/read MB/s and timings.
    """
    _ensure_dir(test_dir)
    file_size_bytes = file_size_mb * 1024 * 1024
    test_file = os.path.join(test_dir, ".usb_cable_tester_speed.tmp")

    if not _has_space_for(test_dir, file_size_bytes):
        raise RuntimeError("Insufficient free space for the requested file size")

    block_size = 8 * 1024 * 1024  # 8 MB blocks
    blocks = max(1, file_size_bytes // block_size)
    tail = file_size_bytes - blocks * block_size

    # Use a mixed pattern to avoid extreme CPU use while still resisting compression
    rand_block = os.urandom(min(block_size, 1024 * 1024))  # 1 MB entropy seed
    pattern = rand_block * (block_size // len(rand_block))
    zeros = b"\x00" * block_size

    write_start = time.perf_counter()
    w_bytes = 0
    try:
        with open(test_file, "wb", buffering=0) as f:
            for i in range(blocks):
                buf = pattern if i % 4 != 0 else zeros  # 3:1 mix to reduce CPU
                f.write(buf)
                w_bytes += len(buf)
            if tail:
                f.write(pattern[:tail])
                w_bytes += tail
            f.flush()
            os.fsync(f.fileno())
    finally:
        write_end = time.perf_counter()
    write_time = max(1e-9, write_end - write_start)
    write_mb_s = (w_bytes / (1024 * 1024)) / write_time

    # Read back
    read_start = time.perf_counter()
    r_bytes = 0
    try:
        with open(test_file, "rb", buffering=0) as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                r_bytes += len(chunk)
    finally:
        read_end = time.perf_counter()
        try:
            os.remove(test_file)
        except Exception:
            pass
    read_time = max(1e-9, read_end - read_start)
    read_mb_s = (r_bytes / (1024 * 1024)) / read_time

    return {
        "file_size_mb": file_size_mb,
        "block_size_bytes": block_size,
        "write_mb_s": write_mb_s,
        "write_time_s": write_time,
        "read_mb_s": read_mb_s,
        "read_time_s": read_time,
        "path": test_dir,
    }
