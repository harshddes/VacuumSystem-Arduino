# Start here: hardware-arrival bench package

Revision 2026-10-23. Arduino Uno R3. User reports D5, D6 and D7 faulty.

Read [the project status and implementation roadmap](../00-project-status.md) for the complete development plan and the boundary between these bench drawings and the unfinished installed controller.

**This package provides fixed wiring for three bench setups. It does not release chamber, Hornet or solenoid-coil field wiring.**

Do not start by drawing an entire vacuum system in KiCad. Open the supplied electrical drawing for the setup you are actually building. Symbols are already placed and connected. Follow terminal labels and wire IDs; no PCB layout is needed.

1. Read [the arrival checklist](01-arrival-checklist.md).
2. Follow [the first-time KiCad walkthrough](02-kicad-first-use.md).
3. Use [the connection guide](03-connections.md), [wire-schedule.csv](wire-schedule.csv), and the matching drawing.
4. Upload only that setup's sketch, then record [the acceptance checks](04-tests.md).
5. Continue in Cursor using [the handoff](05-cursor-handoff.md). The repository includes a scoped project rule.

| Setup | Open this project in KiCad | Firmware | What it establishes |
|---|---|---|---|
| Day 1: DFR0627 only | [day1-loopback.kicad_pro](kicad/day1-loopback/day1-loopback.kicad_pro) | [uart_loopback.ino](firmware/uart_loopback/uart_loopback.ino) | Uno I2C plus exact-byte echo through both UARTs |
| Day 1: add DFR0845 logic wiring | [day1-rs485-logic.kicad_pro](kicad/day1-rs485-logic/day1-rs485-logic.kicad_pro) | No automatic instrument commands supplied | Logic harness preparation; a second endpoint is needed to prove RS485 |
| Day 2: Adafruit input expander | [day2-gpio-bench.kicad_pro](kicad/day2-gpio-bench/day2-gpio-bench.kicad_pro) | [gpio_interlock_bench.ino](firmware/gpio_interlock_bench/gpio_interlock_bench.ino) | Simulated permissions, re-arm and faults with LED outputs |

The user now reports all ordered electronics received. Inspection and physical acceptance tests are still required; receipt is not a PASS result.

## Read this before wiring

- Disconnect USB and all external supplies before changing wires. No 24 V supply is used in these three bench setups.
- D5/D6/D7 remain physically unconnected. A4/A5 and stable Uno operation must pass bench checks; an expander does not repair the Uno.
- Use USB as the only bench power source. Do not add another 5 V supply in parallel. No coil, pump, pilot or gauge power comes from an Uno pin.
- The MCP23017 test board is fixed at **0x21**. The 6318 driver stays at **0x20** and is optional, logic-powered only. Its V+ and all load outputs stay disconnected.
- The expander's A0 is a digital input on a separate board. It is not Uno A0. Ten simulated inputs are assigned in [pin-map.csv](pin-map.csv).
- All real field inputs remain pending their correct input interfaces. The switches/jumpers here are ground contacts at the desk.
- Do not use the old direct-pin LED sketch with the new expander drawing. Its present behavior and pin assignments differ from the older Phase 1 guide. It remains a separate learning exercise.

## What each purchased board does

| Board | Plain-language role | Used here |
|---|---|---|
| DFR0627 | Adds two serial ports while leaving USB logging available | Day 1 |
| DFR0845 | Translates TTL serial signals to an isolated RS485 bus | Logic harness on Day 1; field endpoint deferred |
| Adafruit 5346 | Adds digital inputs/outputs over A4/A5 | Day 2 input bank |
| Adafruit 6318 | Expander plus eight DC load switches | Optional logic-only wiring; no coil outputs released |
| Adafruit 5648 | One separate DC load switch | Park as spare; no wire in these setups |
| Adafruit 3123 | Exposes male DE-9 pins on screw terminals | Park until Hornet interface is verified |
| Perma-Proto 1609 | Soldered carrier for a later secured assembly | Not needed for bench tests; all ordered items now reported received |

## File roles and limits

- `design.json`: connection source of truth for the three bench drawings.
- `wire-schedule.csv`: every represented connection, with wire IDs. These are connections, not necessarily individual purchased jumpers: component leads and a verified distribution rail can complete a connection.
- `kicad/`: editable native projects, embedded symbols and a project-local symbol library. No vendor symbol downloads or footprint libraries are needed to view them. Module pin identifiers refer to external labelled terminals, not internal IC package numbers. These are interconnect drawings, not PCB manufacturing files or SPICE models.
- `previews/`: rendered versions of those same native schematics.
- `resources/`: official source register, focused notes, and installable library ZIPs with licenses/provenance. Existing lab and Uno manuals remain in the repository's original reference folders.
- `verification/`: software validation results. Physical tests remain NOT TESTED until actually performed.

For field work, complete [the unresolved interface record](06-field-holds.md) and the existing [field I/O register](../interfaces/field-io-register.csv). Do not turn an unset value into a guess to meet a delivery date.
