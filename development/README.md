# MAIZE / test-stand valve controller — start here

> **Current status and decisions:** read [the project status and implementation roadmap](00-project-status.md). All ordered electronics are now reported received. The completed KiCad work covers three bench setups; the full installed-system schematic, field interfaces and operational firmware remain in development.

**Current build: Phase 1, Arduino Uno R3 with the expander bench package.** User reports Uno D5/D6/D7 faulty; leave them disconnected.

1. Start with [the bench package](bench-prep/README.md) and its [module checklist](bench-prep/01-arrival-checklist.md).
2. Build the selected setup using its matching native KiCad drawing, wire IDs and diagnostic sketch.
3. Perform [the bench checks](bench-prep/04-tests.md) and record actual results in [the physical test log](bench-prep/verification/physical-test-log.csv).

The new package uses simulated sensor contacts and LED outputs. It does not release wiring to the Hornet, pilot coils or chamber. The older `02-wires.md` and direct-pin sketch are separate learning baselines; do not combine them with the expander drawing.

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

- [01 — the plan](01-plan.md)
- [02 — the wires](02-wires.md)
- [03 — the gauge](03-gauge.md)
- [04 — the valves](04-valves.md)
- [05 — the rules](05-rules.md)
- [06 — the tests](06-tests.md)
- [07 — the machines](07-machines.md)
- [08 — still unknown](08-unknowns.md)
- [shopping list](procurement/shopping-list.md), [spreadsheet](procurement/maize-uno-bom.xlsx)
- [Schematics and editable drawing instructions](schematics/README.md)
- [Sources and supplied laboratory guides](references/README.md)
- [Host software tests](tests/README.md), [verification record](verification/host-test-results.txt)

## Document status

This is the finalized **development baseline**, not an as-built wiring release. Known equipment models are incorporated. Unknown gate terminals, temperature signals, chamber volume, allowed pressure thresholds and failure behavior are explicitly tracked. They must be filled with measured or manufacturer-supported values before the corresponding live phase.

The existing repository [Uno references](../docs/README.md) and `pin567_check/` exercise are preserved. This folder supersedes older Nano-based proposals for this project. Start here if older messages disagree with these pin assignments or phases.

This controller requests valve motion and reads equipment readiness. Pump and cryogenic compressor operation stays with the existing equipment controls. Their location in another room does not remove the need for readiness feedback.

