from pathlib import Path

p = Path(r"development/kicad/maize-controller/maize-controller.kicad_sch")
s = p.read_text(encoding="utf-8")
print("chars", len(s), "lines", s.count("\n"))
i = 0
depth = 0
line = 1
while i < len(s):
    c = s[i]
    if c == "\n":
        line += 1
    elif c == '"':
        i += 1
        while i < len(s):
            if s[i] == "\\":
                i += 2
                continue
            if s[i] == '"':
                break
            if s[i] == "\n":
                print("NEWLINE IN STRING at line", line)
                raise SystemExit(1)
            i += 1
    elif c == "(":
        depth += 1
    elif c == ")":
        depth -= 1
        if depth < 0:
            print("extra close at", line)
            raise SystemExit(1)
    i += 1
print("final depth", depth)
print("extends", s.count("(extends"))
print("paper line:")
for row in s.splitlines():
    if row.strip().startswith("(paper"):
        print(row)
        break
