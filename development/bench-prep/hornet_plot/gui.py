"""
One window, three pages. Drawing only. The pump-down rules live in logic.py.

Pseudocode
----------
1. A notebook holds Pressures, Gate, and Pump-down.
2. Pressures is the plot and the four show/hide boxes.
3. Gate is the valve button and the ion-gauge buttons.
4. Pump-down is the chamber choice, the start button, and the big status line.
"""

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from logic import fmt_cg, fmt_sci


class Gui:
    def __init__(self, root):
        self.root = root
        self.root.title("Hornet")
        self.root.geometry("1180x820")
        self.quit_requested = False
        self.on_start = None
        self.on_stop = None
        self.on_quit = None
        self.on_valve = None
        self.on_ig = None
        self.on_ig_off = None
        self.on_sequence = None
        self.on_chamber = None

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.page_p = ttk.Frame(self.nb)
        self.page_g = ttk.Frame(self.nb)
        self.page_s = ttk.Frame(self.nb)
        self.nb.add(self.page_p, text="Pressures")
        self.nb.add(self.page_g, text="Gate")
        self.nb.add(self.page_s, text="Pump-down")

        self._build_pressures()
        self._build_gate()
        self._build_sequence()

        bar = ttk.Frame(root)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        self.status = ttk.Label(bar, text="RUNNING")
        self.status.pack(side="left")
        self.error = ttk.Label(bar, text="")
        self.error.pack(side="left", padx=16)

    def _build_pressures(self):
        self.fig = Figure(figsize=(11, 6.2), dpi=100)
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.16, hspace=0.35, wspace=0.28)
        grid = self.fig.add_gridspec(2, 2, height_ratios=[2.2, 1.3])
        self.ax_ts = self.fig.add_subplot(grid[0, :])
        self.ax_scatter = self.fig.add_subplot(grid[1, 0])
        self.ax_metrics = self.fig.add_subplot(grid[1, 1])
        self.ax_metrics.axis("off")
        self.ax_ts.set_title("Convection gauges")
        self.ax_ts.set_xlabel("t (s)")
        self.ax_ts.set_ylabel("P (Torr)")
        self.ax_ts.set_yscale("log")
        self.ax_ts.grid(True, which="both", alpha=0.3)
        # Same hue for one question. Address 1 is the heavy line.
        (self.line_cg1,) = self.ax_ts.plot([], [], "-", label="CG1 addr 1", color="#084594", lw=3.5)
        (self.line_a2cg1,) = self.ax_ts.plot([], [], "-", label="CG1 addr 2", color="#6baed6", lw=1.6)
        (self.line_cg2,) = self.ax_ts.plot([], [], "-", label="CG2 addr 1", color="#d94801", lw=3.5)
        (self.line_a2cg2,) = self.ax_ts.plot([], [], "-", label="CG2 addr 2", color="#fdae6b", lw=1.6)
        self.lines = (self.line_cg1, self.line_a2cg1, self.line_cg2, self.line_a2cg2)
        self.ax_ts.legend(loc="upper right")
        self.ax_scatter.set_title("CG1 vs CG2")
        self.ax_scatter.set_xlabel("CG1 (Torr)")
        self.ax_scatter.set_ylabel("CG2 (Torr)")
        self.ax_scatter.set_xscale("log")
        self.ax_scatter.set_yscale("log")
        self.ax_scatter.grid(True, which="both", alpha=0.3)
        self.scatter = self.ax_scatter.scatter([], [], s=28, c="#084594", label="addr 1")
        self.scatter_a2 = self.ax_scatter.scatter([], [], s=16, c="#6baed6", label="addr 2")
        (self.line_eq,) = self.ax_scatter.plot([], [], "--", color="gray", alpha=0.7, label="1:1")
        self.ax_scatter.legend(loc="upper left")
        self.metrics_text = self.ax_metrics.text(
            0.02, 0.98, "", transform=self.ax_metrics.transAxes,
            va="top", ha="left", family="monospace", fontsize=9,
        )
        canvas = FigureCanvasTkAgg(self.fig, master=self.page_p)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

        row = ttk.Frame(self.page_p)
        row.pack(fill="x", padx=8, pady=8)
        self.show = []
        for name in ("CG1 addr 1", "CG1 addr 2", "CG2 addr 1", "CG2 addr 2"):
            var = tk.BooleanVar(value=True)
            self.show.append(var)
            ttk.Checkbutton(row, text=name, variable=var, command=self._redraw).pack(side="left", padx=8)
        ttk.Button(row, text="Start", command=self._start).pack(side="right", padx=4)
        ttk.Button(row, text="Stop", command=self._stop).pack(side="right", padx=4)
        ttk.Button(row, text="Quit", command=self._quit).pack(side="right", padx=4)

    def _build_gate(self):
        pad = ttk.Frame(self.page_g, padding=28)
        pad.pack(fill="both", expand=True)
        self.gate_text = tk.Label(
            pad, text="Waiting for the board.", justify="left", anchor="nw",
            font=("Consolas", 18),
        )
        self.gate_text.pack(fill="both", expand=True)
        buttons = ttk.Frame(pad)
        buttons.pack(fill="x", pady=12)
        self.valve_btn = ttk.Button(buttons, text="Open valve", command=self._valve)
        self.valve_btn.pack(side="left", padx=6, ipadx=12, ipady=8)
        self.ig_btn = ttk.Button(buttons, text="Ion gauge on", command=self._ig, state="disabled")
        self.ig_btn.pack(side="left", padx=6, ipadx=12, ipady=8)
        self.ig_off_btn = ttk.Button(buttons, text="Ion gauge off", command=self._ig_off)
        self.ig_off_btn.pack(side="left", padx=6, ipadx=12, ipady=8)

    def _build_sequence(self):
        pad = ttk.Frame(self.page_s, padding=28)
        pad.pack(fill="both", expand=True)
        ttk.Label(pad, text="Chamber pressure", font=("Segoe UI", 14)).pack(anchor="w")
        self.chamber = tk.StringVar(value="a1cg2")
        choices = (
            ("a1cg2", "CG2 of address 1"),
            ("a2cg1", "CG1 of address 2"),
            ("a2cg2", "CG2 of address 2"),
        )
        for value, label in choices:
            ttk.Radiobutton(
                pad, text=label, value=value, variable=self.chamber,
                command=self._chamber,
            ).pack(anchor="w", pady=4)
        ttk.Label(
            pad,
            text="Cryo pressure is always CG1 of address 1. It is written down only while the gate is closed.",
            wraplength=720,
        ).pack(anchor="w", pady=(12, 8))
        ttk.Button(pad, text="Start pump-down", command=self._sequence).pack(anchor="w", ipadx=10, ipady=6)
        self.banner = tk.Label(
            pad, text="Choose the chamber reading, then start the pump-down.",
            justify="left", anchor="nw", font=("Segoe UI", 20), wraplength=760,
        )
        self.banner.pack(fill="both", expand=True, pady=24)

    def _start(self):
        if self.on_start:
            self.on_start()

    def _stop(self):
        if self.on_stop:
            self.on_stop()

    def _quit(self):
        self.quit_requested = True
        if self.on_quit:
            self.on_quit()
        self.root.quit()

    def _valve(self):
        if self.on_valve:
            self.on_valve()

    def _ig(self):
        if str(self.ig_btn["state"]) == "disabled":
            return
        if self.on_ig:
            self.on_ig()

    def _ig_off(self):
        if self.on_ig_off:
            self.on_ig_off()

    def _sequence(self):
        if self.on_sequence:
            self.on_sequence()

    def _chamber(self):
        if self.on_chamber:
            self.on_chamber(self.chamber.get())

    def _redraw(self):
        self.canvas.draw_idle()

    def shown(self):
        return tuple(v.get() for v in self.show)

    def set_status(self, text):
        self.status.configure(text=text)

    def set_error(self, text):
        self.error.configure(text=text)

    def set_banner(self, text):
        self.banner.configure(text=text)

    def set_gate(self, block, valve_label, ig_allowed):
        self.gate_text.configure(text=block)
        self.valve_btn.configure(text=valve_label)
        self.ig_btn.configure(state="normal" if ig_allowed else "disabled")

    def set_metrics(self, text):
        self.metrics_text.set_text(text)

    def draw_series(self, t, columns):
        # columns are already masked for an open jack. A hidden box is an empty line.
        flags = self.shown()
        for line, values, on in zip(self.lines, columns, flags):
            line.set_visible(on)
            line.set_data(t if on else [], values if on else [])
        visible = [line for line, on in zip(self.lines, flags) if on]
        legend = self.ax_ts.get_legend()
        if visible:
            self.ax_ts.legend(visible, [line.get_label() for line in visible], loc="upper right")
        elif legend is not None:
            legend.remove()
        self.ax_ts.relim()
        self.ax_ts.autoscale_view()
        cg1, a2cg1, cg2, a2cg2 = columns
        pts = []
        pts.extend(self._dots(self.scatter, flags[0] and flags[2], cg1, cg2))
        pts.extend(self._dots(self.scatter_a2, flags[1] and flags[3], a2cg1, a2cg2))
        if pts:
            lo = min(pts)
            hi = max(pts)
            pad_lo, pad_hi = lo * 0.5, hi * 2.0
            self.line_eq.set_data([pad_lo, pad_hi], [pad_lo, pad_hi])
            self.ax_scatter.set_xlim(pad_lo, pad_hi)
            self.ax_scatter.set_ylim(pad_lo, pad_hi)
        self.canvas.draw_idle()

    def _dots(self, scatter, on, x, y):
        if not on:
            scatter.set_offsets(np.empty((0, 2)))
            scatter.set_visible(False)
            return []
        mask = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
        if not np.any(mask):
            scatter.set_offsets(np.empty((0, 2)))
            scatter.set_visible(False)
            return []
        scatter.set_visible(True)
        scatter.set_offsets(np.column_stack([x[mask], y[mask]]))
        return [float(np.min(x[mask])), float(np.min(y[mask])), float(np.max(x[mask])), float(np.max(y[mask]))]

    def save(self, path):
        self.fig.savefig(path, dpi=150, bbox_inches="tight")
