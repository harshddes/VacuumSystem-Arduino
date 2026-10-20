# Your first KiCad session

Goal: open and understand the supplied electrical drawing. You do not need to design a PCB, choose every library component, or run a whole-vacuum-system simulation.

## Open the prepared project

1. Open KiCad's **Project Manager**.
2. Choose **File > Open Existing Project** (usually Ctrl+O on Windows).
3. Browse to `development/bench-prep/kicad/day1-loopback/` and select **day1-loopback.kicad_pro**. Do not open the similarly named `.kicad_sch` as a text file in Cursor expecting a live schematic view.
4. In the project tree, double-click **day1-loopback.kicad_sch**. This opens **Schematic Editor**.
5. If prompted to configure the global symbol table, use the recommended default libraries. The project also carries `Bench.kicad_sym` and `sym-lib-table`; its existing drawing is self-contained. Do not replace its symbols with guessed internet models.
6. Use the mouse wheel to zoom. Middle-button drag pans on the default mapping. **View > Zoom > Fit Schematic** or the corresponding toolbar tool fits the drawing; key bindings may differ by installation. Hover over a symbol and press **E** to inspect properties, then Cancel.

## Read the picture

- **U1** is the physical Uno. **U2** is the physical DFR0627. On the other projects U2 can identify a different physical module; references are local to that drawing. Read the Value field before wiring.
- A box represents a purchased board. Its pins represent the accessible labelled terminals. Their drawing positions do not imitate the connector's physical orientation.
- **A4 / SDA** is the Uno's labelled A4 header. **D / SDA** is the DFR0627's D terminal. The wire schedule connects those two physical labels.
- A short wire ending in a label, such as **I2C_SDA**, is electrically joined to every other occurrence of that exact label on the same sheet. There need not be one long line across the page.
- An **X** on a pin means intentionally unconnected in this setup. It is not a connection to ground.
- **USB_5V** and **LOGIC_GND** are separate common connections. In hardware use verified breadboard distribution rails or a suitable terminal distributor; do not stuff multiple wires into one Uno socket.
- The Day 2 drawing's **R1/R2/R3** are separate resistors. **D1/D2/D3** are LEDs: A is anode, K is cathode. Each branch has one series 470 ohm resistor. The interface symbols are documentation symbols, with no simulation model or PCB footprint.

## Exactly what belongs where

The three supplied drawings already contain the placements. Do not rearrange them before the first test. Physical electrical function depends on connectivity, not whether a module is drawn on the left or right.

| Drawing | Left | Centre | Right | Bottom |
|---|---|---|---|---|
| Day 1 loopback | Uno | DFR0627 | The two loopback net labels | Test boundaries and instructions |
| Day 1 RS485 logic | Uno | DFR0627 | DFR0845, bus terminals marked unused | Field-connection stop conditions |
| Day 2 GPIO bench | Uno | MCP23017 input expander | Ten contacts and optional logic-only driver | Three resistor/LED branches |

No `kicad_pcb` file is supplied because this milestone uses existing boards and a bench harness. Creating a board outline or placing chip footprints now would not help connect tomorrow's modules.

## Learn editing on a copy, after inspecting the supplied drawing

1. Use a git checkpoint or duplicate the project folder before trying edits.
2. Hover a symbol and press **M** to move it. This can leave wires behind. **G** is drag, which attempts to keep connections. Do not move a symbol and assume the connections stayed intact.
3. **A** adds a symbol. The project-local **Bench** library contains the module interfaces already used here. You do not need this action to build the supplied test.
4. **W** starts an electrical wire. Start at the actual pin endpoint. A line that almost touches a pin is not a connection. Use the normal 50 mil grid; do not change the grid to force a connection.
5. **L** adds a local net label. Identical names join electrically; a spelling error creates another net.
6. **Q** places a no-connect flag on a genuinely unused pin. It is not a way to suppress an unexplained circuit error.
7. **Esc** exits the current tool. **Ctrl+S** saves.
8. Use **Inspect > Electrical Rules Checker** if available, then export and validate the netlist using the commands below. Do not treat a clean ERC report as proof of voltage compatibility: these interface symbols deliberately use passive pins and do not model the boards internally.
9. To make a paper copy, use **File > Plot**, select SVG or PDF, and inspect the exported drawing. KiCad does not simulate the complete instrument/valve system by opening a schematic.

## Cursor-friendly validation

From the repository root, with Python and `kicad-cli` installed:

```text
python development/bench-prep/tools/build_schematics.py
python development/bench-prep/tools/validate_package.py --kicad
```

The generator overwrites generated schematic files and the CSV. To make a lasting connection change, update `design.json` first, regenerate, and inspect the new render. If you choose to edit native KiCad files directly, preserve them as a separate revision and reconcile the connection source before regenerating.

On Windows the CLI may be under `C:\Program Files\KiCad\9.0\bin\kicad-cli.exe` (replace 9.0 with the actual installed version). Use `where.exe kicad-cli` to check PATH. In PowerShell, an executable path in quotes needs the call operator, for example `& 'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe' version`.

Official references: [Getting Started](https://docs.kicad.org/9.0/en/getting_started_in_kicad/getting_started_in_kicad.html), [Schematic Editor](https://docs.kicad.org/9.0/en/eeschema/eeschema.html), [CLI](https://docs.kicad.org/9.0/en/cli/cli.html). Select documentation matching your installed version.
