"""
Read CG1, CG2, and the gate line from the Uno.

Pseudocode
----------
1. Open the Uno USB port at 115200.
2. Wait for a line that starts with HORNET.
3. Parse CG1 and CG2 for address 1, then A2CG1 and A2CG2.
   A blank field is a missing gauge, not a pressure.
4. On the way, keep the latest GATE line and the other Uno sentences.
"""

from __future__ import annotations

import re
import time
from typing import Optional

import serial

DEFAULT_PORT = "COM3"
BAUD = 115200
LINE_RE = re.compile(
    r"HORNET CG1=(\S*) CG2=(\S*)(?: A2CG1=(\S*) A2CG2=(\S*))?"
)
# ASK is the remembered coil. REED is only the closed switch.
GATE_RE = re.compile(
    r"GATE ASK=(OPEN|RELEASED) D8=([01]) REED=(CLOSED|NOT_CLOSED) SRC=(\S+)"
)


class UnoEar:
    def __init__(self):
        self.ask = ""
        self.d8 = ""
        self.reed = ""
        self.src = ""
        self.notes = []
        self.pending = ""
        self.cg1 = None
        self.cg2 = None
        self.a2cg1 = None
        self.a2cg2 = None
        self.fresh = False


def hear(ear, line):
    match = GATE_RE.search(line)
    if match:
        ear.ask = match.group(1)
        ear.d8 = match.group(2)
        ear.reed = match.group(3)
        ear.src = match.group(4)
    pressures = LINE_RE.search(line)
    if pressures:
        ear.cg1 = _field(pressures.group(1))
        ear.cg2 = _field(pressures.group(2))
        ear.a2cg1 = _field(pressures.group(3) or "")
        ear.a2cg2 = _field(pressures.group(4) or "")
        ear.fresh = True
    # CG lines are already plotted. Keep button, refuse, and expander sentences.
    if line.startswith("HORNET CG"):
        return
    ear.notes.append(line)
    del ear.notes[:-4]


def take_line(ser, ear, block_s):
    """One complete USB line, or "" if none arrived in time."""
    deadline = time.time() + block_s
    while True:
        if "\n" in ear.pending:
            line, ear.pending = ear.pending.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            hear(ear, line)
            return line
        waiting = ser.in_waiting
        if waiting:
            ear.pending += ser.read(waiting).decode("utf-8", errors="replace")
            continue
        if time.time() >= deadline:
            return ""
        time.sleep(0.02)


def drain(ser, ear):
    """Read whatever the Uno has already sent. Do not wait for the next pressure line."""
    while take_line(ser, ear, 0):
        pass


def open_uno(port: str) -> serial.Serial:
    """Open the Uno. Opening the port can reset the board and drop D8."""
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = BAUD
    ser.timeout = 0.2
    ser.dtr = False
    ser.rts = False
    ser.open()
    time.sleep(0.2)
    return ser


def _field(token) -> Optional[float]:
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def read_pair(ser: serial.Serial, timeout_s: float = 3.0, ear: Optional[UnoEar] = None):
    """Return addr1 CG1, addr1 CG2, addr2 CG1, addr2 CG2. None means no reading."""
    if ear is None:
        ear = UnoEar()
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        line = take_line(ser, ear, 0.05)
        if not line:
            continue
        match = LINE_RE.search(line)
        if match is None:
            continue
        return (
            _field(match.group(1)),
            _field(match.group(2)),
            _field(match.group(3) or ""),
            _field(match.group(4) or ""),
        )
    raise TimeoutError("No HORNET line. The gate sketch must be the one that polls both boxes.")
