"""
Hornet CG1 and CG2 window.

Pseudocode
----------
1. Open the Uno USB port once. Do not send o, c, or x.
2. Create data/run_*.csv.
3. Draw pressure vs time (log), CG1 vs CG2, a numbers box, Start / Stop / Quit.
4. While running, take each HORNET line, append CSV, redraw.
5. Stop pauses the same file. Quit saves a PNG and closes the port.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
from serial import SerialException

from read_hornet import DEFAULT_PORT, open_uno, read_pair

MIN_FIT_POINTS = 3
CSV_HEADER = (
    "timestamp_iso",
    "t_s",
    "CG1_Torr",
    "CG2_Torr",
    "dP_dt_CG1",
    "dP_dt_CG2",
    "decade_s_CG1",
    "decade_s_CG2",
)


@dataclass
class Sample:
    t_s: float
    timestamp_iso: str
    cg1: Optional[float]
    cg2: Optional[float]


@dataclass
class RateMetrics:
    dP_dt_cg1: Optional[float] = None
    dP_dt_cg2: Optional[float] = None
    decade_s_cg1: Optional[float] = None
    decade_s_cg2: Optional[float] = None


@dataclass
class MonitorState:
    running: bool = True
    quit_requested: bool = False
    t0: float = field(default_factory=time.monotonic)
    samples: list[Sample] = field(default_factory=list)
    metrics: RateMetrics = field(default_factory=RateMetrics)
    status: str = "RUNNING"
    last_error: str = ""


def fmt_sci(x: Optional[float]) -> str:
    if x is None:
        return "n/a"
    return f"{x:.3E}"


def fmt_rate(x: Optional[float]) -> str:
    if x is None:
        return ""
    return f"{x:.6E}"


def _window_slopes(t: np.ndarray, p: np.ndarray) -> tuple[Optional[float], Optional[float]]:
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


def compute_metrics(samples: list[Sample], window_s: float) -> RateMetrics:
    if not samples:
        return RateMetrics()
    t_min = samples[-1].t_s - window_s
    window = [s for s in samples if s.t_s >= t_min]
    if len(window) < MIN_FIT_POINTS:
        return RateMetrics()
    t = np.array([s.t_s for s in window], dtype=float)
    cg1 = np.array([np.nan if s.cg1 is None else s.cg1 for s in window], dtype=float)
    cg2 = np.array([np.nan if s.cg2 is None else s.cg2 for s in window], dtype=float)
    d1, tau1 = _window_slopes(t, cg1)
    d2, tau2 = _window_slopes(t, cg2)
    return RateMetrics(d1, d2, tau1, tau2)


def open_csv(log_dir: Path) -> tuple[Path, object]:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir / f"run_{stamp}.csv"
    fh = path.open("w", newline="", encoding="utf-8")
    csv.writer(fh).writerow(CSV_HEADER)
    fh.flush()
    return path, fh


def append_csv(fh, sample: Sample, metrics: RateMetrics) -> None:
    csv.writer(fh).writerow(
        [
            sample.timestamp_iso,
            f"{sample.t_s:.3f}",
            "" if sample.cg1 is None else f"{sample.cg1:.6E}",
            "" if sample.cg2 is None else f"{sample.cg2:.6E}",
            fmt_rate(metrics.dP_dt_cg1),
            fmt_rate(metrics.dP_dt_cg2),
            fmt_rate(metrics.decade_s_cg1),
            fmt_rate(metrics.decade_s_cg2),
        ]
    )
    fh.flush()


class HornetPlot:
    def __init__(self, port: str, interval_s: float, window_s: float, log_dir: Path) -> None:
        self.port = port
        self.interval_s = interval_s
        self.window_s = window_s
        self.state = MonitorState()
        self.csv_path, self.csv_fh = open_csv(log_dir)
        self.plot_path = self.csv_path.with_suffix(".png")
        self._last_poll = 0.0
        self._anim: Optional[FuncAnimation] = None
        self._closed = False
        self._plots_saved = False
        print(f"CSV log: {self.csv_path.resolve()}")
        print(f"Opening {port}. This can reset the Uno and shut the gate.")
        self.ser = open_uno(port)
        self._build_figure()

    def _build_figure(self) -> None:
        self.fig = plt.figure(figsize=(11, 8))
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.18, hspace=0.35, wspace=0.25)
        gs = self.fig.add_gridspec(2, 2, height_ratios=[2.2, 1.4])
        self.ax_ts = self.fig.add_subplot(gs[0, :])
        self.ax_scatter = self.fig.add_subplot(gs[1, 0])
        self.ax_metrics = self.fig.add_subplot(gs[1, 1])
        self.ax_metrics.axis("off")
        self.ax_ts.set_title("Hornet CG1 and CG2")
        self.ax_ts.set_xlabel("t (s)")
        self.ax_ts.set_ylabel("P (Torr)")
        self.ax_ts.set_yscale("log")
        self.ax_ts.grid(True, which="both", alpha=0.3)
        (self.line_cg1,) = self.ax_ts.plot([], [], "-", label="CG1", color="#1f77b4")
        (self.line_cg2,) = self.ax_ts.plot([], [], "-", label="CG2", color="#ff7f0e")
        self.ax_ts.legend(loc="upper right")
        self.ax_scatter.set_title("CG1 vs CG2")
        self.ax_scatter.set_xlabel("CG1 (Torr)")
        self.ax_scatter.set_ylabel("CG2 (Torr)")
        self.ax_scatter.set_xscale("log")
        self.ax_scatter.set_yscale("log")
        self.ax_scatter.grid(True, which="both", alpha=0.3)
        self.scatter = self.ax_scatter.scatter([], [], s=18, c="#1f77b4", alpha=0.7)
        (self.line_eq,) = self.ax_scatter.plot([], [], "--", color="gray", alpha=0.7, label="1:1")
        self.ax_scatter.legend(loc="upper left")
        self.metrics_text = self.ax_metrics.text(
            0.02, 0.98, "", transform=self.ax_metrics.transAxes,
            va="top", ha="left", family="monospace", fontsize=9,
        )
        ax_start = self.fig.add_axes([0.20, 0.03, 0.15, 0.06])
        ax_stop = self.fig.add_axes([0.40, 0.03, 0.15, 0.06])
        ax_quit = self.fig.add_axes([0.60, 0.03, 0.15, 0.06])
        self.btn_start = Button(ax_start, "Start")
        self.btn_stop = Button(ax_stop, "Stop")
        self.btn_quit = Button(ax_quit, "Quit")
        self.btn_start.on_clicked(self._on_start)
        self.btn_stop.on_clicked(self._on_stop)
        self.btn_quit.on_clicked(self._on_quit)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("close_event", self._on_close)
        self.status_artist = self.fig.text(0.02, 0.045, "RUNNING", fontsize=11, weight="bold")

    def _on_start(self, _event=None) -> None:
        self.state.running = True
        self.state.status = "RUNNING"
        self.status_artist.set_text("RUNNING")
        self.fig.canvas.draw_idle()

    def _on_stop(self, _event=None) -> None:
        self.state.running = False
        self.state.status = "PAUSED"
        self.status_artist.set_text("PAUSED")
        if self.csv_fh and not self.csv_fh.closed:
            self.csv_fh.flush()
        self.fig.canvas.draw_idle()

    def _on_quit(self, _event=None) -> None:
        self.state.quit_requested = True
        self.state.running = False
        self._save_plots()
        self._shutdown()
        plt.close(self.fig)

    def _on_close(self, _event=None) -> None:
        self.state.quit_requested = True
        self.state.running = False
        self._save_plots()
        self._shutdown()

    def _on_key(self, event) -> None:
        if event.key == " ":
            self._on_stop() if self.state.running else self._on_start()
        elif event.key in ("q", "Q", "escape"):
            self._on_quit()

    def _shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.csv_fh and not self.csv_fh.closed:
            self.csv_fh.flush()
            self.csv_fh.close()
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def _save_plots(self) -> None:
        if self._plots_saved:
            return
        try:
            self.fig.savefig(self.plot_path, dpi=150, bbox_inches="tight")
            self._plots_saved = True
            print(f"Plots saved: {self.plot_path.resolve()}")
        except Exception as exc:
            print(f"Plot save failed: {exc}", file=sys.stderr)

    def _poll_once(self) -> Sample:
        cg1, cg2 = read_pair(self.ser, timeout_s=max(3.0, self.interval_s + 1.0))
        return Sample(
            t_s=time.monotonic() - self.state.t0,
            timestamp_iso=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            cg1=cg1,
            cg2=cg2,
        )

    def _series(self, values: list[Optional[float]]) -> np.ndarray:
        return np.array([np.nan if v is None else v for v in values], dtype=float)

    def _refresh_plots(self) -> None:
        samples = self.state.samples
        self.metrics_text.set_text(self._metrics_block())
        if not samples:
            return
        t = np.array([s.t_s for s in samples], dtype=float)
        cg1 = self._series([s.cg1 for s in samples])
        cg2 = self._series([s.cg2 for s in samples])
        self.line_cg1.set_data(t, cg1)
        self.line_cg2.set_data(t, cg2)
        self.ax_ts.relim()
        self.ax_ts.autoscale_view()
        both = np.isfinite(cg1) & np.isfinite(cg2) & (cg1 > 0) & (cg2 > 0)
        if np.any(both):
            self.scatter.set_offsets(np.column_stack([cg1[both], cg2[both]]))
            lo = float(min(cg1[both].min(), cg2[both].min()))
            hi = float(max(cg1[both].max(), cg2[both].max()))
            pad_lo, pad_hi = lo * 0.5, hi * 2.0
            self.line_eq.set_data([pad_lo, pad_hi], [pad_lo, pad_hi])
            self.ax_scatter.set_xlim(pad_lo, pad_hi)
            self.ax_scatter.set_ylim(pad_lo, pad_hi)
        self.status_artist.set_text(self.state.status)

    def _metrics_block(self) -> str:
        m = self.state.metrics
        s = self.state.samples[-1] if self.state.samples else None
        lines = [
            f"status   {self.state.status}",
            f"CSV      {self.csv_path.name}",
            f"window   {self.window_s:.0f} s",
        ]
        if s is not None:
            lines.extend(
                [
                    f"CG1      {fmt_sci(s.cg1)} Torr",
                    f"CG2      {fmt_sci(s.cg2)} Torr",
                    f"dP/dt CG1 {fmt_sci(m.dP_dt_cg1)} Torr/s",
                    f"dP/dt CG2 {fmt_sci(m.dP_dt_cg2)} Torr/s",
                    f"s/dec CG1 {fmt_sci(m.decade_s_cg1)}",
                    f"s/dec CG2 {fmt_sci(m.decade_s_cg2)}",
                ]
            )
        if self.state.last_error:
            lines.append(f"error    {self.state.last_error}")
        return "\n".join(lines)

    def _animate(self, _frame: int):
        if self.state.quit_requested:
            return self.line_cg1, self.line_cg2
        now = time.monotonic()
        if self.state.running and (now - self._last_poll) >= self.interval_s:
            self._last_poll = now
            try:
                sample = self._poll_once()
                self.state.samples.append(sample)
                self.state.metrics = compute_metrics(self.state.samples, self.window_s)
                self.state.last_error = ""
                append_csv(self.csv_fh, sample, self.state.metrics)
                print(
                    f"[{self.state.status}] t={sample.t_s:8.1f}s  "
                    f"CG1={fmt_sci(sample.cg1)}  CG2={fmt_sci(sample.cg2)}",
                    flush=True,
                )
                self._refresh_plots()
            except (TimeoutError, SerialException, OSError, ValueError) as exc:
                self.state.last_error = str(exc)
                print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
                self.metrics_text.set_text(self._metrics_block())
        return self.line_cg1, self.line_cg2

    def run(self) -> int:
        self._anim = FuncAnimation(
            self.fig, self._animate, interval=200, blit=False, cache_frame_data=False,
        )
        plt.show()
        self._save_plots()
        self._shutdown()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot Hornet CG1 and CG2 from the Uno.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--window", type=float, default=30.0)
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data",
    )
    args = parser.parse_args()
    try:
        app = HornetPlot(args.port, args.interval, args.window, args.log_dir)
    except SerialException as exc:
        print(f"Serial open failed on {args.port}: {exc}", file=sys.stderr)
        return 1
    try:
        return app.run()
    except KeyboardInterrupt:
        print("\nCtrl+C -- quitting.")
        app._save_plots()
        app._shutdown()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
