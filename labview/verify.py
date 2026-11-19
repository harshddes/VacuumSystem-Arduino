"""Hardware-free checks of the worker shipped beside the LabVIEW VI.

With --fixture, serve sample replies on loopback for testing the native VI's Ethernet mode.
"""
import argparse
import csv
from pathlib import Path
import re
import socket
import subprocess
import threading

WORKER = Path(__file__).with_name("MAIZE.Telemetry.exe")
ADDRESS = ("127.0.0.1", 44820)
NEUTRAL = 5 << 14  # two CLOSED switches, neither OPEN


def tick(flags, previous="", host="127.0.0.1"):
    proc = subprocess.run([str(WORKER)], input=f"{flags}\t{host}\t{previous}",
                          text=True, capture_output=True, timeout=5, check=True)
    columns = proc.stdout.split("|")
    assert len(columns) == 18, proc.stdout
    return columns


def sample(nonce, seq, *, gates=5, e1_ok=1, pressure="0.0004", unit="TORR", age=100, mapped=1):
    return (f"MAIZE2,{nonce},{seq},{seq * 100},{gates},{e1_ok},64656,2,1,"
            f"LOOPBACK_FIXTURE,{pressure},{unit},{age},NONE,{mapped}")


def serve(sock, replies=None):
    seq = 1
    while replies is None or seq <= len(replies):
        data, peer = sock.recvfrom(512)
        match = re.fullmatch(rb"MAIZE2 R ([0-9a-f]{8})\n", data)
        if match is None:
            continue
        nonce = match.group(1).decode("ascii")
        reply = sample(nonce, seq) if replies is None else replies[seq-1](nonce, seq)
        sock.sendto(reply.encode("ascii"), peer)
        seq += 1


def verify():
    state = tick(NEUTRAL)
    assert "SIMULATION" in state[1] and state[3] == "NaN"
    assert all(row.startswith("CLOSED") for row in state[7:9])
    state = tick(NEUTRAL | 8, state[0])
    assert "DRY_IO_ARMED" in state[5]
    state = tick(NEUTRAL | 128, state[0])
    assert "R1 ON" in state[10] and state[7].startswith("CLOSED") and state[8].startswith("CLOSED")
    state = tick(NEUTRAL | 128 | 2048, state[0])
    assert state[6] == "AIR_LOSS" and "R1 OFF" in state[10]
    state = tick(NEUTRAL | 128, state[0])
    assert state[6] == "AIR_LOSS" and "R1 OFF" in state[10]
    state = tick(NEUTRAL | 8, state[0])
    assert state[6] == "NONE"
    for bits in range(16):
        state = tick(bits << 14)
        for idx, raw in enumerate((bits & 3, bits >> 2)):
            assert state[7+idx].startswith(("NO PROOF", "CLOSED", "OPEN", "CONFLICT")[raw])
    state = tick(NEUTRAL | 4)
    state = tick(NEUTRAL | 4 | 8, state[0])
    state = tick(NEUTRAL | 4 | 32, state[0])
    assert state[6] == "PATH_MAP_AND_PROOF_UNKNOWN" and " ON" not in state[10]
    state = tick(NEUTRAL | 8192, state[0])
    assert state[3] == "NaN" and state[4] == "UNAVAILABLE / STALE"

    replies = [
        lambda n,i: sample(n,i,gates=6),  # cryo open, turbo closed
        lambda n,i: sample(n,i,e1_ok=0),
        lambda n,i: sample(n,i,pressure="1100"),
        lambda n,i: sample(n,i,age=2100),
        lambda n,i: sample(n,i,unit="NATIVE"),
        lambda n,i: sample(n,i,mapped=0),
        lambda n,i: sample(n,i-1),       # stale controller sequence
        lambda n,i: sample("ffffffff" if n!="ffffffff" else "00000000",i),
        lambda n,i: sample(n,i,pressure="NaN"),
        lambda n,i: "bad header",
    ]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(ADDRESS)
        sock.settimeout(5)
        server = threading.Thread(target=serve, args=(sock, replies), daemon=True)
        server.start()
        rows = []
        for _ in replies:
            state = tick(3, state[0])
            rows.append(state)
        server.join(5)
        assert not server.is_alive()
    assert rows[0][7].startswith("OPEN") and rows[0][8].startswith("CLOSED")
    assert rows[0][3] == "NaN" and "LOOPBACK_FIXTURE" in rows[0][5]  # mode transition
    assert "?" in rows[1][11] and float(rows[1][3]) > 0
    assert rows[2][3] == rows[3][3] == rows[4][3] == "NaN"
    assert "NATIVE" in rows[4][4]
    assert "unverified" in rows[5][7] and "unverified" in rows[5][8]
    assert all("GAP" in r[1] and r[7] == r[10] == "UNKNOWN" for r in rows[6:])
    disconnected = tick(3, rows[-1][0])
    assert "GAP" in disconnected[1] and disconnected[3] == "NaN"
    path = Path(disconnected[2])
    with path.open(encoding="utf-8", newline="") as f:
        log = list(csv.DictReader(f))
    assert len(log) == len(replies)+1 and log[0]["gate_contact_bits"] == "6"
    assert log[3]["pressure"] == "" and log[-1]["coil_cmd"] == ""
    assert path.parent.name == "MAIZE Vacuum Logs" and path == Path(rows[0][2])
    path.unlink()  # only this test's unique recording
    print("Passed: simulation, 16 reed combinations, re-arm, sequence hold, UDP validation, CSV and disconnect.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    if parser.parse_args().fixture:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(ADDRESS)
            print("Loopback telemetry at 127.0.0.1:44820. Ctrl+C to stop.", flush=True)
            serve(sock)
    else:
        verify()
