"""Build a searchable index from the Uno Rev3 design files and PDFs.

Pseudocode
  for each official variant (socket A000066, flat-chip A000073):
      parse the Eagle schematic XML
      record every placed part
      record every net as the list of part pins tied together
      for the worker chip and the USB chip, attach each leg to its net and pad
      for each header pin, attach the net and the chip legs on that same net
  compare the two variants by chip port, so a renamed net is not mistaken for a new wire
  for each PDF:
      extract an outline (page titles) when the file has one
      extract the words page by page, with the page number in the text
  write one manifest that says which source file each output came from
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

DOCS = Path(__file__).resolve().parents[1]
INDEX = DOCS / "index"
TEXT = INDEX / "text"

# Observed on this PC on 2026-10-06. Not something the PDFs contain.
OBSERVED = {
    "seen_on": "2026-10-06",
    "port": "COM3",
    "vid": "2341",
    "pid": "0043",
    "usb_revision": "0001",
    "serial": "5583833383235121B1D0",
    "windows_name": "USB Serial Device (COM3)",
    "package": "unresolved",
    "package_note": (
        "This USB identity is shared by the socket board A000066 and the "
        "flat-chip board A000073. The worker-chip package is a visual check."
    ),
}

VARIANTS = (
    {
        "sku": "A000066",
        "package": "DIP-28 socket, ATmega328P-PU",
        "schematic": DOCS / "uno-r3-dip-A000066" / "cad" / "UNO-TH_Rev3e.sch",
        "pdfs": [
            DOCS / "uno-r3-dip-A000066" / "A000066-datasheet.pdf",
            DOCS / "uno-r3-dip-A000066" / "A000066-full-pinout.pdf",
            DOCS / "uno-r3-dip-A000066" / "A000066-schematics.pdf",
        ],
    },
    {
        "sku": "A000073",
        "package": "SMD, schematic value ATmega328P-MU",
        "schematic": DOCS / "uno-r3-smd-A000073" / "cad" / "UNOSMD_V3.sch",
        "pdfs": [
            DOCS / "uno-r3-smd-A000073" / "A000073-full-pinout.pdf",
            DOCS / "uno-r3-smd-A000073" / "A000073-schematics.pdf",
        ],
    },
)

CHIP_PDFS = (
    DOCS / "chips" / "ATmega328P-complete-DS40002061B.pdf",
    DOCS / "chips" / "ATmega16U2-complete-doc7799.pdf",
)

PORT_RE = re.compile(r"P[BCD][0-7]|ADC[67]")
NET_ALIAS = {
    "AD0": "A0",
    "AD1": "A1",
    "AD2": "A2",
    "AD3": "A3",
    "AD4/SDA": "A4/SDA",
    "AD5/SCL": "A5/SCL",
}
SUPPLY_SETS = {"+5V", "GND", "+3V3", "VIN", "+3.3V"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_port(pin_name: str) -> str | None:
    found = PORT_RE.findall(pin_name)
    if found:
        return found[0]
    upper = pin_name.upper()
    if "RESET" in upper:
        return "RESET"
    for name in ("XTAL1", "XTAL2", "AREF", "AVCC", "AGND"):
        if name in upper:
            return name
    if pin_name.startswith("VCC"):
        return pin_name
    if pin_name.startswith("GND"):
        return pin_name
    return None


def compare_key(pin_name: str) -> str | None:
    """Collapse package-only name differences before comparing the two drawings."""
    upper = pin_name.upper()
    if "XTAL1" in upper:
        return "XTAL1"
    if "XTAL2" in upper:
        return "XTAL2"
    if "RESET" in upper:
        return "RESET"
    found = PORT_RE.findall(pin_name)
    if found:
        return found[0]
    for name in ("AREF", "AVCC", "AGND"):
        if name in upper:
            return name
    if upper.startswith("VCC"):
        return "VCC"
    if upper.startswith("GND"):
        return "GND"
    return None


def alias_net(name: str) -> str:
    return NET_ALIAS.get(name, name)


def parse_schematic(path: Path) -> dict:
    root = ET.parse(path).getroot()
    connects: dict[tuple[str, str, str], dict[tuple[str, str], str]] = {}
    descriptions: dict[tuple[str, str], str] = {}
    packages: dict[tuple[str, str, str], str] = {}

    for library in root.iter():
        if tag(library) != "library":
            continue
        library_name = library.get("name", "")
        for deviceset in library:
            if tag(deviceset) != "devicesets":
                continue
            for dset in deviceset:
                if tag(dset) != "deviceset":
                    continue
                set_name = dset.get("name", "")
                description = ""
                for child in dset:
                    if tag(child) == "description" and child.text:
                        description = strip_html(child.text)
                descriptions[(library_name, set_name)] = description
                for devices in dset:
                    if tag(devices) != "devices":
                        continue
                    for device in devices:
                        if tag(device) != "device":
                            continue
                        device_name = device.get("name", "")
                        packages[(library_name, set_name, device_name)] = device.get("package", "")
                        pin_pads: dict[tuple[str, str], str] = {}
                        for connects_el in device:
                            if tag(connects_el) != "connects":
                                continue
                            for connect in connects_el:
                                if tag(connect) != "connect":
                                    continue
                                pin_pads[(connect.get("gate", ""), connect.get("pin", ""))] = connect.get("pad", "")
                        connects[(library_name, set_name, device_name)] = pin_pads

    parts = []
    for part in root.iter():
        if tag(part) != "part":
            continue
        library_name = part.get("library", "")
        set_name = part.get("deviceset", "")
        device_name = part.get("device", "")
        parts.append(
            {
                "refdes": part.get("name", ""),
                "library": library_name,
                "deviceset": set_name,
                "device": device_name,
                "technology": part.get("technology", ""),
                "value": part.get("value", ""),
                "package": packages.get((library_name, set_name, device_name), ""),
                "library_description": descriptions.get((library_name, set_name), ""),
            }
        )

    by_ref = {part["refdes"]: part for part in parts}
    nets: dict[str, list[dict]] = defaultdict(list)
    for net in root.iter():
        if tag(net) != "net":
            continue
        name = net.get("name", "")
        seen = set()
        for pinref in net.iter():
            if tag(pinref) != "pinref":
                continue
            refdes = pinref.get("part", "")
            gate = pinref.get("gate", "")
            pin = pinref.get("pin", "")
            key = (refdes, gate, pin)
            if key in seen:
                continue
            seen.add(key)
            part = by_ref.get(refdes, {})
            pad = connects.get(
                (part.get("library", ""), part.get("deviceset", ""), part.get("device", "")),
                {},
            ).get((gate, pin), "")
            nets[name].append(
                {
                    "refdes": refdes,
                    "gate": gate,
                    "pin": pin,
                    "pad": pad,
                    "deviceset": part.get("deviceset", ""),
                    "value": part.get("value", ""),
                }
            )

    return {"parts": parts, "nets": dict(nets), "by_ref": by_ref, "connects": connects}


def is_supply(endpoint: dict) -> bool:
    return endpoint["deviceset"] in SUPPLY_SETS or endpoint["refdes"].startswith(("P+", "GND", "+3V"))


def is_mcu(part: dict) -> bool:
    blob = f"{part.get('deviceset', '')} {part.get('value', '')}".upper()
    return "328" in blob or "ATMEGAXX8" in blob


def is_usb_mcu(part: dict) -> bool:
    blob = f"{part.get('deviceset', '')} {part.get('value', '')}".upper()
    return "16U2" in blob


def is_header(part: dict) -> bool:
    return part.get("deviceset", "").startswith("PINHD")


def companions(endpoints: list[dict], self_ref: str) -> list[dict]:
    rows = []
    for endpoint in endpoints:
        if endpoint["refdes"] == self_ref or is_supply(endpoint):
            continue
        rows.append(endpoint)
    return rows


def endpoint_label(endpoint: dict) -> str:
    pad = f" pad {endpoint['pad']}" if endpoint["pad"] else ""
    value = f" = {endpoint['value']}" if endpoint["value"] else ""
    return f"{endpoint['refdes']}.{endpoint['pin']}{pad}{value}"


def build_variant(spec: dict) -> dict:
    parsed = parse_schematic(spec["schematic"])
    parts = parsed["parts"]
    nets = parsed["nets"]
    mcu_parts = [part for part in parts if is_mcu(part)]
    usb_parts = [part for part in parts if is_usb_mcu(part)]
    header_parts = [part for part in parts if is_header(part)]

    def pin_rows(selected: list[dict], kind: str) -> list[dict]:
        rows = []
        for part in selected:
            hits = []
            seen_pins = set()
            for net_name, endpoints in nets.items():
                for endpoint in endpoints:
                    if endpoint["refdes"] == part["refdes"]:
                        hits.append((net_name, endpoint, endpoints))
                        seen_pins.add(endpoint["pin"])
            known = parsed["connects"].get((part["library"], part["deviceset"], part["device"]), {})
            for (gate, pin), pad in known.items():
                if pin in seen_pins:
                    continue
                hits.append((None, {"refdes": part["refdes"], "gate": gate, "pin": pin, "pad": pad}, []))
            for net_name, endpoint, endpoints in hits:
                others = companions(endpoints, part["refdes"])
                mcu_here = [
                    other
                    for other in others
                    if is_mcu(parsed["by_ref"].get(other["refdes"], {}))
                    or is_usb_mcu(parsed["by_ref"].get(other["refdes"], {}))
                ]
                rows.append(
                    {
                        "variant": spec["sku"],
                        "kind": kind,
                        "refdes": part["refdes"],
                        "deviceset": part["deviceset"],
                        "value": part["value"],
                        "package": part["package"],
                        "pin": endpoint["pin"],
                        "pad": endpoint["pad"],
                        "net": net_name,
                        "net_alias": alias_net(net_name) if net_name else None,
                        "port": canonical_port(endpoint["pin"]),
                        "compare_key": compare_key(endpoint["pin"]),
                        "chip_pins": [endpoint_label(other) for other in mcu_here],
                        "also": [endpoint_label(other) for other in others if other not in mcu_here],
                    }
                )
        rows.sort(key=lambda row: (row["refdes"], natural_pin(row["pin"])))
        return rows

    return {
        "sku": spec["sku"],
        "package": spec["package"],
        "schematic": spec["schematic"].relative_to(DOCS.parent).as_posix(),
        "sha256": sha256(spec["schematic"]),
        "parts": parts,
        "nets": nets,
        "mcu_rows": pin_rows(mcu_parts, "worker"),
        "usb_rows": pin_rows(usb_parts, "usb"),
        "header_rows": pin_rows(header_parts, "header"),
    }


def natural_pin(pin: str) -> tuple:
    if pin.isdigit():
        return (0, int(pin), pin)
    return (1, 0, pin)


def port_net_map(rows: list[dict]) -> dict[str, str | None]:
    found: dict[str, str | None] = {}
    for row in rows:
        key = row.get("compare_key")
        if key and key not in found:
            found[key] = row["net"]
    return found


def other_parts(variant: dict, net_name: str | None) -> set[str] | None:
    if not net_name:
        return None
    return {
        endpoint["refdes"]
        for endpoint in variant["nets"].get(net_name, [])
        if endpoint["refdes"] not in {"ZU4", "U4"}
    }


def compare_variants(left: dict, right: dict) -> dict:
    left_ports = port_net_map(left["mcu_rows"])
    right_ports = port_net_map(right["mcu_rows"])
    ports = sorted(set(left_ports) | set(right_ports), key=lambda name: (name[0], name))
    port_rows = []
    for port in ports:
        left_net = left_ports.get(port)
        right_net = right_ports.get(port)
        present_left = port in left_ports
        present_right = port in right_ports
        same_label = present_left and present_right and left_net == right_net
        same_alias = present_left and present_right and alias_net(left_net or "") == alias_net(right_net or "")
        left_parts = other_parts(left, left_net)
        right_parts = other_parts(right, right_net)
        same_parts = (
            left_parts is not None
            and right_parts is not None
            and left_parts == right_parts
            and len(left_parts) > 0
        )
        if not present_left or not present_right:
            kind = "package_pin"
        elif same_alias or same_parts:
            kind = "match" if same_label else "label_only"
        else:
            kind = "mismatch"
        port_rows.append(
            {
                "port": port,
                "A000066_net": left_net,
                "A000073_net": right_net,
                "present_on": [sku for sku, present in (("A000066", present_left), ("A000073", present_right)) if present],
                "same_net_label": same_label,
                "same_signal": kind in {"match", "label_only"},
                "class": kind,
            }
        )

    left_parts = {part["refdes"]: part for part in left["parts"]}
    right_parts = {part["refdes"]: part for part in right["parts"]}
    shared = sorted(set(left_parts) & set(right_parts))
    value_deltas = []
    for refdes in shared:
        if left_parts[refdes]["value"] != right_parts[refdes]["value"]:
            value_deltas.append(
                {
                    "refdes": refdes,
                    "A000066": left_parts[refdes]["value"],
                    "A000073": right_parts[refdes]["value"],
                }
            )
    only_left = sorted(set(left_parts) - set(right_parts))
    only_right = sorted(set(right_parts) - set(left_parts))
    return {
        "worker_ports": port_rows,
        "shared_refdes_value_deltas": value_deltas,
        "refdes_only_on_A000066": only_left,
        "refdes_only_on_A000073": only_right,
    }


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def cell(items: list[str], limit: int = 6) -> str:
    if len(items) <= limit:
        return "<br>".join(items)
    hidden = len(items) - limit
    return "<br>".join(items[:limit]) + f"<br>+ {hidden} more in pin-index.jsonl"


def write_pin_markdown(path: Path, variant: dict) -> None:
    lines = [
        f"# {variant['sku']} pin index",
        "",
        f"Package note: {variant['package']}",
        f"Source schematic: `{variant['schematic']}`",
        f"SHA-256: `{variant['sha256']}`",
        "",
        "Each row is a header leg from the Eagle schematic. The net name is the name on that drawing. Chip legs are the worker or USB chip pins tied to the same net.",
        "",
        "| Header | Pin | Manual name | Net | Chip on that net | Also on that net |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in variant["header_rows"]:
        net = row["net"] if row["net"] else "(no wire)"
        lines.append(
            f"| {row['refdes']} | {row['pin']} | {row.get('arduino_name') or ''} | {net} | {cell(row['chip_pins'])} | {cell(row['also'])} |"
        )
    lines.extend(
        [
            "",
            "## Worker chip",
            "",
            "| Pin name | Pad | Port | Net |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in variant["mcu_rows"]:
        lines.append(
            f"| {row['pin']} | {row['pad']} | {row['port'] or ''} | {row['net'] or '(no wire)'} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def walk_outline(items, reader: PdfReader, depth: int, out: list[dict]) -> None:
    if not items:
        return
    for item in items:
        if isinstance(item, list):
            walk_outline(item, reader, depth + 1, out)
            continue
        title = str(getattr(item, "title", item))
        page = None
        try:
            page = reader.get_destination_page_number(item) + 1
        except Exception:
            page = None
        out.append({"depth": depth, "title": title, "page": page})


def rel(path: Path) -> str:
    return path.relative_to(DOCS.parent).as_posix()


def load_pdf_cache() -> dict[str, dict]:
    path = INDEX / "pdf-index.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {row["file"].replace("\\", "/"): row for row in rows}


def extract_pdf(path: Path, cache: dict[str, dict]) -> dict:
    digest = sha256(path)
    key = rel(path)
    text_path = TEXT / f"{path.stem}.txt"
    cached = cache.get(key)
    if cached and cached.get("sha256") == digest and text_path.exists() and "error" not in cached:
        normalized = dict(cached)
        for field in ("file", "text_file", "outline_file"):
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].replace("\\", "/")
        return normalized

    reader = PdfReader(str(path))
    outline: list[dict] = []
    try:
        walk_outline(reader.outline, reader, 0, outline)
    except Exception as exc:
        outline = [{"depth": 0, "title": f"outline unreadable: {exc}", "page": None}]

    completed = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace")
        text_path = TEXT / f"{path.stem}.txt"
        text_path.write_text(f"pdftotext failed\n{message}\n", encoding="utf-8")
        return {
            "file": key,
            "sha256": digest,
            "pages": len(reader.pages),
            "outline_entries": len(outline),
            "text_file": rel(text_path),
            "text_chars": 0,
            "error": message.strip(),
        }

    raw = completed.stdout.decode("utf-8", errors="replace")
    pages = raw.split("\f")
    if pages and pages[-1] == "":
        pages = pages[:-1]
    chunks = []
    for number, page in enumerate(pages, start=1):
        body = page.strip("\n")
        chunks.append(f"\n\n===== {path.name} PAGE {number} =====\n\n{body}")
    text = "".join(chunks).lstrip("\n") + "\n"
    text_path.write_text(text, encoding="utf-8")
    outline_path = INDEX / "outline" / f"{path.stem}.json"
    write_json(outline_path, outline)
    return {
        "file": key,
        "sha256": digest,
        "pages": len(reader.pages),
        "extracted_pages": len(pages),
        "outline_entries": len(outline),
        "outline_file": rel(outline_path),
        "text_file": rel(text_path),
        "text_chars": len(text),
    }


ACCEPTED_NETS = {
    "NC": {None},
    "IOREF": {"+5V"},
    "Reset": {"RESET"},
    "+3V3": {"+3V3"},
    "+5V": {"+5V"},
    "GND": {"GND"},
    "VIN": {"VIN"},
    "AREF": {"AREF"},
    "SS": {"SS"},
    "MOSI": {"MOSI"},
    "MISO": {"MISO"},
    "SCK": {"SCK"},
    "A4/SDA": {"A4/SDA", "AD4/SDA"},
    "A4/SD4": {"A4/SDA", "AD4/SDA"},
    "A5/SCL": {"A5/SCL", "AD5/SCL"},
    "A5/SD5": {"A5/SCL", "AD5/SCL"},
}


def accepted_nets(function: str) -> set[str | None] | None:
    if function in ACCEPTED_NETS:
        return ACCEPTED_NETS[function]
    digital = re.fullmatch(r"D(\d+)", function)
    if digital:
        return {f"IO{digital.group(1)}"}
    analog = re.fullmatch(r"A(\d+)", function)
    if analog:
        return {f"A{analog.group(1)}", f"AD{analog.group(1)}"}
    return None


def parse_connector_tables(text: str) -> list[dict]:
    rows = []
    section = None
    page = None
    for line in text.splitlines():
        if line.startswith("=====") and "PAGE" in line:
            match = re.search(r"PAGE (\d+)", line)
            page = int(match.group(1)) if match else page
        if re.fullmatch(r"\s*5\.1 JANALOG\s*", line):
            section = "JANALOG"
            continue
        if re.fullmatch(r"\s*5\.2 JDIGITAL\s*", line):
            section = "JDIGITAL"
            continue
        if section and re.match(r"\s*5\.3\b", line):
            break
        if not section:
            continue
        parts = [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        rows.append(
            {
                "connector": section,
                "pin": int(parts[0]),
                "function": parts[1],
                "type": parts[2] if len(parts) > 2 else "",
                "description": parts[3] if len(parts) > 3 else "",
                "source": f"A000066-datasheet.pdf PAGE {page}",
            }
        )
    return rows


def eagle_header_for(sku: str, connector: str, pin: int) -> tuple[str, int]:
    if sku == "A000073":
        return ("J1" if connector == "JANALOG" else "J2", pin)
    if connector == "JANALOG":
        return ("POWER", pin) if pin <= 8 else ("AD", pin - 8)
    return ("IOL", pin) if pin <= 8 else ("IOH", pin - 8)


def arduino_name(connector: str, pin: int, function: str) -> str:
    if connector == "JDIGITAL" and 1 <= pin <= 14:
        return f"D{pin - 1}"
    if connector == "JANALOG" and 9 <= pin <= 14:
        return f"A{pin - 9}"
    return function


def stamp_arduino_names(variants: list[dict], rows: list[dict]) -> None:
    names = {
        (row["sku"], row["eagle_refdes"], str(row["eagle_pin"])): row["arduino_name"]
        for row in rows
    }
    for variant in variants:
        for header in variant["header_rows"]:
            header["arduino_name"] = names.get((variant["sku"], header["refdes"], str(header["pin"])))


def find_header_row(variant: dict, refdes: str, pin: int) -> dict | None:
    for row in variant["header_rows"]:
        if row["refdes"] == refdes and str(row["pin"]) == str(pin):
            return row
    return None


def build_crosswalk(variants: list[dict]) -> dict:
    text_path = TEXT / "A000066-datasheet.txt"
    manual_rows = parse_connector_tables(text_path.read_text(encoding="utf-8"))
    by_sku = {variant["sku"]: variant for variant in variants}
    checked = []
    for manual in manual_rows:
        allowed = accepted_nets(manual["function"])
        for sku, variant in by_sku.items():
            refdes, pin = eagle_header_for(sku, manual["connector"], manual["pin"])
            eagle = find_header_row(variant, refdes, pin)
            net = None if eagle is None else eagle["net"]
            agrees = allowed is not None and net in allowed
            checked.append(
                {
                    **manual,
                    "sku": sku,
                    "eagle_refdes": refdes,
                    "eagle_pin": pin,
                    "eagle_net": net,
                    "eagle_chip": [] if eagle is None else eagle["chip_pins"],
                    "arduino_name": arduino_name(manual["connector"], manual["pin"], manual["function"]),
                    "agrees": agrees,
                }
            )
    return {
        "source": "docs/index/text/A000066-datasheet.txt",
        "rows": checked,
        "disagreements": [row for row in checked if not row["agrees"]],
    }


def write_board(variants: list[dict], comparison: dict, pdf_index: list[dict], crosswalk: dict) -> None:
    by_class: dict[str, list[dict]] = defaultdict(list)
    for row in comparison["worker_ports"]:
        by_class[row["class"]].append(row)
    lines = [
        "# Board in front of the laptop",
        "",
        "Read this file first.",
        "",
        "- A wire fact comes from the Eagle schematic, via `docs/index/pin-index.jsonl`.",
        "- A sentence in a manual comes from `docs/index/text/`, and the page banner is the page to open in the PDF.",
        "- The header names in the product manual are joined to those wires in `docs/index/connector-crosswalk.json`.",
        "- The USB identity below was read from this PC. It is not a line in a PDF.",
        "",
        "## Measured on this PC",
        "",
        f"- Date: {OBSERVED['seen_on']}",
        f"- Windows name: {OBSERVED['windows_name']}",
        f"- USB vendor/product/revision: {OBSERVED['vid']} / {OBSERVED['pid']} / {OBSERVED['usb_revision']}",
        f"- Serial: {OBSERVED['serial']}",
        f"- Worker-chip package: {OBSERVED['package']}. {OBSERVED['package_note']}",
        "",
        "## Fitted chips, from the schematics",
        "",
    ]
    for variant in variants:
        for part in variant["parts"]:
            if not (is_mcu(part) or is_usb_mcu(part)):
                continue
            lines.append(
                f"- {variant['sku']} `{part['refdes']}` value `{part['value'] or '(blank)'}` "
                f"device `{part['device']}` package `{part['package']}`"
            )
            if part["library_description"]:
                lines.append(f"  - Library blurb, not a specification: {part['library_description']}")
    lines.extend(
        [
            "",
            "Use the Microchip page text for memory size and electrical limits. The library blurb above still describes an older, smaller chip.",
            "",
            "## Drawings compared",
            "",
            f"- Worker ports with the same wire: {len(by_class['match'])}.",
            f"- Same wire, different net label: {len(by_class['label_only'])}.",
            f"- Pin exists on only one package: {len(by_class['package_pin'])} "
            + "("
            + ", ".join(row["port"] for row in by_class["package_pin"])
            + ").",
            f"- Real wiring disagreements: {len(by_class['mismatch'])}.",
            f"- Manual header rows that disagree with the drawing: {len(crosswalk['disagreements'])}.",
            "",
            "Open `docs/index/A000066-pins.md` for the socket board and `docs/index/A000073-pins.md` for the flat-chip board.",
            "",
            "## Page text",
            "",
        ]
    )
    for item in pdf_index:
        lines.append(
            f"- `{item['text_file']}` — {item.get('extracted_pages', item.get('pages', 0))} pages, "
            f"{item.get('text_chars', 0)} characters, source `{item['file']}`"
        )
    lines.extend(
        [
            "",
            "Search with `python docs/tools/lookup.py pin D13` or `python docs/tools/lookup.py text 500mA`.",
            "Rebuild with `python docs/tools/build_index.py` after a source file changes.",
            "",
        ]
    )
    (INDEX / "BOARD.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    INDEX.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)
    variants = [build_variant(spec) for spec in VARIANTS]
    comparison = compare_variants(variants[0], variants[1])

    cache = load_pdf_cache()
    pdf_index = []
    for spec in VARIANTS:
        for pdf in spec["pdfs"]:
            pdf_index.append(extract_pdf(pdf, cache))
    for pdf in CHIP_PDFS:
        pdf_index.append(extract_pdf(pdf, cache))
    write_json(INDEX / "pdf-index.json", pdf_index)
    crosswalk = build_crosswalk(variants)
    stamp_arduino_names(variants, crosswalk["rows"])

    jsonl_path = INDEX / "pin-index.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for variant in variants:
            slim_parts = [{key: value for key, value in part.items() if key != "library_description"} for part in variant["parts"]]
            write_json(INDEX / variant["sku"] / "parts.json", slim_parts)
            write_json(INDEX / variant["sku"] / "nets.json", variant["nets"])
            write_pin_markdown(INDEX / f"{variant['sku']}-pins.md", variant)
            for row in variant["header_rows"] + variant["mcu_rows"] + variant["usb_rows"]:
                handle.write(json.dumps(row) + "\n")

    write_json(INDEX / "variant-compare.json", comparison)
    write_json(
        INDEX / "connector-crosswalk.json",
        {"source": crosswalk["source"], "disagreement_count": len(crosswalk["disagreements"]), "rows": crosswalk["rows"]},
    )
    write_board(variants, comparison, pdf_index, crosswalk)

    for variant in variants:
        print(
            f"{variant['sku']}: parts={len(variant['parts'])} nets={len(variant['nets'])} "
            f"header_pins={len(variant['header_rows'])} worker_pins={len(variant['mcu_rows'])}"
        )
    for kind in ("match", "label_only", "package_pin", "mismatch"):
        rows = [row for row in comparison["worker_ports"] if row["class"] == kind]
        print(f"{kind}: {len(rows)} " + ", ".join(row["port"] for row in rows if kind != "match"))
    print(f"crosswalk rows={len(crosswalk['rows'])} disagreements={len(crosswalk['disagreements'])}")
    for row in crosswalk["disagreements"]:
        print(
            f"  DISAGREE {row['sku']} {row['connector']} pin {row['pin']} {row['function']} "
            f"eagle {row['eagle_refdes']}.{row['eagle_pin']} net={row['eagle_net']}"
        )


if __name__ == "__main__":
    main()
