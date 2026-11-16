"""
Draw a PNG next to each CSV that does not already have one.

Pseudocode
----------
1. Look in data/ for run_*.csv.
2. Skip a file when run_*.png is already beside it.
3. Read t and whichever pressure columns that file has.
4. Leave out 1100 Torr. That is the open-jack value, not a pressure.
5. Save the picture with the same timestamp as the CSV.
"""

import csv
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib.figure import Figure

from logic import is_open

DATA = Path(__file__).resolve().parent / "data"
# Name in the file, label, color, width. Address 1 is the heavy line.
SERIES = (
    ("CG1_Torr", "CG1 addr 1", "#084594", 3.5),
    ("A2_CG1_Torr", "CG1 addr 2", "#6baed6", 1.6),
    ("CG2_Torr", "CG2 addr 1", "#d94801", 3.5),
    ("A2_CG2_Torr", "CG2 addr 2", "#fdae6b", 1.6),
)


def num(text):
    if text is None or text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if is_open(value):
        return None
    return value


def load(path):
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    t = []
    cols = {name: [] for name, _, _, _ in SERIES}
    for row in rows:
        try:
            t.append(float(row["t_s"]))
        except (KeyError, ValueError):
            continue
        for name, _, _, _ in SERIES:
            cols[name].append(num(row.get(name)))
    return np.array(t, dtype=float), cols


def draw(path, t, cols):
    fig = Figure(figsize=(11, 6.2), dpi=100)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.12)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(path.stem)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("P (Torr)")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3)
    drew = False
    for name, label, color, width in SERIES:
        if name not in cols or not cols[name]:
            continue
        y = np.array([np.nan if v is None else v for v in cols[name]], dtype=float)
        if not np.any(np.isfinite(y) & (y > 0)):
            continue
        ax.plot(t, y, "-", label=label, color=color, lw=width)
        drew = True
    if drew:
        ax.legend(loc="upper right")
    out = path.with_suffix(".png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    return out


def main():
    missing = []
    for csv_path in sorted(DATA.glob("run_*.csv")):
        if csv_path.with_suffix(".png").exists():
            continue
        missing.append(csv_path)
    if not missing:
        print("Every CSV already has a PNG.")
        return
    for csv_path in missing:
        t, cols = load(csv_path)
        if t.size == 0:
            print("Skip empty %s" % csv_path.name)
            continue
        out = draw(csv_path, t, cols)
        print("Wrote %s" % out.name)


if __name__ == "__main__":
    main()
