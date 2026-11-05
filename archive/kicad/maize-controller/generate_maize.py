"""Generate the MAIZE phase-5 controller schematic for KiCad 10.

Pseudocode
1. Pull each official symbol out of the KiCad libraries, including parts that
   are only aliases of a parent symbol.
2. Place every part, and hang a short stub off each pin so a net name can
   attach without drawing a rat's nest of crossing lines.
3. Power pins join KiCad power symbols. Every other pin joins a global label.
   One power flag marks ground and the 9 V input, which have no regulator
   feeding them.
4. Write the schematic, then let kicad-cli run the electrical rules check.

What this sheet is
The controller the development notes already describe: Uno R3, isolated
Hornet RS-485, six 24 V DC coil drivers, twelve contact inputs, a panel, and
a hardware path that removes opening power when the processor, the mode
switch, the enable key, or STOP is not healthy.

What this sheet is not
A measured pinout of the cryo gate, the pilots, or the sensor connectors.
Those are still unknown. The terminals are the landing contract, not a claim
that the installed wires were probed.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path

KICAD = Path(r"C:\Program Files\KiCad\10.0")
SYM_DIR = KICAD / "share" / "kicad" / "symbols"
FP_DIR = KICAD / "share" / "kicad" / "footprints"
OUT_DIR = Path(__file__).resolve().parent
PROJECT = "maize-controller"

FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_CP = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
FP_LED = "LED_THT:LED_D5.0mm"
FP_D = "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
FP_D_SMALL = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
FP_FUSE = (
    "Fuse:Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_"
    "P20.00x5.00mm_D1.05mm_Horizontal"
)
FP_HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_TB2 = (
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_"
    "1x02_P5.08mm_Horizontal"
)
FP_TB3 = (
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_"
    "1x03_P5.08mm_Horizontal"
)
FP_TB4 = (
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4-5.08_"
    "1x04_P5.08mm_Horizontal"
)
FP_TB6 = (
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-6-5.08_"
    "1x06_P5.08mm_Horizontal"
)
FP_TB10 = (
    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-10-5.08_"
    "1x10_P5.08mm_Horizontal"
)
FP_SOCK8 = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"
FP_SOCK6 = "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical"
FP_SOCK10 = "Connector_PinSocket_2.54mm:PinSocket_1x10_P2.54mm_Vertical"
FP_XTAL = "Crystal:Crystal_HC49-U_Vertical"
FP_DE9 = "Connector_Dsub:DSUB-9_Pins_Vertical_P2.77x2.84mm_MountingHoles"

# Nets that are not driven by a regulator output. Exactly one PWR_FLAG each.
FLAG_NETS = {"GND", "+9V"}
POWER_SYMS = {"GND": "GND", "+5V": "+5V", "+3V3": "+3V3"}


def uid() -> str:
    return str(uuid.uuid4())


def r2(value: float) -> float:
    return round(float(value) + 1e-9, 2)


def norm_name(name: str) -> str:
    text = name.replace("~{", "").replace("{", "").replace("}", "")
    return text.replace("V_DD", "VDD").replace("V_SS", "VSS")


def pin_key(name: str, number: str) -> str:
    if name.startswith("Pin_"):
        return "#" + name.split("_", 1)[1]
    if name == "" or name == number:
        return "#" + number
    return norm_name(name)


def extract_symbol(text: str, name: str) -> str:
    token = f'(symbol "{name}"'
    start = text.find(token)
    if start < 0:
        # Library files indent the top-level form with one tab.
        start = text.find("\t" + token)
    if start < 0:
        raise KeyError(name)
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError(f"unclosed symbol {name}")


def replace_property(block: str, key: str, value: str) -> str:
    pattern = rf'(\(property "{re.escape(key)}" ")([^"]*)(")'
    if re.search(pattern, block) is None:
        return block
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return re.sub(pattern, lambda match: match.group(1) + escaped + match.group(3), block, count=1)


def child_properties(block: str) -> dict[str, str]:
    return dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', block))


class Pin:
    def __init__(self, number: str, name: str, electrical: str, x: float, y: float, angle: int, unit: int):
        self.number = number
        self.name = name
        self.electrical = electrical
        self.x = x
        self.y = y
        self.angle = angle
        self.unit = unit

    @property
    def key(self) -> str:
        return pin_key(self.name, self.number)


def parse_pins(raw: str, symbol_name: str) -> list[Pin]:
    marks = [(match.start(), match.group(1)) for match in re.finditer(r'\(symbol "([^"]+)"', raw)]
    pin_re = re.compile(
        r'\(pin (\w+) \w+\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)'
        r'.*?\(name "([^"]*)".*?\(number "([^"]*)"',
        re.S,
    )
    pins: list[Pin] = []
    unit_re = re.compile(rf"^{re.escape(symbol_name)}_(\d+)_\d+$")
    for match in pin_re.finditer(raw):
        unit = 1
        for pos, sym in marks:
            if pos >= match.start():
                break
            found = unit_re.match(sym)
            if found:
                unit = int(found.group(1))
        pins.append(
            Pin(
                number=match.group(6),
                name=match.group(5),
                electrical=match.group(1),
                x=float(match.group(2)),
                y=float(match.group(3)),
                angle=int(match.group(4)),
                unit=unit,
            )
        )
    if not pins:
        raise RuntimeError(f"no pins parsed from {symbol_name}")
    return pins


class Libraries:
    def __init__(self) -> None:
        self._file_cache: dict[str, str] = {}
        self.embedded: dict[str, str] = {}
        self.pins: dict[str, list[Pin]] = {}

    def _read(self, filename: str) -> str:
        if filename not in self._file_cache:
            self._file_cache[filename] = (SYM_DIR / filename).read_text(encoding="utf-8", errors="ignore")
        return self._file_cache[filename]

    def _raw(self, filename: str, name: str, depth: int = 0) -> str:
        if depth > 6:
            raise RuntimeError(f"alias loop at {name}")
        block = extract_symbol(self._read(filename), name)
        extends = re.search(r'\(extends "([^"]+)"', block)
        if not extends:
            return block
        parent_name = extends.group(1)
        parent = self._raw(filename, parent_name, depth + 1)
        parent = re.sub(
            rf'^\t?\(symbol "{re.escape(parent_name)}"',
            f'(symbol "{name}"',
            parent,
            count=1,
        )
        parent = parent.replace(f'(symbol "{parent_name}_', f'(symbol "{name}_')
        for key, value in child_properties(block).items():
            parent = replace_property(parent, key, value)
        return parent

    def use(self, filename: str, name: str) -> str:
        lib_id = f"{filename.removesuffix('.kicad_sym')}:{name}"
        if lib_id in self.embedded:
            return lib_id
        # Expand aliases so the sheet still has pins if a library is missing.
        # KiCad may warn that an expanded alias does not byte-match the library stub.
        flat = self._raw(filename, name)
        flat = re.sub(rf'^\t?\(symbol "{re.escape(name)}"', f'(symbol "{lib_id}"', flat, count=1)
        self.embedded[lib_id] = flat
        self.pins[lib_id] = parse_pins(flat, name)
        return lib_id


def outward(angle: int) -> tuple[float, float]:
    rad = math.radians(angle)
    # The pin angle points from the connection back into the body.
    return (-math.cos(rad), -math.sin(rad))


class Sheet:
    def __init__(self, libs: Libraries) -> None:
        self.libs = libs
        self.chunks: list[str] = []
        self.records: list[dict] = []
        self.ref_counts: dict[str, int] = {}
        self.power_count = 0
        self.flagged: set[str] = set()
        self.root_uuid = uid()
        self.bounds = [1e9, 1e9, -1e9, -1e9]
        self.x = 30.0
        self.y = 2000.0
        self.row_depth = 0.0

    def _touch(self, x: float, y: float) -> None:
        self.bounds[0] = min(self.bounds[0], x)
        self.bounds[1] = min(self.bounds[1], y)
        self.bounds[2] = max(self.bounds[2], x)
        self.bounds[3] = max(self.bounds[3], y)

    def alloc(self, width: float, height: float) -> tuple[float, float]:
        if self.x + width > 1160:
            self.x = 30.0
            self.y -= self.row_depth + 18
            self.row_depth = 0.0
        # Library pins sit on a 1.27 mm grid. The symbol origin has to as well,
        # or every wire end is off-grid and a 2.54 mm flag lead can hit the next pin.
        origin = (
            r2(round((self.x + width / 2) / 1.27) * 1.27),
            r2(round((self.y - height / 2) / 1.27) * 1.27),
        )
        self.x += width
        self.row_depth = max(self.row_depth, height)
        return origin

    def newline(self) -> None:
        self.x = 30.0
        self.y -= self.row_depth + 22
        self.row_depth = 0.0

    def next_ref(self, prefix: str) -> str:
        self.ref_counts[prefix] = self.ref_counts.get(prefix, 0) + 1
        return f"{prefix}{self.ref_counts[prefix]}"

    def add(
        self,
        filename: str,
        symbol: str,
        ref_prefix: str,
        value: str,
        origin: tuple[float, float],
        nets: dict[str, str | None],
        footprint: str = "",
        on_board: bool = True,
        width: float = 0,
        height: float = 0,
    ) -> str:
        if width:
            origin = self.alloc(width, height)
        lib_id = self.libs.use(filename, symbol)
        pins = self.libs.pins[lib_id]
        if not footprint:
            found = re.search(r'\(property "Footprint" "([^"]*)"', self.libs.embedded[lib_id])
            footprint = found.group(1) if found else ""
        ref = self.next_ref(ref_prefix)
        missing = []
        assigned: list[tuple[Pin, str | None]] = []
        for pin in pins:
            if pin.key not in nets:
                missing.append(pin.key)
            else:
                assigned.append((pin, nets[pin.key]))
        if missing:
            have = sorted({pin.key for pin in pins})
            raise KeyError(f"{ref} {lib_id} missing {sorted(set(missing))}; have {have}")
        # Unit 0 is the body shared by every unit. A one-unit symbol sometimes
        # keeps its pins there. Units 2 and up would need a second drawing.
        pin_units = sorted({pin.unit for pin in pins})
        if any(unit > 1 for unit in pin_units):
            raise RuntimeError(f"{lib_id} has pin units {pin_units}, this generator places one unit only")
        top = max(pin.y for pin in pins)
        ox, oy = r2(origin[0]), r2(origin[1])
        self._emit_symbol(
            lib_id=lib_id,
            ref=ref,
            value=value,
            footprint=footprint,
            x=ox,
            y=oy,
            ref_y=r2(oy + top + 3.5),
            pins=pins,
            on_board=on_board,
        )
        pad_nets = []
        for pin, net in assigned:
            # Symbol libraries use +Y up. KiCad places a symbol by mirroring that Y.
            world = (r2(ox + pin.x), r2(oy - pin.y))
            self._connect(world, pin.angle, net)
            if on_board:
                pad_nets.append({"num": pin.number, "net": net or ""})
        if on_board and footprint:
            self.records.append(
                {
                    "ref": ref,
                    "value": value,
                    "lib_id": lib_id,
                    "footprint": footprint,
                    "pads": pad_nets,
                }
            )
        return ref

    def _emit_symbol(
        self,
        lib_id: str,
        ref: str,
        value: str,
        footprint: str,
        x: float,
        y: float,
        ref_y: float,
        pins: list[Pin],
        on_board: bool,
        power: bool = False,
    ) -> None:
        board = "yes" if on_board else "no"
        pin_forms = "\n".join(
            f'\t\t(pin "{pin.number}"\n\t\t\t(uuid "{uid()}")\n\t\t)' for pin in pins
        )
        # One graphical unit: every pin on these symbols lives on unit 1.
        # Duplicate pin numbers (several GND pins of one package) each need an entry.
        seen: list[str] = []
        unique_pin_forms = []
        for pin in pins:
            if pin.number in seen:
                continue
            seen.append(pin.number)
            unique_pin_forms.append(
                f'\t\t(pin "{pin.number}"\n\t\t\t(uuid "{uid()}")\n\t\t)'
            )
        pin_forms = "\n".join(unique_pin_forms)
        power_line = "\t\t(power)\n" if power else ""
        self.chunks.append(
            f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board {board})
\t\t(dnp no)
{power_line}\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x} {ref_y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {x} {r2(ref_y - 2.54)} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Footprint" "{footprint}"
\t\t\t(at {x} {y} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {x} {y} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
{pin_forms}
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{self.root_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""
        )

    def _connect(self, xy: tuple[float, float], angle: int, net: str | None) -> None:
        self._touch(xy[0], xy[1])
        if net is None:
            self.chunks.append(f'\t(no_connect\n\t\t(at {xy[0]} {xy[1]})\n\t\t(uuid "{uid()}")\n\t)')
            return
        file_x, file_y = outward(angle)
        # Same Y mirror as the pin position, so the stub leaves the body.
        end = (r2(xy[0] + file_x * 2.54), r2(xy[1] - file_y * 2.54))
        self._touch(end[0], end[1])
        self.chunks.append(
            f"""\t(wire
\t\t(pts
\t\t\t(xy {xy[0]} {xy[1]}) (xy {end[0]} {end[1]})
\t\t)
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uid()}")
\t)"""
        )
        if net in POWER_SYMS:
            self._power(POWER_SYMS[net], end)
            if net in FLAG_NETS:
                self._flag_once(net, end)
        else:
            self._label(net, end)
            if net in FLAG_NETS:
                self._flag_once(net, end)

    def _power(self, symbol: str, xy: tuple[float, float]) -> None:
        lib_id = self.libs.use("power.kicad_sym", symbol)
        self.power_count += 1
        ref = f"#PWR{self.power_count:04d}"
        pins = self.libs.pins[lib_id]
        seen_numbers: list[str] = []
        pin_lines: list[str] = []
        for pin in pins:
            if pin.number in seen_numbers:
                continue
            seen_numbers.append(pin.number)
            pin_lines.append(f'\t\t(pin "{pin.number}"\n\t\t\t(uuid "{uid()}")\n\t\t)')
        pin_forms = "\n".join(pin_lines)
        # Power-symbol graphics hang off the connection point. Keep the value visible.
        self.chunks.append(
            f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {xy[0]} {xy[1]} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {xy[0]} {r2(xy[1] - 4)} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "{symbol}"
\t\t\t(at {xy[0]} {r2(xy[1] - 2.2)} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {xy[0]} {xy[1]} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {xy[0]} {xy[1]} 0)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
{pin_forms}
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{self.root_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""
        )

    def _flag_once(self, net: str, xy: tuple[float, float]) -> None:
        if net in self.flagged:
            return
        self.flagged.add(net)
        # Same point as the stub end. A lead away from here can land on the next pin.
        self._power("PWR_FLAG", xy)

    def _label(self, name: str, xy: tuple[float, float]) -> None:
        self.chunks.append(
            f"""\t(global_label "{name}"
\t\t(shape passive)
\t\t(at {xy[0]} {xy[1]} 0)
\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t(uuid "{uid()}")
\t)"""
        )

    def note(self, text: str, x: float, y: float, size: float = 1.6) -> None:
        text = text.replace("\\n", "\n")
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        self._touch(x, y)
        self.chunks.append(
            f"""\t(text "{escaped}"
\t\t(exclude_from_sim no)
\t\t(at {r2(x)} {r2(y)} 0)
\t\t(effects (font (size {size} {size})) (justify left top))
\t\t(uuid "{uid()}")
\t)"""
        )

    def render(self) -> str:
        margin = 30
        # Page origin is the lower left. The sheet must be taller than the highest symbol.
        width = max(420, self.bounds[2] + margin)
        height = max(297, self.bounds[3] + margin)
        libs = "\n".join(self.libs.embedded.values())
        body = "\n".join(self.chunks)
        return f"""(kicad_sch
\t(version 20250610)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{self.root_uuid}")
\t(paper "User" {r2(width)} {r2(height)})
\t(title_block
\t\t(title "MAIZE phase 5 controller")
\t\t(date "2026-10-20")
\t\t(rev "A")
\t\t(company "PPML")
\t\t(comment 1 "Design assumptions. Not a measured field pinout.")
\t\t(comment 2 "24 V DC coils only. Hornet pin 2 is not connected.")
\t\t(comment 3 "RS-485 ground is isolated from Uno ground.")
\t\t(comment 4 "Do not apply USB power and the 9 V logic input together.")
\t)
\t(lib_symbols
{libs}
\t)
{body}
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
\t(embedded_fonts no)
)
"""


def two_pin(net_a: str | None, net_b: str | None) -> dict[str, str | None]:
    return {"#1": net_a, "#2": net_b}


def resistor(sheet: Sheet, value: str, a: str | None, b: str | None, width: float = 22, height: float = 18) -> None:
    sheet.add("Device.kicad_sym", "R", "R", value, (0, 0), two_pin(a, b), FP_R, True, width, height)


def capacitor(sheet: Sheet, value: str, a: str | None, b: str | None) -> None:
    sheet.add("Device.kicad_sym", "C", "C", value, (0, 0), two_pin(a, b), FP_C, True, 20, 18)


def polarized(sheet: Sheet, value: str, plus: str, minus: str) -> None:
    # Pin 1 of the KiCad polarized-capacitor symbol is the positive terminal.
    sheet.add(
        "Device.kicad_sym", "C_Polarized", "C", value, (0, 0),
        {"#1": plus, "#2": minus}, FP_CP, True, 20, 18,
    )


def diode(sheet: Sheet, value: str, cathode: str, anode: str, small: bool = False) -> None:
    symbol = "1N4148" if small else "1N4007"
    footprint = FP_D_SMALL if small else FP_D
    sheet.add(
        "Diode.kicad_sym", symbol, "D", value, (0, 0),
        {"K": cathode, "A": anode}, footprint, True, 22, 16,
    )


def led(sheet: Sheet, anode_net: str, cathode_net: str = "GND") -> None:
    sheet.add(
        "Device.kicad_sym", "LED", "D", "LED", (0, 0),
        {"K": cathode_net, "A": anode_net}, FP_LED, True, 20, 16,
    )


def header(sheet: Sheet, value: str, nets: list[str | None], footprint: str) -> None:
    count = len(nets)
    symbol = f"Conn_01x{count:02d}"
    mapping = {f"#{index + 1}": net for index, net in enumerate(nets)}
    sheet.add(
        "Connector_Generic.kicad_sym", symbol, "J", value, (0, 0),
        mapping, footprint, True, 16, 8 + 6 * count,
    )


def build(sheet: Sheet) -> None:
    sheet.note(
        "MAIZE PHASE 5 CONTROLLER  —  read this before believing a wire\\n"
        "Assumptions, because the gate, pilot, and sensor terminals are still unmeasured:\\n"
        "1. Coil drivers are 24 V DC, about 0.5 A each. An AC coil does not belong on this board.\\n"
        "2. Opening power is a relay contact. It drops if the processor stops kicking the watchdog,\\n"
        "   the enable key is open, the mode is OFF, or STOP is pressed.\\n"
        "3. Close-coil force jumpers stay OPEN until a double-acting actuator is proven.\\n"
        "   Spring-return valves must leave those jumpers empty. Loss of 24 V then lets the spring close.\\n"
        "4. Sensor inputs are dry contacts. The board puts about 5 mA through a closed contact.\\n"
        "5. Hornet DE-9 follows the archived IGM402 map: 9 = data B (+), 6 = data A (-), 4 = isolated reference.\\n"
        "   Pin 2 (gauge 20-28 V) is not connected. Relay pins 1, 5, 7 are brought out and are not a filament proof.\\n"
        "6. Cold-ready, filament-off, and pump-ready are contact landings waiting for the real measurement.\\n"
        "7. The scroll pump, Cryo-Torr, and CTI compressor are not powered or started by this board.\\n"
        "8. Logic input is 9-12 V at J_LOGIC. Do not also power the Uno from USB.\\n"
        "9. UART 7-bit I2C address is 0x48 (A1 and A0 tied to 3.3 V). Baud is a firmware choice after the Hornet manual matches.\\n"
        "10. Active-low inputs: a closed contact reads as true, same idea as the phase 1 buttons.",
        30, 2140, 1.4,
    )
    sheet.y = 1980
    sheet.x = 30
    sheet.row_depth = 0

    # --- Logic and coil power -------------------------------------------------
    sheet.note("POWER  9-12 V logic, separate 24 V coils. Gauge 24 V stays on the Hornet supply.", 30, sheet.y, 2.0)
    sheet.newline()
    header(sheet, "J_LOGIC", ["+9V_RAW", "GND"], FP_TB2)
    sheet.add("Device.kicad_sym", "Fuse", "F", "500mA", (0, 0), two_pin("+9V_RAW", "+9V_SW"), FP_FUSE, True, 18, 20)
    diode(sheet, "1N4007", "+9V", "+9V_SW")
    polarized(sheet, "10uF/25V", "+9V", "GND")
    sheet.add(
        "Regulator_Linear.kicad_sym", "AMS1117-5.0", "U", "AMS1117-5.0", (0, 0),
        {"GND": "GND", "VO": "+5V", "VI": "+9V"},
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", True, 40, 28,
    )
    polarized(sheet, "22uF/16V", "+5V", "GND")
    capacitor(sheet, "100n", "+5V", "GND")
    led_net = "LED_5V"
    resistor(sheet, "2.2k", "+5V", led_net)
    led(sheet, led_net)
    header(sheet, "J_COIL24", ["+24V_RAW", "GND"], FP_TB2)
    sheet.add("Device.kicad_sym", "Fuse", "F", "3A", (0, 0), two_pin("+24V_RAW", "+24V_FUSED"), FP_FUSE, True, 18, 20)
    sheet.add("Device.kicad_sym", "Fuse", "F", "2A", (0, 0), two_pin("+24V_FUSED", "+24V_CLOSE"), FP_FUSE, True, 18, 20)
    sheet.newline()

    # 24 V present, and opening-rail present, divided down for the Uno.
    resistor(sheet, "100k", "+24V_FUSED", "SENSE_24V")
    resistor(sheet, "15k", "SENSE_24V", "GND")
    sheet.add("Device.kicad_sym", "D_Zener", "D", "5.1V", (0, 0), {"K": "SENSE_24V", "A": "GND"}, FP_D_SMALL, True, 22, 16)
    resistor(sheet, "100k", "+24V_OPEN", "SENSE_OPEN")
    resistor(sheet, "15k", "SENSE_OPEN", "GND")
    sheet.add("Device.kicad_sym", "D_Zener", "D", "5.1V", (0, 0), {"K": "SENSE_OPEN", "A": "GND"}, FP_D_SMALL, True, 22, 16)
    resistor(sheet, "4.7k", "+24V_OPEN", "LED_OPEN_A")
    led(sheet, "LED_OPEN_A")
    sheet.newline()

    # --- 3.3 V island for the UART and the isolator's logic side --------------
    sheet.note("3.3 V UART ISLAND  SC16IS752 is not a 5 V chip. I2C is level-shifted.", 30, sheet.y, 2.0)
    sheet.newline()
    sheet.add(
        "Regulator_Linear.kicad_sym", "AMS1117-3.3", "U", "AMS1117-3.3", (0, 0),
        {"GND": "GND", "VO": "+3V3", "VI": "+5V"},
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", True, 40, 28,
    )
    polarized(sheet, "10uF/16V", "+5V", "GND")
    polarized(sheet, "22uF/10V", "+3V3", "GND")
    capacitor(sheet, "100n", "+3V3", "GND")
    sheet.newline()

    # --- Watchdog and the two safety relays ----------------------------------
    sheet.note(
        "OPENING POWER  both MOSFETs must be on. Watchdog healthy AND panel chain closed.\\n"
        "FORCE CLOSE  relay NC shorts close-coil low sides to ground only while the watchdog is NOT healthy.",
        30, sheet.y, 1.8,
    )
    sheet.newline()
    sheet.add(
        "Power_Supervisor.kicad_sym", "TPS3823-xxDBV", "U", "TPS3823-33", (0, 0),
        {"RESET": "WD_OK", "GND": "GND", "MR": "STOP_NODE", "WDI": "WDI", "VDD": "+5V"},
        "Package_TO_SOT_SMD:SOT-23-5", True, 46, 30,
    )
    capacitor(sheet, "100n", "+5V", "GND")
    resistor(sheet, "10k", "STOP_NODE", "+5V")
    resistor(sheet, "1k", "WDI_UNO", "WDI")

    # Panel chain: key, then manual OR auto, then STOP normally-closed.
    sheet.add(
        "Switch.kicad_sym", "SW_SPST", "SW", "ENABLE_KEY", (0, 0),
        {"A": "+5V", "B": "KEY_OK"}, "", False, 28, 16,
    )
    sheet.add(
        "Switch.kicad_sym", "SW_SPST", "SW", "MODE_MANUAL", (0, 0),
        {"A": "KEY_OK", "B": "MODE_MAN"}, "", False, 30, 16,
    )
    sheet.add(
        "Switch.kicad_sym", "SW_SPST", "SW", "MODE_AUTO", (0, 0),
        {"A": "KEY_OK", "B": "MODE_AUTO"}, "", False, 28, 16,
    )
    diode(sheet, "1N4148", "ENABLE_RAW", "MODE_MAN", small=True)
    diode(sheet, "1N4148", "ENABLE_RAW", "MODE_AUTO", small=True)
    sheet.add(
        "Switch.kicad_sym", "SW_SPST", "SW", "STOP_NC_AT_REST", (0, 0),
        {"A": "ENABLE_RAW", "B": "ENABLE_SW"}, "", False, 36, 16,
    )
    resistor(sheet, "100k", "ENABLE_SW", "GND")
    resistor(sheet, "100k", "MODE_MAN", "GND")
    resistor(sheet, "100k", "MODE_AUTO", "GND")
    sheet.add(
        "Switch.kicad_sym", "SW_Push", "SW", "STOP_NO", (0, 0),
        {"#1": "STOP_NODE", "#2": "GND"}, "", False, 24, 16,
    )
    sheet.newline()

    # K_OPEN coil from 24 V, low side through two MOSFETs in series.
    sheet.add(
        "Relay.kicad_sym", "G5LE-1", "K", "G5LE-1-DC24", (0, 0),
        {"#1": "+24V_FUSED", "#5": "KOPEN_LOW", "#2": "+24V_FUSED", "#3": "+24V_OPEN", "#4": None},
        "Relay_THT:Relay_SPDT_Omron-G5LE-1", True, 40, 32,
    )
    diode(sheet, "1N4007", "+24V_FUSED", "KOPEN_LOW")
    nmos = {"G": "ENABLE_GATE", "S": "KOPEN_MID", "D": "KOPEN_LOW"}
    sheet.add(
        "Transistor_FET.kicad_sym", "2N7002", "Q", "2N7002", (0, 0),
        nmos, "Package_TO_SOT_SMD:SOT-23", True, 28, 22,
    )
    sheet.add(
        "Transistor_FET.kicad_sym", "2N7002", "Q", "2N7002", (0, 0),
        {"G": "WD_GATE", "S": "GND", "D": "KOPEN_MID"},
        "Package_TO_SOT_SMD:SOT-23", True, 28, 22,
    )
    resistor(sheet, "1k", "ENABLE_SW", "ENABLE_GATE")
    resistor(sheet, "100k", "ENABLE_GATE", "GND")
    resistor(sheet, "1k", "WD_OK", "WD_GATE")
    resistor(sheet, "100k", "WD_GATE", "GND")
    sheet.add("Device.kicad_sym", "D_Zener", "D", "12V", (0, 0), {"K": "ENABLE_GATE", "A": "GND"}, FP_D_SMALL, True, 22, 16)
    sheet.add("Device.kicad_sym", "D_Zener", "D", "12V", (0, 0), {"K": "WD_GATE", "A": "GND"}, FP_D_SMALL, True, 22, 16)
    sheet.newline()

    # Force-close relay. NC (pin 4) is closed while the coil is off.
    # Datasheet bottom view: coil = 1 and 5, COM = 2, NO = 3, NC = 4.
    sheet.add(
        "Relay.kicad_sym", "G5LE-1", "K", "G5LE-1-DC24", (0, 0),
        {"#1": "+24V_FUSED", "#5": "KFORCE_LOW", "#2": "FORCE_BUS", "#3": None, "#4": "GND"},
        "Relay_THT:Relay_SPDT_Omron-G5LE-1", True, 40, 32,
    )
    diode(sheet, "1N4007", "+24V_FUSED", "KFORCE_LOW")
    sheet.add(
        "Transistor_FET.kicad_sym", "2N7002", "Q", "2N7002", (0, 0),
        {"G": "FORCE_GATE", "S": "GND", "D": "KFORCE_LOW"},
        "Package_TO_SOT_SMD:SOT-23", True, 28, 22,
    )
    resistor(sheet, "1k", "WD_OK", "FORCE_GATE")
    resistor(sheet, "100k", "FORCE_GATE", "GND")
    sheet.newline()

    # --- Uno and the sockets it plugs into -----------------------------------
    sheet.note("UNO R3  sockets are the fabricated part. The Uno symbol is the plugged-in board, not a copper part.", 30, sheet.y, 2.0)
    sheet.newline()
    # Keys are the symbol's pin names. Repeated names (both GND pins, both SDA pins)
    # correctly share one net.
    uno_nets = {
        "NC": None,
        "IOREF": None,
        "RESET": None,
        "3V3": "UNO_3V3",
        "+5V": "UNO_5V",
        "GND": "GND",
        "VIN": "+9V",
        "A0": "SENSE_24V",
        "A1": "SENSE_OPEN",
        "A2": None,
        "A3": None,
        "SDA/A4": "SDA_5V",
        "SCL/A5": "SCL_5V",
        "D0/RX": None,
        "D1/TX": None,
        "D2": "INT_IN",
        "D3": "UART_IRQ",
        "D4": "WDI_UNO",
        "D5": "CRYO_REQ",
        "D6": "ROUGH_REQ",
        "D7": "VENT_REQ",
        "D8": "ARM_BTN",
        "D9": "STOP_NODE",
        "D10": "START_BTN",
        "D11": "MODE_MAN",
        "D12": "MODE_AUTO",
        "D13": None,
        "AREF": None,
    }
    sheet.add(
        "MCU_Module.kicad_sym", "Arduino_UNO_R3", "A", "Arduino_UNO_R3", (0, 0),
        uno_nets, "Module:Arduino_UNO_R3", False, 150, 90,
    )
    capacitor(sheet, "100n", "UNO_5V", "GND")
    capacitor(sheet, "100n", "UNO_3V3", "GND")
    header(sheet, "J_UNO_PWR", [
        None, None, None, "UNO_3V3", "UNO_5V", "GND", "GND", "+9V",
    ], FP_SOCK8)
    header(sheet, "J_UNO_ANALOG", [
        "SENSE_24V", "SENSE_OPEN", None, None, "SDA_5V", "SCL_5V",
    ], FP_SOCK6)
    header(sheet, "J_UNO_D0", [
        None, None, "INT_IN", "UART_IRQ", "WDI_UNO", "CRYO_REQ", "ROUGH_REQ", "VENT_REQ",
    ], FP_SOCK8)
    header(sheet, "J_UNO_D8", [
        "ARM_BTN", "STOP_NODE", "START_BTN", "MODE_MAN", "MODE_AUTO", None, "GND", None, "SDA_5V", "SCL_5V",
    ], FP_SOCK10)
    sheet.newline()

    # Panel harness. Switches are off the board; the terminal block is on it.
    sheet.note("PANEL  momentary requests to ground. Mode and enable pass 5 V only as far as the relay gates.", 30, sheet.y, 2.0)
    sheet.newline()
    header(sheet, "J_PANEL", [
        "GND", "+5V", "KEY_OK", "MODE_MAN", "MODE_AUTO", "ENABLE_RAW", "ENABLE_SW",
        "STOP_NODE", "CRYO_REQ", "ROUGH_REQ",
    ], FP_TB10)
    header(sheet, "J_PANEL_B", ["VENT_REQ", "ARM_BTN", "START_BTN", "GND"], FP_TB4)
    for name, net in (
        ("CRYO_REQ", "CRYO_REQ"),
        ("ROUGH_REQ", "ROUGH_REQ"),
        ("VENT_REQ", "VENT_REQ"),
        ("ARM", "ARM_BTN"),
        ("START", "START_BTN"),
    ):
        sheet.add(
            "Switch.kicad_sym", "SW_Push", "SW", name, (0, 0),
            {"#1": net, "#2": "GND"}, "", False, 24, 14,
        )
        resistor(sheet, "10k", net, "+5V")
    header(sheet, "J_DISPLAY", ["GND", "+5V", "SDA_5V", "SCL_5V"], FP_TB4)
    sheet.newline()

    # --- I2C level shift, expanders, UART, isolated RS-485 -------------------
    sheet.note("I2C  5 V expanders, 3.3 V UART. Pull-ups on both sides of the shifter.", 30, sheet.y, 2.0)
    sheet.newline()
    for sig5, sig3 in (("SDA_5V", "SDA_3V3"), ("SCL_5V", "SCL_3V3")):
        sheet.add(
            "Transistor_FET.kicad_sym", "BSS138", "Q", "BSS138", (0, 0),
            {"G": "+3V3", "S": sig3, "D": sig5},
            "Package_TO_SOT_SMD:SOT-23", True, 28, 22,
        )
        resistor(sheet, "4.7k", sig5, "+5V")
        resistor(sheet, "4.7k", sig3, "+3V3")
    sheet.newline()

    def expander(value: str, nets: dict[str, str | None]) -> None:
        sheet.add(
            "Interface_Expansion.kicad_sym", "MCP23017x-x-SP", "U", value, (0, 0),
            nets, "Package_DIP:DIP-28_W7.62mm", True, 70, 70,
        )
        capacitor(sheet, "100n", "+5V", "GND")

    expander("MCP23017_OUT_0x20", {
        "GPB0": "GPIO_SPARE0",
        "GPB1": "GPIO_SPARE1",
        "GPB2": None,
        "GPB3": None,
        "GPB4": None,
        "GPB5": None,
        "GPB6": None,
        "GPB7": "GPIO_LED_SEQ",
        "VDD": "+5V",
        "VSS": "GND",
        "NC": None,
        "SCK": "SCL_5V",
        "SDA": "SDA_5V",
        "A0": "GND",
        "A1": "GND",
        "A2": "GND",
        "RESET": "WD_OK",
        "INTB": "OUT_INT",
        "INTA": "OUT_INT",
        "GPA0": "GPIO_CRYO_OPEN",
        "GPA1": "GPIO_CRYO_CLOSE",
        "GPA2": "GPIO_ROUGH_OPEN",
        "GPA3": "GPIO_ROUGH_CLOSE",
        "GPA4": "GPIO_VENT_OPEN",
        "GPA5": "GPIO_VENT_CLOSE",
        "GPA6": "GPIO_LED_FAULT",
        "GPA7": "GPIO_LED_ARMED",
    })
    resistor(sheet, "10k", "OUT_INT", "+5V")
    sheet.newline()

    expander("MCP23017_IN_0x21", {
        "GPB0": "IN_PS101",
        "GPB1": "IN_P102",
        "GPB2": "IN_IGOFF",
        "GPB3": "IN_SPARE_A",
        "GPB4": "IN_SPARE_B",
        "GPB5": None,
        "GPB6": None,
        "GPB7": None,
        "VDD": "+5V",
        "VSS": "GND",
        "NC": None,
        "SCK": "SCL_5V",
        "SDA": "SDA_5V",
        "A0": "+5V",
        "A1": "GND",
        "A2": "GND",
        "RESET": "WD_OK",
        "INTB": "INT_IN",
        "INTA": "INT_IN",
        "GPA0": "IN_ZS101C",
        "GPA1": "IN_ZS101O",
        "GPA2": "IN_ZS102C",
        "GPA3": "IN_ZS102O",
        "GPA4": "IN_ZS103C",
        "GPA5": "IN_ZS103O",
        "GPA6": "IN_TI101",
        "GPA7": None,
    })
    resistor(sheet, "10k", "INT_IN", "+5V")
    sheet.newline()

    # Status LEDs driven by the output expander. Command lamps, not position proof.
    for net in ("GPIO_LED_FAULT", "GPIO_LED_ARMED", "GPIO_LED_SEQ", "GPIO_SPARE0", "GPIO_SPARE1"):
        anode = net + "_LED"
        resistor(sheet, "2.2k", net, anode)
        led(sheet, anode)
    sheet.newline()

    uart = {
        "RTSA": None,
        "CTSA": "GND",
        "TXA": "UART_TX",
        "RXA": "UART_RX",
        "RESET": "UART_RESET",
        "XTAL1": "XTAL1",
        "XTAL2": "XTAL2",
        "VDD": "+3V3",
        "I2C/SPI": "+3V3",
        "A0/CS": "+3V3",
        "A1/SI": "+3V3",
        "n.c./SO": None,
        "SCL/SCLK": "SCL_3V3",
        "SDA/VSS": "SDA_3V3",
        "IRQ": "UART_IRQ",
        "CTSB": "GND",
        "RTSB": None,
        "GPIO0/DSRB": "RS485_DE",
        "GPIO1/DTRB": None,
        "GPIO2/CDB": None,
        "GPIO3/RIB": None,
        "VSS": "GND",
        "TXB": None,
        "RXB": "GND",
        "GPIO4/DSRA": None,
        "GPIO5/DTRA": None,
        "GPIO6/CDA": None,
        "GPIO7/RIA": None,
    }
    sheet.add(
        "Interface_UART.kicad_sym", "SC16IS752IPW", "U", "SC16IS752IPW", (0, 0),
        uart, "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm", True, 70, 70,
    )
    capacitor(sheet, "100n", "+3V3", "GND")
    resistor(sheet, "1k", "UART_IRQ", "+3V3")
    # Diode lets the 5 V watchdog pull the 3.3 V reset down without feeding 5 V in.
    diode(sheet, "1N4148", "WD_OK", "UART_RESET", small=True)
    resistor(sheet, "10k", "UART_RESET", "+3V3")
    sheet.add(
        "Device.kicad_sym", "Crystal", "Y", "1.8432MHz", (0, 0),
        {"#1": "XTAL1", "#2": "XTAL2"}, FP_XTAL, True, 24, 16,
    )
    capacitor(sheet, "22p", "XTAL1", "GND")
    capacitor(sheet, "22p", "XTAL2", "GND")
    resistor(sheet, "1M", "XTAL1", "XTAL2")
    resistor(sheet, "100k", "RS485_DE", "GND")
    sheet.newline()

    iso = {
        "Vcc1": "+3V3",
        "GND1": "GND",
        "R": "UART_RX",
        "RE": "RS485_DE",
        "DE": "RS485_DE",
        "D": "UART_TX",
        "GND2": "GND_ISO",
        "NC": None,
        "A": "BUS_A",
        "B": "BUS_B",
        "Vcc2": "+5V_ISO",
    }
    sheet.add(
        "Interface_UART.kicad_sym", "ISO3082DW", "U", "ISO3082DW", (0, 0),
        iso, "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm", True, 70, 55,
    )
    capacitor(sheet, "100n", "+3V3", "GND")
    sheet.add(
        "Converter_DCDC_Isolated.kicad_sym", "CRE1S0505SC", "U", "CRE1S0505SC", (0, 0),
        {"-VIN": "GND", "+VIN": "+5V", "-VOUT": "GND_ISO", "+VOUT": "+5V_ISO"},
        "", True, 40, 30,
    )
    polarized(sheet, "10uF/16V", "+5V", "GND")
    polarized(sheet, "10uF/16V", "+5V_ISO", "GND_ISO")
    capacitor(sheet, "100n", "+5V_ISO", "GND_ISO")
    # Fail-safe bias keeps an open bus in the idle state. Termination is a shunt, off by default.
    resistor(sheet, "680", "+5V_ISO", "BUS_A")
    resistor(sheet, "680", "BUS_B", "GND_ISO")
    sheet.add(
        "Jumper.kicad_sym", "Jumper_2_Open", "JP", "TERM_120_FIT_TO_ENABLE", (0, 0),
        {"A": "BUS_A", "B": "TERM_MID"}, FP_HDR2, True, 24, 14,
    )
    resistor(sheet, "120", "TERM_MID", "BUS_B")
    sheet.newline()

    sheet.note(
        "HORNET DE-9 MALE  plugs into the gauge's female RS-485 socket.\\n"
        "A of the ISO3082 (non-inverting) lands on pin 9. B lands on pin 6. Swap only if the idle bus is backwards.\\n"
        "Pin 4 is isolated ground. Do not tie it to Uno ground. Pin 2 is not connected.",
        30, sheet.y, 1.8,
    )
    sheet.newline()
    de9 = {f"#{n}": None for n in range(1, 10)}
    de9["#9"] = "BUS_A"
    de9["#6"] = "BUS_B"
    de9["#4"] = "GND_ISO"
    de9["#1"] = "HORNET_RLY_1"
    de9["#5"] = "HORNET_RLY_5"
    de9["#7"] = "HORNET_RLY_7"
    sheet.add("Connector.kicad_sym", "DE9_Pins", "J", "J_HORNET", (0, 0), de9, FP_DE9, True, 40, 40)
    header(sheet, "J_HORNET_RELAY_UNCOMMITTED", ["HORNET_RLY_1", "HORNET_RLY_5", "HORNET_RLY_7"], FP_TB3)
    sheet.newline()

    # --- Contact inputs -------------------------------------------------------
    sheet.note(
        "CONTACT INPUTS  +24 V through 4.7k and the opto LED. Closed contact = expander pin low = true.\\n"
        "Spares are landings only. They are not a turbo interlock.",
        30, sheet.y, 1.8,
    )
    sheet.newline()
    sensors = [
        ("J_ZS101C", "IN_ZS101C", "cryo closed"),
        ("J_ZS101O", "IN_ZS101O", "cryo open"),
        ("J_ZS102C", "IN_ZS102C", "rough closed"),
        ("J_ZS102O", "IN_ZS102O", "rough open"),
        ("J_ZS103C", "IN_ZS103C", "vent closed"),
        ("J_ZS103O", "IN_ZS103O", "vent open"),
        ("J_TI101", "IN_TI101", "cryo ready"),
        ("J_PS101", "IN_PS101", "air pressure ok"),
        ("J_P102", "IN_P102", "rough pump ready"),
        ("J_IGOFF", "IN_IGOFF", "filament off contact"),
        ("J_SPARE_A", "IN_SPARE_A", "spare"),
        ("J_SPARE_B", "IN_SPARE_B", "spare"),
    ]
    for index, (ref_value, gpio, label) in enumerate(sensors):
        # Contact lands across the terminal. The resistor, not the contact, limits LED current.
        anode = f"OPTO_A_{index}"
        sig = f"SIG_{index}"
        sheet.add(
            "Isolator.kicad_sym", "PC817", "U", "PC817", (0, 0),
            {"#1": anode, "#2": "GND", "#3": "GND", "#4": gpio},
            "Package_DIP:DIP-4_W7.62mm", True, 36, 24,
        )
        resistor(sheet, "4.7k", sig, anode)
        resistor(sheet, "10k", gpio, "+5V")
        header(sheet, ref_value, ["+24V_FUSED", sig], FP_TB2)
        sheet.add(
            "Switch.kicad_sym", "SW_SPST", "SW", label, (0, 0),
            {"A": "+24V_FUSED", "B": sig}, "", False, 28, 14,
        )
        if (index + 1) % 3 == 0:
            sheet.newline()
    sheet.newline()

    # --- Coil drivers ---------------------------------------------------------
    sheet.note(
        "COIL DRIVERS  low-side IRLZ44N, flyback on the terminal, gate clamped.\\n"
        "OPEN coils take the inhibited 24 V rail. CLOSE coils take the fused rail that stays up.\\n"
        "A close channel's force diode is armed only when its jumper shunt is fitted.",
        30, sheet.y, 1.8,
    )
    sheet.newline()
    drivers = [
        ("CRYO_OPEN", "GPIO_CRYO_OPEN", "+24V_OPEN", False),
        ("CRYO_CLOSE", "GPIO_CRYO_CLOSE", "+24V_CLOSE", True),
        ("ROUGH_OPEN", "GPIO_ROUGH_OPEN", "+24V_OPEN", False),
        ("ROUGH_CLOSE", "GPIO_ROUGH_CLOSE", "+24V_CLOSE", True),
        ("VENT_OPEN", "GPIO_VENT_OPEN", "+24V_OPEN", False),
        ("VENT_CLOSE", "GPIO_VENT_CLOSE", "+24V_CLOSE", True),
    ]
    for index, (tag, gpio, high, force) in enumerate(drivers):
        gate = f"GATE_{tag}"
        drain = f"DRAIN_{tag}"
        sheet.add(
            "Transistor_FET.kicad_sym", "IRLZ44N", "Q", "IRLZ44N", (0, 0),
            {"G": gate, "D": drain, "S": "GND"},
            "Package_TO_SOT_THT:TO-220-3_Vertical", True, 30, 24,
        )
        resistor(sheet, "100", gpio, gate)
        resistor(sheet, "100k", gate, "GND")
        sheet.add("Device.kicad_sym", "D_Zener", "D", "12V", (0, 0), {"K": gate, "A": "GND"}, FP_D_SMALL, True, 22, 16)
        diode(sheet, "1N4007", high, drain)
        anode = f"LED_{tag}"
        resistor(sheet, "2.2k", gpio, anode)
        led(sheet, anode)
        header(sheet, f"J_{tag}", [high, drain], FP_TB2)
        sheet.add(
            "Device.kicad_sym", "L", "L", tag, (0, 0),
            {"#1": high, "#2": drain}, "", False, 24, 16,
        )
        if force:
            mid = f"FORCE_MID_{tag}"
            sheet.add(
                "Jumper.kicad_sym", "Jumper_2_Open", "JP", f"FORCE_{tag}", (0, 0),
                {"A": drain, "B": mid}, FP_HDR2, True, 24, 14,
            )
            # Anode at the drain side, cathode at the shared force bus.
            # Bus-to-ground through the relay NC pulls the coil in without tying channels together.
            diode(sheet, "1N4007", "FORCE_BUS", mid)
        if (index + 1) % 2 == 0:
            sheet.newline()

    sheet.newline()
    sheet.note(
        "OFF BOARD ON PURPOSE\\n"
        "Cryo-Torr 8, CTI 8200 helium compressor, and IDP-15 are not on this copper.\\n"
        "This board asks valves to move and reads proofs. It does not start a pump motor or a compressor.\\n"
        "Before any coil is landed: meter K2 unpowered. Pin 2 must conduct to pin 4 and not to pin 3.",
        30, sheet.y - 10, 1.8,
    )


def write_project(directory: Path) -> None:
    # KiCad 10 accepts a short project file and fills the rest when the schematic is opened.
    pro = {
        "board": {"design_settings": {}},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [],
        "text_variables": {},
    }
    (directory / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2), encoding="utf-8")


def main() -> None:
    libs = Libraries()
    sheet = Sheet(libs)
    build(sheet)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sch_path = OUT_DIR / f"{PROJECT}.kicad_sch"
    sch_path.write_text(sheet.render(), encoding="utf-8")
    (OUT_DIR / "board_parts.json").write_text(json.dumps(sheet.records, indent=2), encoding="utf-8")
    write_project(OUT_DIR)
    print(f"wrote {sch_path}")
    print(f"symbols {len(libs.embedded)} parts_on_board {len(sheet.records)} refs {sheet.ref_counts}")
    print(f"bounds {sheet.bounds}")


if __name__ == "__main__":
    main()
