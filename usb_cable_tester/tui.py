from __future__ import annotations

import curses
import textwrap
from typing import Any, Dict, List, Optional

from .volumes import list_candidate_volumes, Volume
from .safety import preflight_checks, SafetyError
from .speed_test import run_disk_speed_test
from .classify import classify_result
from . import system_info as sysinfo
from .store import save_result
from .banner import get_banner


def run_tui(initial_info: Optional[Dict[str, Any]] = None) -> int:
    try:
        return curses.wrapper(lambda stdscr: _main(stdscr, initial_info or sysinfo.get_system_info()))
    except curses.error:
        print("TUI requires a real terminal/TTY.")
        return 2


class State:
    def __init__(self, info: Dict[str, Any]):
        self.info = info
        self.volumes: List[Volume] = list_candidate_volumes()
        self.sel_idx: int = 0
        self.custom_path: Optional[str] = None
        self.file_size_mb: int = 256
        self.warnings: List[str] = []
        self.test_path: Optional[str] = None
        self.speed: Optional[Dict[str, Any]] = None
        self.classification: Optional[Dict[str, Any]] = None
        self.label: Optional[str] = None
        self.saved_to: Optional[str] = None
        self.step: int = 0  # 0=welcome,1=vols,2=size,3=preflight,4=probe,5=test,6=results


def _draw(stdscr, title: str, body_lines: List[str], footer: str = "") -> None:
    stdscr.clear()
    maxy, maxx = stdscr.getmaxyx()
    title_line = title[: maxx - 1]
    stdscr.addstr(0, 0, title_line, curses.A_BOLD)
    y = 2
    for line in body_lines:
        for wrapped in textwrap.wrap(line, width=maxx - 2):
            if y >= maxy - 2:
                break
            stdscr.addstr(y, 1, wrapped)
            y += 1
        if y >= maxy - 2:
            break
    if footer:
        stdscr.addstr(maxy - 1, 0, footer[: maxx - 1], curses.A_REVERSE)
    stdscr.refresh()


def _format_vol(v: Volume) -> str:
    attrs = []
    if v.is_external is True:
        attrs.append("external")
    elif v.is_external is False:
        attrs.append("internal")
    if v.is_network:
        attrs.append("network")
    if v.fs_type:
        attrs.append(v.fs_type)
    prefix = f"{v.label} " if v.label else ""
    return f"{prefix}({v.mount_point})" + (" - " + ", ".join(attrs) if attrs else "")


def _input_line(stdscr, prompt: str) -> str:
    curses.echo()
    maxy, maxx = stdscr.getmaxyx()
    stdscr.addstr(maxy - 2, 0, " " * (maxx - 1))
    stdscr.addstr(maxy - 2, 0, prompt[: maxx - 2])
    stdscr.refresh()
    s = stdscr.getstr(maxy - 2, len(prompt) + 1, 512)
    curses.noecho()
    try:
        return s.decode()
    except Exception:
        return ""


