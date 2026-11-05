"""Place the phase-5 controller and pour a ground plane.

Pseudocode
1. Read the part list written with the schematic.
2. Load each footprint and pack the groups into rows: power, Uno sockets,
   panel, safety relays, serial link, sensor inputs, coil drivers.
3. Copy each pad's net from that list.
4. Draw the board edge and pour ground across the back.
   Signal copper is left as airwires. A crossed automatic router would
   short nets, which is worse than an unfinished route.
"""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
FP_ROOT = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
PARTS = HERE / "board_parts.json"
BOARD_PATH = HERE / "maize-controller.kicad_pcb"

ROW_WIDTH = 260.0
GAP = 1.6
MARGIN = 8.0


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def group_of(record: dict) -> int:
    value = record["value"]
    ref = record["ref"]
    if value in {"J_LOGIC", "J_COIL24"} or value.startswith("AMS1117") or ref.startswith("F"):
        return 0
    if value.startswith("J_UNO"):
        return 1
    if value.startswith("J_PANEL") or value.startswith("J_DISPLAY"):
        return 2
    if value.startswith("G5LE") or value.startswith("TPS3823"):
        return 3
    if value.startswith("MCP23017") or value.startswith("SC16") or value.startswith("ISO3082") or value.startswith("CRE1"):
        return 4
    if value.startswith("J_HORNET") or value == "J_HORNET":
        return 5
    if value.startswith("PC817") or value.startswith("J_ZS") or value.startswith("J_TI") or value.startswith("J_PS") or value.startswith("J_P102") or value.startswith("J_IG") or value.startswith("J_SPARE"):
        return 6
    if value.startswith("IRLZ44") or value.startswith("J_CRYO") or value.startswith("J_ROUGH") or value.startswith("J_VENT"):
        return 7
    return 8


def load_footprint(lib_id: str):
    library, name = lib_id.split(":", 1)
    footprint = pcbnew.FootprintLoad(str(FP_ROOT / f"{library}.pretty"), name)
    if footprint is None:
        raise FileNotFoundError(lib_id)
    return footprint


def place(board: pcbnew.BOARD, footprint, x_mm: float, y_mm: float) -> tuple[float, float]:
    footprint.SetPosition(pcbnew.VECTOR2I(0, 0))
    box = footprint.GetBoundingBox()
    shift_x = mm(x_mm) - box.GetLeft()
    shift_y = mm(y_mm) - box.GetTop()
    pos = footprint.GetPosition()
    footprint.SetPosition(pcbnew.VECTOR2I(pos.x + shift_x, pos.y + shift_y))
    board.Add(footprint)
    box = footprint.GetBoundingBox()
    return pcbnew.ToMM(box.GetWidth()), pcbnew.ToMM(box.GetHeight())


def ensure_net(board: pcbnew.BOARD, name: str, cache: dict):
    if name in cache:
        return cache[name]
    item = pcbnew.NETINFO_ITEM(board, name)
    board.Add(item)
    found = board.FindNet(name)
    cache[name] = found
    return found


def add_edge(board: pcbnew.BOARD, x1, y1, x2, y2) -> None:
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetLayer(pcbnew.Edge_Cuts)
    shape.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    shape.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    shape.SetWidth(mm(0.1))
    board.Add(shape)


def pour_ground(board: pcbnew.BOARD, width: float, height: float, net) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(net)
    zone.SetIsFilled(False)
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetLocalClearance(mm(0.3))
    zone.SetMinThickness(mm(0.25))
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in ((MARGIN / 2, MARGIN / 2), (width - MARGIN / 2, MARGIN / 2), (width - MARGIN / 2, height - MARGIN / 2), (MARGIN / 2, height - MARGIN / 2)):
        outline.Append(mm(x), mm(y))
    board.Add(zone)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def main() -> None:
    records = json.loads(PARTS.read_text(encoding="utf-8"))
    records.sort(key=lambda record: (group_of(record), record["ref"]))
    board = pcbnew.BOARD()
    nets: dict = {}
    cursor_x = MARGIN
    cursor_y = MARGIN
    row_height = 0.0
    max_x = 0.0
    max_y = 0.0

    for record in records:
        footprint = load_footprint(record["footprint"])
        footprint.SetReference(record["ref"])
        footprint.SetValue(record["value"])
        footprint.SetPosition(pcbnew.VECTOR2I(0, 0))
        box = footprint.GetBoundingBox()
        width = pcbnew.ToMM(box.GetWidth())
        height = pcbnew.ToMM(box.GetHeight())
        if cursor_x + width > ROW_WIDTH and cursor_x > MARGIN:
            cursor_x = MARGIN
            cursor_y += row_height + GAP
            row_height = 0.0
        place(board, footprint, cursor_x, cursor_y)
        for pad in footprint.Pads():
            net_name = ""
            for listed in record["pads"]:
                if listed["num"] == pad.GetNumber() and listed["net"]:
                    net_name = listed["net"]
                    break
            if net_name:
                pad.SetNet(ensure_net(board, net_name, nets))
        cursor_x += width + GAP
        row_height = max(row_height, height)
        max_x = max(max_x, cursor_x)
        max_y = max(max_y, cursor_y + height)

    board_w = max_x + MARGIN
    board_h = max_y + MARGIN
    add_edge(board, 0, 0, board_w, 0)
    add_edge(board, board_w, 0, board_w, board_h)
    add_edge(board, board_w, board_h, 0, board_h)
    add_edge(board, 0, board_h, 0, 0)
    pour_ground(board, board_w, board_h, ensure_net(board, "GND", nets))
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"wrote {BOARD_PATH}")
    print(f"parts {len(records)} nets {len(nets)} size {board_w:.1f} x {board_h:.1f} mm")


if __name__ == "__main__":
    main()


