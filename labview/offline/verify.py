"""Exercise the shipped model through the same pipe protocol used by the VI."""
from pathlib import Path
import subprocess

EXE = Path(__file__).with_name("MAIZE.Offline.exe")


class Session:
    def __init__(self):
        self.state = ""

    def scan(self, requests=0, mode=1, fault=0):
        result = subprocess.run([str(EXE)], input=f"{requests} {mode} {fault} {self.state}",
                                text=True, capture_output=True, check=True, timeout=5)
        row = result.stdout.strip().split("|")
        assert len(row) == 15 and row[11] == "1", row
        self.state = row[0]
        return row

    def arm(self, mode=1):
        self.scan(mode=mode)
        row = self.scan(16, mode)
        self.scan(mode=mode)
        return row


manual = Session()
first = manual.scan()
assert first[2:4] == ["MANUAL / Disarmed", "760 simulated Torr"] and int(first[5]) == 85
assert manual.arm()[2].endswith("Armed")
assert manual.scan(2)[12] == "Let-up OPEN command"
conflict = manual.scan(3)
assert int(conflict[10]) & 8192 and int(conflict[9]) & 8192
assert conflict[12] == "Roughing request inhibited, Let-up request inhibited"
for _ in range(12):
    manual.scan()
assert manual.arm()[2].endswith("Disarmed")
assert manual.arm()[2].endswith("Armed")
assert int(manual.scan(8)[9]) & (1 << 22)

def pumpdown(model, injected=0):
    assert model.arm(mode=2)[2].endswith("Armed")
    assert model.scan(32, mode=2)[12] == "Roughing OPEN command"
    for _ in range(95):
        row = model.scan(mode=2, fault=injected)
        if int(row[5]) >> 6 == 2 or int(row[9]):
            return row
    raise AssertionError("Pumpdown did not finish")


auto = Session()
vacuum = pumpdown(auto)
assert vacuum[2] == "AUTO / High vacuum" and vacuum[12] == "Cryo OPEN command"
assert float(vacuum[3].split()[0]) < 1
assert auto.scan(64, mode=2)[2].endswith("Preparing to vent")
vented = False
for _ in range(65):
    row = auto.scan(mode=2)
    vented |= row[12] == "Let-up OPEN command"
    if row[2] == "AUTO / Armed":
        break
assert vented and row[2] == "AUTO / Armed" and float(row[3].split()[0]) >= 700
assert int(row[5]) == 85

jammed = pumpdown(Session(), injected=12)
assert int(jammed[9]) & (1 << 25)

signal_loss = Session()
assert pumpdown(signal_loss)[2].endswith("High vacuum")
disconnected = signal_loss.scan(mode=2, fault=1)
assert int(disconnected[9]) & (1 << 21) and "command" not in disconnected[12]

print("Offline model verified: manual interlocks, re-arm, automatic pumpdown and vent, gate timeout, pressure loss.")