def _main(stdscr, info: Dict[str, Any]) -> int:
    curses.curs_set(0)
    stdscr.nodelay(False)
    state = State(info)

    while True:
        if state.step == 0:
            body = []
            for line in get_banner().splitlines():
                body.append(line)
            body += [
                "",
                "USB-C Cable Tester — TUI Wizard",
                "",
                "Safely measure throughput via a selected volume and infer cable capabilities.",
                "A temporary file is created and removed after the test. Default size is 256 MB.",
                "",
                "Keyboard: Enter=continue, q=quit",
            ]
            _draw(stdscr, "Welcome", body, footer="Enter: Continue  •  q: Quit")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (curses.KEY_ENTER, 10, 13):
                state.step = 1

        elif state.step == 1:
            lines = ["Select a target volume (recommended: external SSD):", ""]
            if not state.volumes:
                lines.append("No volumes detected. Press 'o' to enter a path manually.")
            for i, v in enumerate(state.volumes):
                prefix = "→ " if i == state.sel_idx else "  "
                lines.append(prefix + _format_vol(v))
            lines.append("")
            lines.append("o: Other path…   Enter: Select   Up/Down: Move   q: Quit")
            _draw(stdscr, "Choose Volume", lines, footer="Up/Down • Enter=Select • o=Other • q=Quit")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (curses.KEY_UP, ord("k")):
                state.sel_idx = max(0, state.sel_idx - 1)
            elif ch in (curses.KEY_DOWN, ord("j")):
                state.sel_idx = min(max(0, len(state.volumes) - 1), state.sel_idx + 1)
            elif ch in (ord("o"), ord("O")):
                path = _input_line(stdscr, "Path: ")
                state.custom_path = path.strip() or None
                state.test_path = state.custom_path
                state.step = 2
            elif ch in (curses.KEY_ENTER, 10, 13):
                if state.volumes:
                    state.test_path = state.volumes[state.sel_idx].mount_point
                    state.step = 2

        elif state.step == 2:
            lines = [
                f"Target: {state.test_path}",
                "",
                f"Test file size: {state.file_size_mb} MB",
                "",
                "Left/Right: -/+ 50 MB   e: Edit   Enter: Continue   b: Back   q: Quit",
            ]
            _draw(stdscr, "Test Size", lines, footer="←/→ +/-50MB • e=Edit • Enter=Continue • b=Back")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (ord("b"), ord("B")):
                state.step = 1
            elif ch == curses.KEY_LEFT:
                state.file_size_mb = max(32, state.file_size_mb - 50)
            elif ch == curses.KEY_RIGHT:
                state.file_size_mb = min(8192, state.file_size_mb + 50)
            elif ch in (ord("e"), ord("E")):
                s = _input_line(stdscr, "Enter size MB: ")
                try:
                    v = int(s.strip())
                    if v > 0:
                        state.file_size_mb = min(8192, max(32, v))
                except Exception:
                    pass
            elif ch in (curses.KEY_ENTER, 10, 13):
                state.step = 3

        elif state.step == 3:
            try:
                _, warnings = preflight_checks(state.test_path or "", state.file_size_mb)
                state.warnings = warnings
                err = None
            except SafetyError as e:
                err = str(e)
            lines = [f"Target: {state.test_path}", ""]
            if err:
                lines += ["Safety check failed:", f" - {err}"]
            else:
                if state.warnings:
                    lines.append("Warnings:")
                    for w in state.warnings:
                        lines.append(f" - {w}")
                else:
                    lines.append("No warnings. Looks good.")
            lines += ["", "Enter: Continue   b: Back   q: Quit"]
            _draw(stdscr, "Safety Preflight", lines, footer="Enter=Continue • b=Back • q=Quit")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (ord("b"), ord("B")):
                state.step = 2
            elif ch in (curses.KEY_ENTER, 10, 13):
                if err:
                    state.step = 1
                else:
                    state.step = 4

        elif state.step == 4:
            # System-only probe summary
            summary = classify_result(info=state.info, speed_result=None)
            lines = [
                "Initial system probe (no writes):",
                f"Likely: {summary.get('summary')}",
            ]
            if summary.get("reasons"):
                lines.append("Reasons:")
                for r in summary["reasons"]:
                    lines.append(f" - {r}")
            lines += ["", "Enter: Run throughput test   s: Skip test   q: Quit   b: Back"]
            _draw(stdscr, "System Probe", lines, footer="Enter=Run test • s=Skip • b=Back • q=Quit")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (ord("b"), ord("B")):
                state.step = 3
            elif ch in (ord("s"), ord("S")):
                state.speed = None
                state.step = 6
            elif ch in (curses.KEY_ENTER, 10, 13):
                state.step = 5

        elif state.step == 5:
            _draw(stdscr, "Running Test", ["Running write/read throughput test..."], footer="Testing… please wait")
            stdscr.refresh()
            speed = run_disk_speed_test(test_dir=state.test_path or "", file_size_mb=state.file_size_mb)
            state.speed = speed
            state.info = sysinfo.get_system_info()
            state.step = 6

        elif state.step == 6:
            state.classification = classify_result(info=state.info, speed_result=state.speed)
            lines = []
            if state.speed:
                lines += [
                    f"Write: {state.speed['write_mb_s']:.1f} MB/s  Read: {state.speed['read_mb_s']:.1f} MB/s",
                    f"Size: {state.file_size_mb} MB  Path: {state.test_path}",
                    "",
                ]
            lines += [f"Likely: {state.classification.get('summary')}"]
            if state.classification.get("reasons"):
                lines.append("Reasons:")
                for r in state.classification["reasons"]:
                    lines.append(f" - {r}")
            lines += [
                "",
                "l: Set label   S: Save result   n: New run   q: Quit",
            ]
            _draw(stdscr, "Results", lines, footer="l=Label • S=Save • n=New • q=Quit")
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return 0
            if ch in (ord("n"), ord("N")):
                state = State(sysinfo.get_system_info())
                continue
            if ch in (ord("l"), ord("L")):
                s = _input_line(stdscr, "Cable label: ")
                state.label = s.strip() or None
            if ch in (ord("s"), ord("S")):
                entry = {
                    "label": state.label,
                    "system": state.info,
                    "speed_test": state.speed,
                    "classification": state.classification,
                }
                path = save_result(entry)
                state.saved_to = path
                _draw(stdscr, "Saved", [f"Saved to {path}", "", "Press any key to continue…"], footer="Any key…")
                stdscr.getch()

    return 0
