# Development plan and requirements

Revision 2026-10-09 • Uno R3 • Five build phases

## System boundary

The subsystem reads operator requests, chamber pressure, valve positions and equipment-ready signals. It permits valve motion, reports pressure and faults, and eventually runs sequences. It does not replace pump motor controllers, cryopump regeneration controls or existing laboratory interlocks.

The test stand first uses Cryo-Torr 8, its identified gate and IDP-15 roughing source. Turbo-V 250 and oil pumps are optional later configurations. A handwheel valve cannot be moved or blocked electronically; full automation requires controllable isolation and vent paths.

## Requirements and evidence

| ID | Required behavior | First complete verification |
|---|---|---|
| R01 | No opening at boot, reset, brownout or fault recovery; fresh re-arm and fresh request required | Phase 1 logic; Phase 5 physical power tests |
| R02 | Simultaneous vent and pump requests reject both and latch a fault | Phase 1 cryo/vent; Phase 4 all paths |
| R03 | Cryo opening requires valid, fresh, low-enough chamber pressure; cryopump cold/ready; vent closed | Phase 2 pressure; Phase 3 physical proof |
| R04 | Vent opening requires every chamber pump path proven closed, no pump opening request and hot filaments proven off | Phase 4 |
| R05 | Roughing opening requires vent closed and roughing pump ready | Phase 4 |
| R06 | Turbo opening, if fitted, requires pressure permission, turbo ready/full speed and backing ready | Optional extension after Phase 4 |
| R07 | CLOSE and OFF override opening requests; a denied request cannot reopen later merely because a sensor recovers | Phase 1 release behavior; Phase 4 controls |
| R08 | Manual and auto requests pass through the same interlock function | Phase 5 |
| R09 | Invalid/stale pressure, missing readiness, contradictory position proof or travel timeout inhibit relevant opening and cause the defined fault response | Phases 2–5 |
| R10 | Readout shows pressure value, unit, sensor identity, age/validity, actual valve position and rejection reason | Phase 2 laptop; Phase 5 panel |
| R11 | Display/laptop failure does not remove interlocks; loss of controller/output communication produces the independently defined physical response | Phase 5 |
| R12 | Field interfaces protect Uno pins from coil supply, RS-485 bus and field sensor voltage | Electrical verification before Phase 3 |
| R13 | No unmonitored handwheel or bypass path defeats vent/pump exclusion | Plumbing survey before Phase 4 |
| R14 | Existing laboratory interlocks remain effective | System review before connecting field outputs |

“Closed” means a physical closed-position input, not the absence of an OPEN command. “Ready” means the needed operating condition, not just a power switch being ON.

## Engineering V, without the ceremony

Design downward: operator needs → requirements above → system interfaces → wiring and firmware modules. Verify upward: individual inputs/drivers → one valve → full interlocks → complete pumpdown/vent scenarios. Each test links to a requirement. Passing the software tests does not close the physical acceptance tests.

| Phase | Deliverables and work | Exit condition |
|---|---|---|
| 1 | Breadboard, provided sketch, button/jumper labels, bench test record | All Phase 1 checks pass on the Uno; reboot and request-conflict behavior demonstrated |
| 2 | Firmware-matched Hornet manual, isolated serial interface, bounded parser, read-only laptop readout, pressure test records | Readings agree with Hornet; wrong unit/status/address and disconnected/stale data never give pressure permission |
| 3 | Gate/actuator/pilot identification, terminal diagram, rated driver, input interfaces, real position and cryo-ready proof, independent output inhibition | One gate passes commanded motion, timeout, power/gas loss and communication-fault tests under controlled conditions |
| 4 | Completed chamber piping survey, actuated roughing and vent paths, filament-off proof, pump-ready inputs, manual request controls | Every path is covered; vent exclusion and close priority verified using physical positions |
| 5 | Sequence state machine, watchdog/output-enable design, secured enclosure, fused supplies, standalone controls/readout, final acceptance record | Pumpdown and vent complete unattended within the validated envelope; faults and restarts require deliberate recovery |

Do not attach real coils to the Phase 1 sketch. Phase 3 introduces different firmware and field wiring after the interfaces are known. Phase 5 can reuse the Phase 3/4 wiring if enough I/O, status signals and independent inhibition were designed in from the start.

## Module boundaries to keep hardware reusable

1. **Inputs:** convert a particular sensor's electrical signal into normalized `closed`, `ready`, `pressure_valid` and numeric pressure.
2. **Requests:** manual buttons/switches now; auto sequence requests later.
3. **Permissions:** one function checks the same rules regardless of request source.
4. **Outputs:** convert an accepted request into the particular pilot/actuator command.
5. **Readout/logging:** receives snapshots; cannot bypass permissions.

A replacement valve need not be the exact same brand. Its voltage, current, pilot scheme, normal/fault position, pressure differential rating, end switches and travel time must be requalified. Replacing a component is not just swapping a connector.

## Software and tools

- **Arduino IDE:** upload and debug Phase 1; later compile Uno firmware. Select Arduino Uno, not Nano.
- **Serial Monitor:** Phase 1 status at 9600 baud; laptop readout is sufficient during development.
- **diagrams.net:** edit the included `.drawio` diagrams and keep vacuum, pneumatic and electrical lines distinct.
- **KiCad:** create the actual circuit/connector schematic and secured assembly once field interfaces are identified. Breadboard drawings alone are not a field wiring record.
- **Git/GitHub:** revisions, issue tracking, test evidence and tagged releases.
- **C++ compiler:** run the supplied host logic tests. These are independent of IDE upload.

LabVIEW is optional for a future monitoring screen. It is not needed for this build and would not replace valve permissions on the Uno.

## Release discipline

Record component model/revision, Hornet firmware, wiring revision, firmware commit, configuration and test results together. Keep Phase 1 labeled BENCH ONLY. A live release needs completed field terminal drawings, measured failure behavior, reviewed limits and actual acceptance results. Never label a blank acceptance sheet “passed.”
