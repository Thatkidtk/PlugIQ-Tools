from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


DB_FILE = ".usb_cable_results.json"


def save_result(entry: Dict[str, Any], path: Optional[str] = None) -> str:
    target = path or os.path.join(os.getcwd(), DB_FILE)
    data = []
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if not isinstance(data, list):
                    data = []
        except Exception:
            data = []
    data.append(entry)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return target
