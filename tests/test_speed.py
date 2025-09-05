import os
import tempfile

from usb_cable_tester.speed_test import run_disk_speed_test


def test_speed_small_file():
    with tempfile.TemporaryDirectory() as d:
        res = run_disk_speed_test(d, file_size_mb=16)
        assert res["file_size_mb"] == 16
        assert res["write_mb_s"] > 0
        assert res["read_mb_s"] > 0

