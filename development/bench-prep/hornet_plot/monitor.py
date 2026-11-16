"""
Serial port, log file, and the window. Rules are in logic.py. Pages are in gui.py.

Pseudocode
----------
1. Open the Uno once. Do not pulse the reset line.
2. Build the three-page window.
3. Every tick, read lines already waiting. When recording, store a fresh pressure.
4. Carry out pump-down actions the logic asks for: open the gate, send mail, ion-gauge on.
5. Quit saves the picture and closes the port. The ion-gauge letter is not sent from here
   unless the logic says the pressure is already below 1e-4 Torr.
"""

import argparse
import atexit
import sys
import time
import tkinter as tk

import numpy as np
from datetime import datetime, timezone
from pathlib import Path

from serial import SerialException

from alert import send_cryo_mail
from gui import Gui
from logic import (
    Pumpdown,
    Sample,
    append_csv,
    chamber_of,
    compute_metrics,
    fmt_cg,
    fmt_sci,
    ig_button_ok,
    open_csv,
    plot_value,
)
from read_hornet import DEFAULT_PORT, UnoEar, drain, open_uno


def gate_block(ear, allowed):
    if ear.reed == "CLOSED":
        position = "CLOSED"
    elif ear.reed == "NOT_CLOSED":
        position = "NOT CLOSED"
    else:
        position = "waiting"
    if ear.ask == "OPEN":
        command = "holding open"
    elif ear.ask == "RELEASED":
        command = "released"
    else:
        command = "waiting"
    who = {
        "BUTTON": "finger",
        "USB": "screen",
        "BOOT": "startup",
        "BUS": "board lost",
    }.get(ear.src, ear.src or "waiting")
    extra = ""
    for note in reversed(ear.notes):
        if note.startswith("GATE"):
            break
        if note.startswith("OPEN REFUSED") or note.startswith("IG REFUSED"):
            extra = "\n" + note
            break
    text = "Position     %s\nCommand      %s\nLast change  %s\nIon gauge    %s%s" % (
        position,
        command,
        who,
        "allowed" if allowed else "blocked",
        extra,
    )
    label = "Close valve" if ear.ask == "OPEN" else "Open valve"
    return text, label


def metrics_text(status, csv_name, window_s, sample, metrics, ear, error):
    lines = [
        "status   %s" % status,
        "CSV      %s" % csv_name,
        "window   %.0f s" % window_s,
    ]
    if sample is not None:
        lines.extend(
            [
                "A1 CG1   %s" % fmt_cg(sample.cg1),
                "A1 CG2   %s" % fmt_cg(sample.cg2),
                "A2 CG1   %s" % fmt_cg(sample.a2cg1),
                "A2 CG2   %s" % fmt_cg(sample.a2cg2),
                "dP/dt A1 CG1 %s Torr/s" % fmt_sci(metrics.dP_dt_cg1),
                "dP/dt A1 CG2 %s Torr/s" % fmt_sci(metrics.dP_dt_cg2),
                "dP/dt A2 CG1 %s Torr/s" % fmt_sci(metrics.dP_dt_a2cg1),
                "dP/dt A2 CG2 %s Torr/s" % fmt_sci(metrics.dP_dt_a2cg2),
            ]
        )
    lines.append("ASK      %s" % (ear.ask or "n/a"))
    lines.append("D8       %s" % (ear.d8 or "n/a"))
    lines.append("REED     %s" % (ear.reed or "n/a"))
    if error:
        lines.append("error    %s" % error)
    return "\n".join(lines)


