# Start here: hardware-arrival bench package

Revision 2026-10-23. Arduino Uno R3. User reports D5, D6 and D7 faulty.

Read [the project status and implementation roadmap](../00-project-status.md) for the complete development plan and the boundary between these bench drawings and the unfinished installed controller.

**This package provides fixed wiring for three bench setups.** The Hornet read-only trial is [07-hornet-read-trial.md](07-hornet-read-trial.md). The Phase 3 gate circuit is [08-gate-position.md](08-gate-position.md). Neither is a released field harness.

Do not start by drawing an entire vacuum system in KiCad. Open the supplied electrical drawing for the setup you are actually building. Symbols are already placed and connected. Follow terminal labels and wire IDs; no PCB layout is needed.

1. Read [the arrival checklist](01-arrival-checklist.md).
2. Follow [the first-time KiCad walkthrough](02-kicad-first-use.md).
3. Use [the connection guide](03-connections.md), [wire-schedule.csv](wire-schedule.csv), and the matching drawing.
4. Upload only that setup's sketch, then record [the acceptance checks](04-tests.md).
5. Continue in Cursor using [the handoff](05-cursor-handoff.md). The repository includes a scoped project rule.

The next desk experiment after the lamp tests is the Hornet read-only trial. Follow only [07-hornet-read-trial.md](07-hornet-read-trial.md) while wiring it. That page does not release a finished gauge harness. Phase 3 gate wiring follows only [08-gate-position.md](08-gate-position.md).

| Setup | Open this project in KiCad | Firmware | What it establishes |
|---|---|---|---|
| Day 1: DFR0627 only | [day1-loopback.kicad_pro](kicad/day1-loopback/day1-loopback.kicad_pro) | [uart_loopback.ino](firmware/uart_loopback/uart_loopback.ino) | Uno I2C plus exact-byte echo through both UARTs |
| Day 1: add DFR0845 logic wiring | [day1-rs485-logic.kicad_pro](kicad/day1-rs485-logic/day1-rs485-logic.kicad_pro) | No automatic instrument commands supplied | Logic harness preparation; a second endpoint is needed to prove RS485 |
| Day 2: Adafruit input expander | [day2-gpio-bench.kicad_pro](kicad/day2-gpio-bench/day2-gpio-bench.kicad_pro) | [gpio_interlock_bench.ino](firmware/gpio_interlock_bench/gpio_interlock_bench.ino) | Simulated permissions, re-arm and faults with LED outputs |
| Phase 3: one cryo gate | No KiCad project yet | Same [gpio_interlock_bench.ino](firmware/gpio_interlock_bench/gpio_interlock_bench.ino); follow [08-gate-position.md](08-gate-position.md) | SG reeds on 5346 A4/B4, D8 to 5 V module IN (jumper H), module NO in the 24 V Humphrey loop |

The user now reports all ordered electronics received. Inspection and physical acceptance tests are still required; receipt is not a PASS result.

## Read this before wiring

- Disconnect USB and all external supplies before changing wires. The three KiCad bench setups use no 24 V. Phase 3 uses a separate 24 V Humphrey loop; 24 V negative does not join Uno ground. Follow [08-gate-position.md](08-gate-position.md) for that loop.
- D5/D6/D7 remain physically unconnected. A4/A5 and stable Uno operation must pass bench checks; an expander does not repair the Uno.
- Use USB as the only logic power source. Do not add another 5 V supply in parallel. No coil, pump, pilot or gauge power comes from an Uno pin. D8 only drives the relay-module IN pin. The module turns the 5 V coil.
- The MCP23017 test board is fixed at **0x21**. The 6318 driver stays at **0x20** and is optional, logic-powered only. Its V+ and all load outputs stay disconnected.
- The expander's A0 is a digital input on a separate board. It is not Uno A0. Day 2 simulated inputs and Phase 3 reed/coil pins are assigned in [pin-map.csv](pin-map.csv).
- Day 2 switches/jumpers are ground contacts at the desk. Phase 3 SG reeds are also ground contacts, at 5 V only. Follow [08-gate-position.md](08-gate-position.md) for those two pairs.
- Do not use the old direct-pin LED sketch with the new expander drawing. Its present behavior and pin assignments differ from the older Phase 1 guide. It remains a separate learning exercise.

## What each purchased board does

| Board | Plain-language role | Used here |
|---|---|---|
| DFR0627 | Adds two serial ports while leaving USB logging available | Day 1 |
| DFR0845 | Translates TTL serial signals to an isolated RS485 bus | Logic harness on Day 1; field endpoint deferred |
| Adafruit 5346 | Adds digital inputs/outputs over A4/A5 | Day 2 input bank |
| Adafruit 6318 | Expander plus eight DC load switches | Optional logic-only wiring; no coil outputs released |
| Adafruit 5648 | One separate DC load switch | Park as spare; no wire in these setups |
| Adafruit 3123 | Exposes male DE-9 pins on screw terminals | Screw numbers 1–9 for the one read-only Hornet trial in [07-hornet-read-trial.md](07-hornet-read-trial.md); shell GND unused |
| Perma-Proto 1609 | Soldered carrier for a later secured assembly | Not needed for bench tests; all ordered items now reported received |

## File roles and limits

- `design.json`: connection source of truth for the three bench drawings. Phase 3 gate wires are not in it.
- `wire-schedule.csv`: every represented connection in those three drawings, with wire IDs. Phase 3 wires are in [phase3-wire-schedule.csv](phase3-wire-schedule.csv). These are connections, not necessarily individual purchased jumpers: component leads and a verified distribution rail can complete a connection.
- `kicad/`: editable native projects, embedded symbols and a project-local symbol library. No vendor symbol downloads or footprint libraries are needed to view them. Module pin identifiers refer to external labelled terminals, not internal IC package numbers. These are interconnect drawings, not PCB manufacturing files or SPICE models.
- `previews/`: rendered versions of those same native schematics.
- `resources/`: official source register, focused notes, and installable library ZIPs with licenses/provenance. Existing lab and Uno manuals remain in the repository's original reference folders.
- `verification/`: software validation results. Physical tests remain NOT TESTED until actually performed.

For field work, complete [the unresolved interface record](06-field-holds.md) and the existing [field I/O register](../interfaces/field-io-register.csv). Do not turn an unset value into a guess to meet a delivery date.
