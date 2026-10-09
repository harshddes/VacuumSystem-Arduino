# MAIZE / test-stand valve controller — start here

**Revision: 2026-10-09. Board: Arduino Uno R3. Current build: Phase 1.**

Build the LED demonstration first. It needs **3 LEDs, 3 × 470 Ω resistors, 3 momentary buttons and 20 male-to-male jumper wires**, plus your Uno, breadboard, USB data cable and laptop. Have 40 jumpers available if buying a pack; the extras cover split ground rails and replacements.

1. Follow [the Phase 1 wiring and upload guide](02-phase1-breadboard.md).
2. Open [phase1_led_demo.ino](firmware/phase1_led_demo/phase1_led_demo.ino) in Arduino IDE.
3. Perform the [Phase 1 acceptance tests](06-verification.md). Record actual results in [the test log](verification/test-log.csv).

The buttons request cryo opening, vent opening and re-arm. Seven removable ground jumpers pretend to be sensors. LEDs show accepted requests. **This sketch controls LEDs only. It is not firmware for operating the chamber.**

## The complete development path

| Phase | What we build | What it proves |
|---|---|---|
| **1 — now** | Buttons, simulated sensors and LEDs | Requests are accepted or rejected correctly; restart requires re-arm |
| 2 | Actual Hornet pressure interface; laptop readout; LED outputs | Real pressure, units, validity and communication faults are handled |
| 3 | One identified cryo gate, field interfaces, position proof and cold/ready input | One real valve can move and respond to faults correctly |
| 4 | Every roughing, vent and pump isolation path; complete physical interlocks | The entire chamber has the required guardrails |
| 5 | Uno sequencing, secured assembly and standalone controls | Pumpdown and vent sequences work without a laptop |

Inventory and identifying connectors are preparation, not a sixth build phase. Automation uses the same permission checks as manual requests. No PLC is required by this prototype plan.

## Documents

- [01 — Development plan, requirements and engineering V](01-development-plan.md)
- [02 — Phase 1: exact wiring, 20-wire count and upload steps](02-phase1-breadboard.md)
- [03 — Hornet pressure interface and readout](03-pressure-interface.md)
- [04 — Valves, switches, drivers and pneumatic services](04-valves-and-pneumatics.md)
- [05 — Interlocks, control modes and final sequence design](05-controller-design.md)
- [06 — Verification and acceptance](06-verification.md)
- [07 — Equipment and required services](07-equipment-and-services.md)
- [08 — Information needed before field wiring](08-open-items.md)
- [Procurement: buy now versus later](procurement/BOM.md), [editable workbook](procurement/maize-uno-bom.xlsx)
- [Schematics and editable drawing instructions](schematics/README.md)
- [Sources and supplied laboratory guides](references/README.md)
- [Host software tests](tests/README.md), [verification record](verification/host-test-results.txt)

## Document status

This is the finalized **development baseline**, not an as-built wiring release. Known equipment models are incorporated. Unknown gate terminals, temperature signals, chamber volume, allowed pressure thresholds and failure behavior are explicitly tracked. They must be filled with measured or manufacturer-supported values before the corresponding live phase.

The existing repository [Uno references](../docs/README.md) and `pin567_check/` exercise are preserved. This folder supersedes older Nano-based proposals for this project. Start here if older messages disagree with these pin assignments or phases.

This controller requests valve motion and reads equipment readiness. Pump and cryogenic compressor operation stays with the existing equipment controls. Their location in another room does not remove the need for readiness feedback.
