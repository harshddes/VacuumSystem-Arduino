# Continue in Cursor without starting over

Cursor is useful here as a local coding/documentation assistant. It receives context from the repository and project rules; this is not model training. Opening a GUI manual does not automatically give it a desktop-control connection. This workflow needs file access and an optional terminal, not a new KiCad-control plugin.

## Setup

1. Open the actual repository folder in Cursor. Pull the new commit after preserving local changes. Avoid a second untracked copy of the project.
2. Ensure the project rule `.cursor/rules/ppml-bench-prep.mdc` is present and enabled. It supplies constraints and points to the current package; it does not load every manual into every chat.
3. Read `development/00-project-status.md` for current decisions and remaining work. Open `development/bench-prep/README.md`, `02-kicad-first-use.md`, `03-connections.md`, and the relevant firmware file as context. Use the file-mention picker to attach them when necessary; Cursor UI details vary by version.
4. Launch KiCad normally. You operate its GUI; Cursor can tell you the next action or edit the project sources and run `kicad-cli` when available locally. Do not assume a desktop automation capability exists.
5. Close a schematic in KiCad before letting Cursor regenerate that file, then reopen it. Avoid simultaneous GUI/file-generator edits.

## Paste this as your first message

```text
Continue this PPML project from development/00-project-status.md,
then development/bench-prep/README.md. All ordered electronics have arrived;
physical tests are not recorded yet. The full field schematic/controller
is still in development, and a custom PCB is optional.
First read .cursor/rules/ppml-bench-prep.mdc, design.json, 02-kicad-first-use.md,
03-connections.md, 04-tests.md and verification/software-validation.md.
I am a KiCad beginner. My Uno D5/D6/D7 are unavailable.
We will build day1-loopback first, then day1-rs485-logic, then the separate
day2-gpio-bench. Use the matching supplied sketch and wire IDs.
Tell me one physical connection or GUI action at a time: exact printed
terminal name, purpose, and expected check. Explain what a board does in
one sentence before we use it. Do not ask me to design a PCB or recreate
commercial module internals. Do not invent instrument terminals or limits.
Start by helping me open the existing day1-loopback project in KiCad.
```

## How to request an actual change

Describe the behavior or signal needed, then have Cursor find its source. A lasting connection edit must update `design.json`, the affected sketch/pin map, generated drawings and connection CSV, and validation expectations together. After generation, run the native KiCad netlist check and inspect the new render. A text file that looks syntactically plausible is insufficient evidence of a connected circuit.

If the GUI differs, give Cursor your KiCad version and the actual window title/menu labels. If it proposes a new component, require its manufacturer model, voltage, function and reason before adding it. Existing purchased modules should not be replaced merely to find a prettier symbol.

For application help, use the official links in `resources/source-register.json`. For component connections, use the module's own pinout and this revision's connection record. For field wiring, complete `06-field-holds.md`; a chat suggestion cannot fill a missing manufacturer fact.