class App:
    def __init__(self, port, interval_s, window_s, log_dir):
        self.interval_s = interval_s
        self.window_s = window_s
        self.running = True
        self.csv_path, self.csv_fh = open_csv(log_dir)
        self.plot_path = self.csv_path.with_suffix(".png")
        self.saved = False
        self.closed = False
        self.ear = UnoEar()
        self.samples = []
        self.metrics = compute_metrics([], window_s)
        self.last_error = ""
        self.last_poll = 0.0
        self.last_hornet = time.monotonic()
        self.t0 = time.monotonic()
        self.pump = Pumpdown()
        self.valve_sent = 0.0
        print("CSV log: %s" % self.csv_path.resolve())
        print("Opening %s. This can reset the Uno and shut the gate." % port)
        self.ser = open_uno(port)
        self.root = tk.Tk()
        self.ui = Gui(self.root)
        self.ui.on_start = self.start
        self.ui.on_stop = self.stop
        self.ui.on_quit = self.finish
        self.ui.on_valve = self.valve
        self.ui.on_ig = self.ig_on
        self.ui.on_ig_off = self.ig_off
        self.ui.on_sequence = self.sequence
        self.ui.on_chamber = self.pick_chamber
        self.ui.set_banner(self.pump.banner)
        self.root.protocol("WM_DELETE_WINDOW", self.ui._quit)
        # The window X, Quit, and a normal Python exit all land here.
        atexit.register(self.finish)
        self.root.after(200, self.tick)

    def write(self, payload):
        try:
            self.ser.write(payload)
            self.ser.flush()
            return True
        except (SerialException, OSError) as exc:
            self.last_error = str(exc)
            return False

    def start(self):
        self.running = True
        self.ui.set_status("RUNNING")

    def stop(self):
        self.running = False
        self.ui.set_status("PAUSED")
        self.csv_fh.flush()
        # Pausing the log is the end of this picture. Quit writes it again if more rows arrive.
        self.save_plot()

    def pick_chamber(self, which):
        if self.pump.on:
            return
        self.pump.chamber = which

    def sequence(self):
        self.start()
        ok = self.pump.start(self.ear.reed, self.ear.cg1)
        self.ui.set_banner(self.pump.banner)
        print(self.pump.banner, flush=True)
        return ok

    def valve(self):
        now = time.monotonic()
        if now - self.valve_sent < 0.4:
            return
        self.valve_sent = now
        self.write(b"c" if self.ear.ask == "OPEN" else b"o")

    def ig_on(self):
        sample = self.samples[-1] if self.samples else None
        if sample is None or not ig_button_ok(sample):
            self.pump.banner = "Ion gauge blocked. Pressure is still too high."
            self.ui.set_banner(self.pump.banner)
            return
        self.write(b"i")

    def ig_off(self):
        self.write(b"k")

    def act(self, sample, actions):
        for action in actions:
            if action == "open":
                self.write(b"o")
            elif action == "ig_on":
                self.write(b"i")
            elif action == "email":
                sent = False
                try:
                    sent = send_cryo_mail(chamber_of(sample, self.pump.chamber))
                except Exception as exc:
                    self.last_error = str(exc)
                if sent:
                    print("Email sent to harshdes@umich.edu", flush=True)
                else:
                    print("Email was not sent. SMTP login is not set.", flush=True)
        if actions:
            self.ui.set_banner(self.pump.banner)
            print(self.pump.banner, flush=True)

    def snapshot(self):
        if not self.ear.fresh:
            return None
        self.ear.fresh = False
        return Sample(
            time.monotonic() - self.t0,
            datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            self.ear.cg1,
            self.ear.cg2,
            self.ear.a2cg1,
            self.ear.a2cg2,
            self.ear.ask,
            self.ear.d8,
            self.ear.reed,
            self.ear.src,
        )

    def paint(self):
        sample = self.samples[-1] if self.samples else None
        allowed = sample is not None and ig_button_ok(sample)
        text, label = gate_block(self.ear, allowed)
        self.ui.set_gate(text, label, allowed)
        self.ui.set_error(self.last_error)
        self.ui.set_metrics(
            metrics_text(
                "RUNNING" if self.running else "PAUSED",
                self.csv_path.name,
                self.window_s,
                sample,
                self.metrics,
                self.ear,
                self.last_error,
            )
        )
        if not self.samples:
            return
        t = [s.t_s for s in self.samples]
        cols = []
        for pick in (
            lambda s: s.cg1,
            lambda s: s.a2cg1,
            lambda s: s.cg2,
            lambda s: s.a2cg2,
        ):
            cols.append([s_value(pick(s)) for s in self.samples])
        self.ui.draw_series(np.array(t, dtype=float), [np.array(c, dtype=float) for c in cols])

    def tick(self):
        if self.ui.quit_requested:
            return
        try:
            drain(self.ser, self.ear)
        except (SerialException, OSError, ValueError) as exc:
            self.last_error = str(exc)
            print("[ERROR] %s" % exc, file=sys.stderr, flush=True)
        now = time.monotonic()
        if self.running and (now - self.last_poll) >= self.interval_s:
            self.last_poll = now
            sample = self.snapshot()
            if sample is not None:
                self.last_hornet = now
                self.last_error = ""
                self.samples.append(sample)
                self.metrics = compute_metrics(self.samples, self.window_s)
                append_csv(self.csv_fh, sample, self.metrics)
                self.act(sample, self.pump.step(sample))
                print(
                    "[%s] t=%8.1fs  A1 CG1=%s  A1 CG2=%s  A2 CG1=%s  A2 CG2=%s  ASK=%s REED=%s"
                    % (
                        "RUNNING" if self.running else "PAUSED",
                        sample.t_s,
                        fmt_cg(sample.cg1),
                        fmt_cg(sample.cg2),
                        fmt_cg(sample.a2cg1),
                        fmt_cg(sample.a2cg2),
                        sample.ask or "n/a",
                        sample.reed or "n/a",
                    ),
                    flush=True,
                )
            elif now - self.last_hornet > 4.0:
                self.last_error = "No HORNET line."
        self.paint()
        self.root.after(200, self.tick)

    def save_plot(self):
        # One PNG beside the CSV, same timestamp. Safe to call more than once.
        try:
            self.ui.save(self.plot_path)
            self.saved = True
            print("Plots saved: %s" % self.plot_path.resolve())
        except Exception as exc:
            print("Plot save failed: %s" % exc, file=sys.stderr)

    def finish(self):
        if self.closed:
            return
        self.closed = True
        self.save_plot()
        if self.csv_fh and not self.csv_fh.closed:
            self.csv_fh.flush()
            self.csv_fh.close()
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def run(self):
        self.root.mainloop()
        self.finish()


def s_value(v):
    p = plot_value(v)
    if p is None:
        return float("nan")
    return p


def main():
    parser = argparse.ArgumentParser(description="Hornet window.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--window", type=float, default=30.0)
    parser.add_argument("--log-dir", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    try:
        app = App(args.port, args.interval, args.window, args.log_dir)
    except SerialException as exc:
        print("Serial open failed on %s: %s" % (args.port, exc), file=sys.stderr)
        return 1
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nCtrl+C -- quitting.")
        app.finish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
