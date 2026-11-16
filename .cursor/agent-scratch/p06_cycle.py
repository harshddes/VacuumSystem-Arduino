import time
from pathlib import Path
import serial

log_path = Path("development/bench-prep/verification/runs/2026-11-04/gate/p06-two-cycles.txt")
log_path.parent.mkdir(parents=True, exist_ok=True)

ser = serial.Serial("COM3", 115200, timeout=0.2)
lines = []
notes = []

def pump(seconds):
    end = time.time() + seconds
    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", "replace").rstrip()
        lines.append(f"{time.time():.3f} {line}")
        print(line)

def wait_online(limit=8):
    end = time.time() + limit
    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", "replace").rstrip()
        lines.append(f"{time.time():.3f} {line}")
        print(line)
        if "MCP ONLINE" in line:
            return True
    return False

def closed_bit(line):
    if "CLOSED=" not in line:
        return None
    return line.split("CLOSED=")[1][0]

def wait_closed(want, limit):
    start = time.time()
    end = start + limit
    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", "replace").rstrip()
        stamp = time.time()
        lines.append(f"{stamp:.3f} {line}")
        print(line)
        bit = closed_bit(line)
        if bit == want:
            return stamp - start
    return None

if not wait_online():
    notes.append("MCP did not come online")
else:
    time.sleep(1.5)
    pump(1.5)
    for n in (1, 2):
        ser.write(b"o")
        ser.flush()
        t_open = wait_closed("0", 12)
        notes.append(f"cycle {n} open command to CLOSED=0: {t_open}")
        time.sleep(2)
        pump(0.2)
        ser.write(b"c")
        ser.flush()
        t_close = wait_closed("1", 12)
        notes.append(f"cycle {n} release to CLOSED=1: {t_close}")
        time.sleep(2)
        pump(0.2)

ser.close()
body = "\n".join(notes) + "\n\n" + "\n".join(lines) + "\n"
log_path.write_text(body, encoding="utf-8")
print("---")
print("\n".join(notes))
print("--- saved", log_path)
