import time
from pathlib import Path
import serial

log_path = Path("development/bench-prep/verification/runs/2026-11-04/gate/p02-short-pulse.txt")
log_path.parent.mkdir(parents=True, exist_ok=True)

ser = serial.Serial()
ser.port = "COM3"
ser.baudrate = 115200
ser.timeout = 0.2
ser.dtr = False
ser.rts = False
ser.open()
time.sleep(0.2)

chunks = []

def take(seconds):
    end = time.time() + seconds
    while time.time() < end:
        data = ser.read(400)
        if data:
            chunks.append(data)

def text():
    return b"".join(chunks).decode("utf-8", "replace")

take(3)
ser.write(b"o")
ser.flush()
take(2)
ser.write(b"x")
ser.flush()
take(6)
ser.close()

body = text()
log_path.write_text(
    "P02 one short pulse. Sent o, then x about 2 s later. No other keys.\n" + body,
    encoding="utf-8",
)
print(body)
print("--- saved", log_path)
