"""
Decisions for the Hornet plot. No window and no serial port live here.

Pseudocode
----------
1. Keep each pressure sample and the slope over the recent window.
2. A pump-down writes the cryo number only while the gate reed is closed.
3. Open the gate once the chosen chamber reading is within 1 Torr of that number.
4. Below 80 mTorr, ask for one email. Below 1e-4 Torr, ask for the ion gauge once.
5. 1100 Torr is an open jack. 9.9e9 is the filament-off flag. Neither is a pressure.
"""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np

MIN_FIT_POINTS = 3
OPEN_TORR = 1100.0
MATCH_TORR = 1.0
CRYO_READY_TORR = 0.080
IG_BUTTON_TORR = 1.1e-3
IG_AUTO_TORR = 1.0e-4
IG_OFF_FLAG = 9.0e9

CSV_HEADER = (
    "timestamp_iso",
    "t_s",
    "CG1_Torr",
    "CG2_Torr",
    "A2_CG1_Torr",
    "A2_CG2_Torr",
    "gate_ask",
    "gate_d8",
    "gate_reed",
    "gate_src",
    "dP_dt_CG1",
    "dP_dt_CG2",
    "decade_s_CG1",
    "decade_s_CG2",
)


class Sample:
    def __init__(self, t_s, timestamp_iso, cg1, cg2, a2cg1, a2cg2, ask, d8, reed, src):
        self.t_s = t_s
        self.timestamp_iso = timestamp_iso
        self.cg1 = cg1
        self.cg2 = cg2
        self.a2cg1 = a2cg1
        self.a2cg2 = a2cg2
        self.ask = ask
        self.d8 = d8
        self.reed = reed
        self.src = src


class Metrics:
    def __init__(self):
        self.dP_dt_cg1 = None
        self.dP_dt_cg2 = None
        self.dP_dt_a2cg1 = None
        self.dP_dt_a2cg2 = None
        self.decade_s_cg1 = None
        self.decade_s_cg2 = None


def fmt_sci(x):
    if x is None:
        return "n/a"
    return "%.3E" % x


def fmt_rate(x):
    if x is None:
        return ""
    return "%.6E" % x


def is_open(x):
    return x is not None and abs(x - OPEN_TORR) <= 1.0


def fmt_cg(x):
    if x is None:
        return "n/a"
    if is_open(x):
        return "not connected"
    return "%s Torr" % fmt_sci(x)


def plot_value(x):
    if x is None or is_open(x):
        return None
    return x


def chamber_of(sample, which):
    if which == "a2cg1":
        return sample.a2cg1
    if which == "a2cg2":
        return sample.a2cg2
    return sample.cg2


def live_readings(sample):
    # An open jack and the filament-off flag must not unlock the ion gauge.
    vals = []
    for v in (sample.cg1, sample.cg2, sample.a2cg1, sample.a2cg2):
        if v is None or is_open(v) or v >= IG_OFF_FLAG:
            continue
        vals.append(v)
    return vals


def ig_button_ok(sample):
    vals = live_readings(sample)
    return bool(vals) and max(vals) <= IG_BUTTON_TORR


def ig_auto_ok(sample):
    # The convection floor near 1e-3 is not a 1e-4 reading.
    vals = live_readings(sample)
    return bool(vals) and max(vals) < IG_AUTO_TORR


def _slopes(t, p):
    mask = np.isfinite(t) & np.isfinite(p) & (p > 0)
    t_w = t[mask]
    p_w = p[mask]
    if t_w.size < MIN_FIT_POINTS:
        return None, None
    if float(t_w[-1] - t_w[0]) < 1e-6:
        return None, None
    p_med = float(np.median(p_w))
    p_span = float(np.max(p_w) - np.min(p_w))
    if p_med <= 0 or (p_span / p_med) < 1e-4:
        return None, None
    dP_dt = float(np.polyfit(t_w, p_w, 1)[0])
    m_log = float(np.polyfit(t_w, np.log10(p_w), 1)[0])
    decade_s = None if abs(m_log) < 1e-5 else float(1.0 / abs(m_log))
    return dP_dt, decade_s


