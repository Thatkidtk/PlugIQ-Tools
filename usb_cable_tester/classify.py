from __future__ import annotations

from typing import Any, Dict, List, Optional
import json


def _pick_speed_class(write_mb_s: Optional[float], read_mb_s: Optional[float]) -> Optional[str]:
    if write_mb_s is None and read_mb_s is None:
        return None
    best = max(v for v in [write_mb_s or 0.0, read_mb_s or 0.0])
    # Very rough mapping; device may be the bottleneck.
    # Thresholds chosen conservatively to avoid over-claiming.
    if best < 80:
        return "USB 2.0 (Hi-Speed, 480 Mb/s theoretical)"
    if best < 450:
        return "USB 3.2 Gen 1 (5 Gb/s)"
    if best < 900:
        return "USB 3.2 Gen 2 (10 Gb/s)"
    if best < 1700:
        return "USB 3.2 Gen 2x2 (20 Gb/s) or USB4/TB (20 Gb/s)"
    return "USB4 / Thunderbolt (40 Gb/s class)"


def _mac_infer(usb: Optional[Dict[str, Any]], tb: Optional[Dict[str, Any]], reasons: List[str], display: Optional[Dict[str, Any]] = None) -> Optional[str]:
    # Check Thunderbolt link status first
    if tb:
        links = []
        if tb.get("data"):
            # Search recursively for link speeds
            import json

            content = json.dumps(tb["data"]).lower()
            if "40 gb/s" in content:
                reasons.append("Thunderbolt link reports 40 Gb/s")
                return "Thunderbolt 3/4 (40 Gb/s) or USB4"
            if "20 gb/s" in content:
                reasons.append("Thunderbolt link reports 20 Gb/s")
                return "Thunderbolt / USB4 (20 Gb/s)"
        if tb.get("links"):
            lstr = " ".join(tb["links"]).lower()
            if "40 gb/s" in lstr:
                reasons.append("Thunderbolt link reports 40 Gb/s")
                return "Thunderbolt 3/4 (40 Gb/s) or USB4"
            if "20 gb/s" in lstr:
                reasons.append("Thunderbolt link reports 20 Gb/s")
                return "Thunderbolt / USB4 (20 Gb/s)"

    # USB bus advertised speeds (system_profiler text)
    if usb and usb.get("speeds"):
        text = " ".join(usb["speeds"]).lower()
        if "10 gb/sec" in text:
            reasons.append("USB bus advertises up to 10 Gb/s")
            return "USB 3.2 Gen 2 (10 Gb/s)"
        if "5 gb/sec" in text:
            reasons.append("USB bus advertises up to 5 Gb/s")
            return "USB 3.2 Gen 1 (5 Gb/s)"
        if "20 gb/sec" in text:
            reasons.append("USB bus advertises up to 20 Gb/s")
            return "USB 3.2 Gen 2x2 (20 Gb/s)"
        if "480 mb/sec" in text:
            reasons.append("USB bus advertises up to 480 Mb/s")
            return "USB 2.0 (Hi-Speed)"
    # Display hints for DP Alt Mode
    if display:
        data = display.get("data") or []
        text = json.dumps(data).lower()
        if "connection type" in text and "usb-c" in text:
            reasons.append("Display reports USB-C connection; DP Alt Mode likely")
        lines = display.get("lines") or []
        if lines:
            lstr = " ".join(lines).lower()
            if "usb-c" in lstr or "displayport" in lstr:
                reasons.append("Display profile mentions USB-C/DisplayPort; DP Alt Mode likely")
    # Thunderbolt text often includes cable hints
    if tb and tb.get("source") == "system_profiler_text" and tb.get("raw"):
        raw = str(tb.get("raw")).lower()
        if "cable" in raw:
            if "passive" in raw:
                reasons.append("Thunderbolt profiler mentions a passive cable")
            if "active" in raw:
                reasons.append("Thunderbolt profiler mentions an active cable")
    return None


def _linux_infer(usb: Optional[Dict[str, Any]], typec: Optional[Dict[str, Any]], tb: Optional[Dict[str, Any]], reasons: List[str], display: Optional[Dict[str, Any]] = None) -> Optional[str]:
    # Type-C identity if present
    if typec and typec.get("ports"):
        for p in typec["ports"]:
            c = p.get("cable") or {}
            # max speed or speed field may exist in some kernels
            for key in ("max_speed", "speed"):
                v = c.get(key)
                if v:
                    reasons.append(f"Type-C cable reports {key}={v}")
                    try:
                        n = int(v)
                        if n >= 40000:
                            return "USB4/TB (40 Gb/s)"
                        if n >= 20000:
                            return "USB 3.2 Gen 2x2 (20 Gb/s) or USB4"
                        if n >= 10000:
                            return "USB 3.2 Gen 2 (10 Gb/s)"
                        if n >= 5000:
                            return "USB 3.2 Gen 1 (5 Gb/s)"
                        if n >= 480:
                            return "USB 2.0 (480 Mb/s)"
                    except ValueError:
                        pass
            if c.get("active"):
                reasons.append(f"Cable active={c['active']}")
    # Thunderbolt sysfs/boltctl
    if tb:
        text = " ".join((" ".join(tb.get("boltctl", [])) + " " + json.dumps(tb.get("sysfs", []))) if tb else "").lower()
        if "40" in text and "gb/s" in text:
            reasons.append("Thunderbolt stack indicates 40 Gb/s")
            return "Thunderbolt 3/4 (40 Gb/s) or USB4"
        if "20" in text and "gb/s" in text:
            reasons.append("Thunderbolt stack indicates 20 Gb/s")
            return "Thunderbolt / USB4 (20 Gb/s)"
    # USB tree speeds suggest bus capability
    if usb and usb.get("lsusb_tree"):
        t = " ".join(usb["lsusb_tree"]).lower()
        if "5000m" in t or "5g" in t:
            reasons.append("USB tree shows 5000M link(s)")
            return "USB 3.2 Gen 1 (5 Gb/s)"
        if "10000m" in t or "10g" in t:
            reasons.append("USB tree shows 10000M link(s)")
            return "USB 3.2 Gen 2 (10 Gb/s)"
        if "20000m" in t or "20g" in t:
            reasons.append("USB tree shows 20000M link(s)")
            return "USB 3.2 Gen 2x2 (20 Gb/s)"
        if "480m" in t:
            reasons.append("USB tree shows 480M link(s)")
            return "USB 2.0 (480 Mb/s)"
    # DP Alt Mode hints
    if display:
        drm = display.get("drm_connectors") or []
        for c in drm:
            if (c.get("status") == "connected") and (str(c.get("connector_type")) in ("DP", "DisplayPort")):
                reasons.append("A DisplayPort connector is active; DP Alt Mode may be in use on a Type-C port")
                break
    return None


def classify_result(info: Dict[str, Any], speed_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    reasons: List[str] = []
    osname = (info.get("os") or "").lower()
    summary: Optional[str] = None

    if osname == "darwin":
        summary = _mac_infer(info.get("usb"), info.get("thunderbolt"), reasons, display=info.get("display"))
    elif osname == "linux":
        summary = _linux_infer(info.get("usb"), info.get("typec"), info.get("thunderbolt"), reasons, display=info.get("display"))

    if not summary and speed_result:
        cls = _pick_speed_class(speed_result.get("write_mb_s"), speed_result.get("read_mb_s"))
        if cls:
            reasons.append("Observed throughput suggests: " + cls)
            summary = cls

    if not summary:
        summary = "Insufficient data to classify precisely"

    return {
        "summary": summary,
        "reasons": reasons,
    }
