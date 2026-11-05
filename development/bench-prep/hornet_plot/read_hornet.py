"""
Read CG1 and CG2 from the Uno gate sketch.

Pseudocode
----------
1. Open the Uno USB port at 115200. Write nothing.
2. Wait for a line that starts with HORNET.
3. Parse CG1= and CG2=. A blank field is a missing gauge, not a pressure.
"""

from __future__ import annotations

import re
import time
from typing import Optional

import serial

DEFAULT_PORT = "COM3"
BAUD = 115200
LINE_RE = re.compile(r"HORNET CG1=(\S*) CG2=(\S*)")


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


def _field(token: str) -> Optional[float]:
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def read_pair(ser: serial.Serial, timeout_s: float = 3.0) -> tuple[Optional[float], Optional[float]]:
    """Return the next CG1, CG2 pair. None means that channel had no reading."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        match = LINE_RE.search(line)
        if match is None:
            continue
        return _field(match.group(1)), _field(match.group(2))
    raise TimeoutError("No HORNET line. The gate sketch must be the one that polls CG1 and CG2.")
