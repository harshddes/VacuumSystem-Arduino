"""Search the Uno Rev3 index built by build_index.py.

Examples
  python docs/tools/lookup.py pin D13
  python docs/tools/lookup.py pin SCK
  python docs/tools/lookup.py part ZU4
  python docs/tools/lookup.py text polyfuse
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

INDEX = Path(__file__).resolve().parents[1] / "index"
TEXT = INDEX / "text"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def blob(row: dict) -> str:
    return json.dumps(row, ensure_ascii=False).lower()


def show_pin(query: str) -> None:
    needle = query.lower()
    rows = load_jsonl(INDEX / "pin-index.jsonl")
    hits = [row for row in rows if needle in blob(row)]
    crosswalk_path = INDEX / "connector-crosswalk.json"
    if crosswalk_path.exists():
        crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
        named = [
            row
            for row in crosswalk["rows"]
            if needle in blob(row)
        ]
    else:
        named = []
    print(f"pin-index hits: {len(hits)}")
    if not hits:
        print("no pin-index hits")
    for row in hits[:40]:
        print(
            f"{row['variant']} {row['kind']} {row['refdes']}.{row['pin']} "
            f"net={row['net']} port={row.get('port')} chip={row.get('chip_pins')}"
        )
    if len(hits) > 40:
        print(f"... {len(hits) - 40} more")
    print(f"manual-crosswalk hits: {len(named)}")
    for row in named[:20]:
        flag = "OK" if row["agrees"] else "DISAGREE"
        print(
            f"{flag} {row['sku']} {row['connector']} pin {row['pin']} {row['function']} "
            f"-> {row['eagle_refdes']}.{row['eagle_pin']} net={row['eagle_net']} ({row['source']})"
        )


def show_part(query: str) -> None:
    needle = query.lower()
    for folder in ("A000066", "A000073"):
        parts = json.loads((INDEX / folder / "parts.json").read_text(encoding="utf-8"))
        hits = [part for part in parts if needle in json.dumps(part).lower()]
        print(f"{folder} part hits: {len(hits)}")
        for part in hits:
            print(
                f"  {part['refdes']} {part['deviceset']} value={part['value'] or '(blank)'} "
                f"package={part['package']}"
            )


def show_text(query: str) -> None:
    needle = query.lower()
    shown = 0
    for path in sorted(TEXT.glob("*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines()
        page = "?"
        for index, line in enumerate(lines):
            if line.startswith("=====") and "PAGE" in line:
                page = line.strip("= ").strip()
            if needle in line.lower():
                print(f"{path.name} :: {page}")
                print(f"  {line.strip()}")
                shown += 1
                if shown >= 12:
                    print("stopped after 12 text hits")
                    return
    if shown == 0:
        print("no text hits")


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in {"pin", "part", "text"}:
        print("usage: lookup.py pin|part|text QUERY")
        sys.exit(2)
    kind, query = sys.argv[1], " ".join(sys.argv[2:])
    if kind == "pin":
        show_pin(query)
    elif kind == "part":
        show_part(query)
    else:
        show_text(query)


if __name__ == "__main__":
    main()
