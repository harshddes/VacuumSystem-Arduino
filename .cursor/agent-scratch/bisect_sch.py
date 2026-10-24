"""Find the first embedded symbol KiCad refuses to load."""
import subprocess
from pathlib import Path

CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
SRC = Path(r"development/kicad/maize-controller/maize-controller.kicad_sch")
TMP = Path(r"development/kicad/maize-controller/_bisect.kicad_sch")

text = SRC.read_text(encoding="utf-8")
# Split top-level children of kicad_sch
assert text.startswith("(kicad_sch")


def children(s: str) -> list[str]:
    # s includes the outer (kicad_sch ... )
    i = s.find("(")
    depth = 0
    start = None
    out = []
    for idx, ch in enumerate(s):
        if ch == '"':
            idx2 = idx + 1
            # skip strings; handled below by index walk instead
        break
    i = 0
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
print("top children", len(kids), [k.split("\n", 1)[0][:80] for k in kids])
lib = next(k for k in kids if k.startswith("(lib_symbols") or k.startswith("\t(lib_symbols"))
symbols = children("(wrap\n" + lib[lib.find("("):] )
# children() on a wrapped form: first child is lib_symbols itself if wrap adds a paren
# Re-parse lib_symbols body.
body_start = lib.find("\n")
inner = "(lib_symbols" + lib[lib.find("(lib_symbols") + len("(lib_symbols"):]
# simpler: symbols are the children inside lib_symbols
sym_kids = children(lib if lib.startswith("(") else "(" + lib)
print("lib children", len(sym_kids))
print("first", sym_kids[0][:80].replace("\n", " "))
print("last", sym_kids[-1][:80].replace("\n", " "))


def probe(symbol_blocks: list[str]) -> bool:
    libs = "\n".join(symbol_blocks)
    doc = f"""(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "9.0")
\t(uuid "11111111-1111-1111-1111-111111111111")
\t(paper "A4")
\t(lib_symbols
{libs}
\t)
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
)
"""
    TMP.write_text(doc, encoding="utf-8")
    proc = subprocess.run(
        [str(CLI), "sch", "erc", "--severity-error", "-o", str(TMP.with_suffix(".rpt")), str(TMP)],
        capture_output=True, text=True,
    )
    ok = proc.returncode == 0 or "Failed to load" not in (proc.stdout + proc.stderr)
    return "Failed to load" not in (proc.stdout + proc.stderr)


# empty
print("empty", probe([]))
print("all symbols", probe(sym_kids))
if not probe(sym_kids):
    lo, hi = 1, len(sym_kids)
    while lo < hi:
        mid = (lo + hi) // 2
        print("probe prefix", mid, flush=True)
        if probe(sym_kids[:mid]):
            lo = mid + 1
        else:
            hi = mid
    bad = lo - 1
    print("first bad index", bad)
    if bad is not None:
        head = sym_kids[bad].split("\n", 1)[0]
        print("BAD", head[:200])
        print(sym_kids[bad][:1500])
