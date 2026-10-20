# Software and drawing validation

Revision 2026-10-20. Repository base reviewed: `c6d7e8271d9b1f431d9ebfd1639af97e6eb5752c`.

## Executed checks

| Check | Result |
|---|---|
| Connection source, CSV, reserved pins, input ordering and address settings | PASS: 3 stages; 52 scheduled connections |
| Native KiCad parsing, XML netlist export and SVG plotting | PASS: all 3 projects using KiCad CLI 7.0.11 |
| Native exported net graph versus declared connection graph | PASS: every connected terminal group matches |
| Rendered schematic visual inspection | PASS after fixing overlapping contact/LED pin labels; final SVGs inspected |
| Existing bench permission core | PASS: 519 scenarios |
| Actual new GPIO sketch with simulated time/pins/bus | PASS: startup, deliberate re-arm, mapping, denied requests, conflict, permission loss, bus loss and reconnect |
| Arduino Uno AVR compile/link: UART loopback | PASS: 7,568 bytes flash; 603 bytes global RAM |
| Arduino Uno AVR compile/link: GPIO interlock bench | PASS: 9,334 bytes flash; 520 bytes global RAM |

Target build: Arduino CLI 1.2.2, `arduino:avr:uno`, Arduino AVR Boards 1.8.6. Libraries: DFRobot_IICSerial 1.0.2; Adafruit MCP23017 Arduino Library 2.3.2; Adafruit BusIO 1.17.4. Arduino core Wire/SPI used where needed. Global RAM reports exclude stack/runtime needs and do not establish capacity for all future phases.

The native file format is compatible with KiCad 7 and later; native parsing/export was actually tested with 7.0.11. The beginner GUI walkthrough follows official KiCad 9 documentation and notes version differences. A graphical session on the user's Windows installation was not performed.

## Repeat locally

```text
python development/bench-prep/tools/build_schematics.py
python development/bench-prep/tools/run_checks.py --kicad
arduino-cli compile --fqbn arduino:avr:uno development/bench-prep/firmware/uart_loopback
arduino-cli compile --fqbn arduino:avr:uno development/bench-prep/firmware/gpio_interlock_bench
```

Requires Python 3, g++, the relevant libraries/core, and `kicad-cli` on PATH. `run_checks.py --cli <path>` can specify another CLI location. It fails if native KiCad validation is requested and unavailable; it does not silently report an unexecuted native check as passed. On Windows, Cursor can also guide target verification through the Arduino IDE rather than installing another CLI.

The 519 cases exercise the common permission class. The extra integration test executes the actual new GPIO sketch, avoiding the older test gap where a sketch could include that class without calling it. Fake I2C inputs do not model real library timing, electrical levels, wiring faults or analogue interference.

## Not established by these checks

Physical Uno health, actual module operation, supply measurements, real RS485 traffic, Hornet pressure accuracy, coil/driver suitability, valve motion, pneumatic failure response, and chamber interlocks remain **NOT TESTED**. Record those results in the physical log only after performing them. These bench files are not a live-controller release.