def _col(window, pick):
    return np.array([np.nan if plot_value(pick(s)) is None else pick(s) for s in window], dtype=float)


def compute_metrics(samples, window_s):
    out = Metrics()
    if not samples:
        return out
    t_min = samples[-1].t_s - window_s
    window = [s for s in samples if s.t_s >= t_min]
    if len(window) < MIN_FIT_POINTS:
        return out
    t = np.array([s.t_s for s in window], dtype=float)
    out.dP_dt_cg1, out.decade_s_cg1 = _slopes(t, _col(window, lambda s: s.cg1))
    out.dP_dt_cg2, out.decade_s_cg2 = _slopes(t, _col(window, lambda s: s.cg2))
    out.dP_dt_a2cg1, _ = _slopes(t, _col(window, lambda s: s.a2cg1))
    out.dP_dt_a2cg2, _ = _slopes(t, _col(window, lambda s: s.a2cg2))
    return out


def open_csv(log_dir):
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir / ("run_%s.csv" % stamp)
    fh = path.open("w", newline="", encoding="utf-8")
    csv.writer(fh).writerow(CSV_HEADER)
    fh.flush()
    return path, fh


def append_csv(fh, sample, metrics):
    csv.writer(fh).writerow(
        [
            sample.timestamp_iso,
            "%.3f" % sample.t_s,
            "" if sample.cg1 is None else "%.6E" % sample.cg1,
            "" if sample.cg2 is None else "%.6E" % sample.cg2,
            "" if sample.a2cg1 is None else "%.6E" % sample.a2cg1,
            "" if sample.a2cg2 is None else "%.6E" % sample.a2cg2,
            sample.ask,
            sample.d8,
            sample.reed,
            sample.src,
            fmt_rate(metrics.dP_dt_cg1),
            fmt_rate(metrics.dP_dt_cg2),
            fmt_rate(metrics.decade_s_cg1),
            fmt_rate(metrics.decade_s_cg2),
        ]
    )
    fh.flush()


class Pumpdown:
    def __init__(self):
        self.chamber = "a1cg2"
        self.on = False
        self.cryo_target = None
        self.gate_sent = False
        self.mail_sent = False
        self.ig_sent = False
        self.banner = "Choose the chamber reading, then start the pump-down."

    def start(self, reed, cg1):
        # The written cryo number is only valid while the gate is shut.
        if reed != "CLOSED":
            self.on = False
            self.banner = "Gate is not closed. Close it, then start again."
            return False
        if cg1 is None or is_open(cg1):
            self.on = False
            self.banner = "No cryo reading on address 1 convection 1."
            return False
        self.cryo_target = cg1
        self.on = True
        self.gate_sent = False
        self.mail_sent = False
        self.ig_sent = False
        self.banner = "Cryo target %s Torr. Waiting for the chamber." % fmt_sci(cg1)
        return True

    def step(self, sample):
        # Each string is one action for the runner. This object does not touch the port.
        actions = []
        if not self.on or self.cryo_target is None:
            return actions
        chamber = chamber_of(sample, self.chamber)
        if chamber is None or is_open(chamber):
            return actions
        if not self.gate_sent and abs(chamber - self.cryo_target) <= MATCH_TORR:
            actions.append("open")
            self.gate_sent = True
            self.banner = "Within 1 Torr. Gate open sent."
        if chamber < CRYO_READY_TORR and not self.mail_sent:
            actions.append("email")
            self.mail_sent = True
            self.banner = "Less than 80 mTorr. Turn on the cryopump."
        if not self.ig_sent and ig_auto_ok(sample):
            actions.append("ig_on")
            self.ig_sent = True
            self.banner = "Below 1e-4 Torr. Ion gauge on sent."
        return actions
