# Focused resource pack

Use `source-register.json` to find the official source for a particular terminal or GUI action. The connection diagrams use external module terminals, so no commercial board symbol, PCB footprint or simulation model needs to be found online before the first test.

The local walkthrough is an original, task-specific explanation based on KiCad's official documentation. Full manuals remain at their official URLs so the correct installed-version edition can be consulted. Existing Uno documentation is under `docs/` at repository root; PPML lab guides are under `development/references/lab/`.

## Important manufacturer details already incorporated

- DFR0627's D/C mean SDA/SCL. T/R are TTL UART, not RS232 or RS485. Its DIP switches must match the library constructor. Multiple I2C scan responses can be normal for this device. Its own documentation provides a two-port loopback test.
- DFR0845 has a 3.3-5V logic supply and isolated RS485 side. Its auxiliary 12V output is not a Hornet supply. The OEM advises against hot plugging. Its generic sample uses `Serial1` on a different controller; an Uno R3 does not have that second built-in hardware serial object. Use the DFR0627 when an additional UART is required.
- 5346's GPIO A0-A6/B0-B6 are digital. Current manufacturer notes advise against changing input use on A7/B7. This package assigns no input there.
- Both Adafruit MCP boards default to 0x20. This design sets only the input expander to 0x21, leaving the eight-channel driver at 0x20. The 6318's logic supply and load supply are different connections; its ground is common to those two sides.
- 6318's eight auxiliary GPIO are not protected 24V field inputs. DC coil switching depends on actual load ratings and a separately engineered failure response.
- A KiCad symbol is a schematic representation; a footprint defines physical board pads; a simulation model describes behavior. None can substitute for the other.

## What Cursor needs

It needs the current connection record, matching sketch, relevant manufacturer pinout and a small set of project rules. It does not need an entire application manual pasted into every message. The supplied rule points to these files. Use CLI validation for generated files and inspect the native drawing in KiCad.

No full hardware operating manual is silently assumed to match an unidentified instrument revision. The Hornet reference manual is linked for verification, not treated as a released field harness.
