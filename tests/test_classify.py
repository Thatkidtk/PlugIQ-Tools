from usb_cable_tester.classify import classify_result


def test_classify_by_speed_only_low():
    info = {"os": "darwin"}
    speed = {"write_mb_s": 30.0, "read_mb_s": 35.0}
    out = classify_result(info, speed)
    assert "USB 2.0" in out["summary"]


def test_classify_by_speed_only_mid():
    info = {"os": "linux"}
    speed = {"write_mb_s": 420.0, "read_mb_s": 470.0}
    out = classify_result(info, speed)
    assert "USB 3.2" in out["summary"]

