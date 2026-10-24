# Project status and implementation roadmap

Revision 2026-10-23. Latest hardware report: the user says all ordered electronics have arrived. This confirms reported receipt, not inspection, electrical compatibility or operation.

**The current plan is documented. The full vacuum controller is still in development. The three supplied KiCad projects cover bench tests only.**

Use this page as the handoff for the current decisions, completed work and remaining work. Exact bench connections remain governed by `bench-prep/design.json`, its generated wire schedule and the matching schematic/firmware. This page does not release additional field wiring.

## What we are building

An enclosed, modular valve controller using the purchased Uno and interface boards. It reads operator requests, pressure, valve positions and equipment readiness; checks permissions; requests valve motion; reports faults; and later runs pumpdown/vent sequences.

The initial equipment configuration is the reported Cryo-Torr 8, CTI 8200 and IDP-15. Turbo and other pump configurations are later extensions. Existing pump/compressor controls and laboratory machine interlocks remain effective. A laptop or LabVIEW screen may display information and make requests; the controller must enforce permissions locally.

**A custom PCB is optional and is not the next required deliverable.** First qualify the modules and equipment interfaces. Then use secured module mounting, labelled terminal blocks, suitable connectors, protected supplies and an enclosure. A Perma-Proto can carry appropriate low-voltage interconnections after qualification; not every module or field component needs to be soldered onto one board. Field power distribution and actuator wiring require their own rated, secured arrangement.

If a custom PCB later has a clear purpose, create it from the qualified schematic and verify footprints, connector orientation, ratings, layout and assembled hardware separately. No custom controller PCB or manufacturing package has been completed.

## What exists, and what is still missing

| Item | Repository status | Physical status / limit |
|---|---|---|
| Five-phase requirements and development plan | [Documented](01-plan.md) | Exit conditions still need actual evidence |
| Three native KiCad bench projects and rendered previews | [Completed for their stated scope](bench-prep/README.md) | No complete installed-system schematic yet |
| Bench pin map and 52 scheduled connections | [Documented](bench-prep/03-connections.md) | Follow only the selected setup; not a full field harness |
| UART loopback and expander/LED sketches | [Compiled and software checked](bench-prep/verification/software-validation.md) | Actual purchased hardware has no recorded acceptance results |
| Beginner KiCad instructions, libraries and manufacturer sources | [Available](bench-prep/02-kicad-first-use.md) | Local installation and actual hardware still need checks |
| Cursor context and handoff | [Available](bench-prep/05-cursor-handoff.md) | Context files are not model training or automatic GUI control |
| Hornet read-only acquisition and qualified pressure data | Requirements/reference information documented | Applicable unit/firmware/power/harness and implementation still pending |
| Protected field inputs, rated coil outputs and independent inhibition/closing | [Open interfaces documented](bench-prep/06-field-holds.md) | Not designed and qualified as a complete system |
| Complete valve sequencing, panel installation and final acceptance | Planned | Still to implement and verify |

The software record includes native KiCad export/net checks, 519 permission-core scenarios, a simulated execution test of the actual new GPIO sketch and both Uno AVR builds. These do not establish real RS485 communication, pressure validity, valve motion or response to power/air loss. The [physical test log](bench-prep/verification/physical-test-log.csv) remains **NOT TESTED**; do not change it merely because parts arrived.

## Development sequence

These stages retain the original five-phase plan. The three bench drawings are separate test setups inside Phase 1, not three finished vacuum-controller phases. Their historical “Day 1/Day 2” names identify setups; all parts are now reported received.

