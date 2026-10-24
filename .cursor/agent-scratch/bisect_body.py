import subprocess
from pathlib import Path

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
SRC = Path(r"development/kicad/maize-controller/maize-controller.kicad_sch")
TMP = Path(r"development/kicad/maize-controller/_bisect.kicad_sch")
text = SRC.read_text(encoding="utf-8")


def children(s: str) -> list[str]:
    i = 0
    depth = 0
    start = None
    out = []
    while i < len(s):
        ch = s[i]
        if ch == '"':
            i += 1
            while i < len(s):
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == '"':
                    break
                i += 1
        elif ch == "(":
            if depth == 1:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 1 and start is not None:
                out.append(s[start:i + 1])
                start = None
            if depth == 0:
                break
        i += 1
    return out


kids = children(text)
lib = next(k for k in kids if "lib_symbols" in k[:40])
body = [k for k in kids if k not in (lib,) and not k.startswith("(version") and not k.startswith("(generator") and not k.startswith("(uuid") and not k.startswith("(paper") and not k.startswith("(title_block") and not k.startswith("(sheet_instances")]
# The filters above are wrong because kids don't include the leading tab consistently.
# Re-filter by first token.
def head(k: str) -> str:
    return k.lstrip()[1:].split()[0].strip('"')

body = [k for k in kids if head(k) not in {"version", "generator", "generator_version", "uuid", "paper", "title_block", "lib_symbols", "sheet_instances"}]
print("body items", len(body), "first", head(body[0]), "last", head(body[-1]))


def probe(items: list[str]) -> bool:
    doc = (
        "(kicad_sch\n\t(version 20250114)\n\t(generator \"eeschema\")\n"
        "\t(generator_version \"9.0\")\n\t(uuid \"11111111-1111-1111-1111-111111111111\")\n"
        "\t(paper \"A3\")\n\t" + lib + "\n" + "\n".join(items) +
        "\n\t(sheet_instances\n\t\t(path \"/\" (page \"1\"))\n\t)\n)\n"
    )
    TMP.write_text(doc, encoding="utf-8")
    proc = subprocess.run([CLI, "sch", "erc", "--severity-error", "-o", str(TMP.with_suffix(".rpt")), str(TMP)], capture_output=True, text=True)
    blob = proc.stdout + proc.stderr
    return "Failed to load" not in blob


print("empty body", probe([]))
print("full body", probe(body))
lo, hi = 1, len(body)
while lo < hi:
    mid = (lo + hi) // 2
    ok = probe(body[:mid])
    print(f"prefix {mid} {'ok' if ok else 'FAIL'}", flush=True)
    if ok:
        lo = mid + 1
    else:
        hi = mid
print("first failing index", lo - 1)
item = body[lo - 1]
print(item[:2000])
