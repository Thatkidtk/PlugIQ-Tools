import os
import tempfile

import pytest

from usb_cable_tester.safety import preflight_checks, SafetyError


def test_refuse_system_root():
    root = os.path.abspath(os.sep)
    with pytest.raises(SafetyError):
        preflight_checks(root, 10)


def test_temp_dir_ok_small():
    with tempfile.TemporaryDirectory() as d:
        ok, warnings = preflight_checks(d, 32)
        assert ok is True
        assert isinstance(warnings, list)