| Phase | Next work | Evidence needed to finish |
|---|---|---|
| 1: module and logic bench | First DFR0627 loopback; then separate DFR0845 logic harness preparation; then separate MCP23017 contacts/LED bench | Supply/wiring checks, UART echo and deliberate failure test, GPIO/re-arm/fault tests, recorded results. Logic harness preparation alone does not prove RS485 |
| 2: real pressure, LEDs only | Match Hornet firmware/manual and power path; qualify RS485 with a real endpoint; implement bounded read-only pressure/status parsing and freshness | Agreement with instrument readout; invalid/stale/disconnected data cannot grant pressure permission; working roughdown-range sensor |
| 3: one real valve | Finish interface schematic, rated driver and input conditioning; qualify position/ready feedback and independent opening inhibition/closing service | Controlled motion, travel timeout and defined power/air/communication-loss response demonstrated |
| 4: every chamber path | Survey all connected paths; cover roughing, vent and isolation; prove closure, pump readiness and filament-off conditions | Physical interlock tests cover every path and relevant failure |
| 5: complete controller | Implement shared manual/automatic permission checks and sequences; secure supplies, panel and enclosure; finish documentation | Reviewed limits, restart/fault recovery, pumpdown/vent acceptance and matching as-built records |

No step consists of replacing a bench LED with a solenoid and treating the diagnostic sketch as operational firmware.

## Full KiCad schematic: the next design deliverable

The eventual full interconnect schematic should cover these five areas. It will represent purchased modules by their external interfaces; it need not redraw each commercial board's internal circuit.

1. **Power:** selected supplies, protection, distribution, logic/field references, isolation boundaries and relevant disconnects.
2. **Controller and communications:** a qualified Uno, I2C addresses, DFR0627, DFR0845 and the verified Hornet connector/cable.
3. **Inputs:** requests, position proof, equipment readiness and other field signals, with conditioning appropriate to their actual electrical type.
4. **Outputs and fault response:** verified pilot coils, rated drivers/suppression, independent opening inhibition and the qualified closing arrangement.
5. **Installation:** terminal numbers, cable IDs, connector views, panel controls and enclosure connections.

This schematic is **not completed**. Its first complete revision will be a design for a prototype that must be tested. The final as-built revision must incorporate the measured results and actual installation. KiCad connectivity/ERC checks and any selected circuit simulations support design review; they cannot substitute for physical qualification. A full-system simulation with exact models of every purchased board is not required to begin the stated bench tests.

## Evidence required before issuing field connections

Use [the field holds](bench-prep/06-field-holds.md), [unknowns](08-unknowns.md), [field I/O register](interfaces/field-io-register.csv) and [configuration record](interfaces/configuration-record.json). At minimum, resolve:

- Hornet full model, INFO firmware, protocol/settings, existing supply path, connector orientation and cable continuity; identify the working roughdown-range sensor and its matching cable.
- Gate/actuator/pilot labels; coil AC/DC voltage, current or wattage, duty, number of coils and actual pneumatic scheme.
- Position sensor electrical type, terminal assignments and measured OPEN/CLOSED truth table.
- Cryo-ready readout/output type and the applicable ready condition; other required pump/status and filament-off proof.
- Supply ratings, connected chamber paths/volume, supported operating limits and measured travel/response times.
- Actual valve behavior on loss of air, power or controller communication, and the independently effective inhibit/closing design. Removing power does not necessarily close a double-acting actuator.

Uno D5/D6/D7 remain disconnected. The expander replaces digital I/O but does not repair the Uno or prove the rest of it healthy. Check stable power, upload, I2C and the pins used by the bench package. If electrical damage is confirmed, the recommendation for the permanent controller is a known-good Uno rather than relying on the damaged board.

Evidence may be a matched manufacturer document, labelled photographs or measurements as appropriate. A photograph alone does not establish current, contact behavior or failure motion. Keep unresolved values unset; receiving electronics does not resolve them.

## What “finished” will mean

The installed controller needs a matching as-built schematic/wire schedule, firmware revision, supported configuration/limits, secured assembly and completed physical acceptance record. [The existing plan](01-plan.md) defines the requirements and release evidence. The [supplied laboratory guides and manufacturer references](references/README.md) are already indexed in the repository.

The immediate action is to follow [the module bench checklist](bench-prep/01-arrival-checklist.md), starting with the six-connection DFR0627 loopback. Equipment identification can proceed alongside those tests. Remaining field design and commissioning work must stay visible in the handoff; it must not depend on remembering this conversation.
