# Phase 2 — actual pressure and laptop readout

Revision 2026-10-09 • Equipment reported: InstruTech Hornet **IGM402YFD**, label **20–28 VDC**

## Start by matching the instrument revision

Record the Hornet INFO-screen firmware and photograph every connector label. InstruTech assigns different archived manuals to different firmware versions. Archived manual **000861-115 applies to firmware p/n 1769 version 108**; use the applicable manual for the unit actually installed. The connector mapping below is a reference from that manual, not permission to wire an unidentified revision.

The IGM402 has RS-485 and supports external convection gauges. Check whether **Worker Bee CVG101GC** is physically available and functioning. Ion-gauge pressure alone does not cover atmospheric roughdown; an appropriate low-vacuum sensor must supply that range. When the Worker Bee is connected to the Hornet, a separate Worker Bee controller is not automatically necessary. Confirm the matching OEM sensor cable; the Hornet cable family previously identified is **HB431-1-03F / HB431-1-10F**, not a generic DE-9 serial lead. Verify ordering compatibility with InstruTech before purchasing.

## Proposed low-cost interface

Uno A4/A5 I²C → **DFRobot DFR0627 dual UART** → **DFRobot DFR0845 isolated RS-485 interface** → Hornet RS-485 port. Uno USB remains available to the laptop. Use correctly assembled headers and the interface manufacturer's wiring/library documentation. The UART-to-RS-485 link is TTL UART, not RS-232.

The DFR0845 provides an isolated bus-side interface. Its 12 V auxiliary output is not a 20–28 V Hornet supply. Keep bus-side reference and logic-side ground connections consistent with the isolation design; do not accidentally bridge the isolation through another cable or display.

| Hornet RS-485 female DE-9 socket pin | Archived manual function |
|---:|---|
| 6 | DATA A (−) |
| 9 | DATA B (+) |
| 4 | Power ground / RS-485 reference |
| 2 | +20–28 VDC supply |
| 1 / 5 / 7 | Relay NO / NC / common |

Use a **male DE-9 breakout**, such as Adafruit 3123, for that female socket. Follow molded pin numbers and the manual's connector-view orientation; a rear view is mirrored. Match electrical polarity rather than assuming every vendor uses A/B letters the same way. Determine termination, biasing and reference wiring from the selected interfaces and cable length.

If an existing approved supply already powers the Hornet through its other port, do not add a second supply through this socket. Document the single power path and the isolated bus reference separately.

The other, analog/digital male port has a different pinout. Its analog output can exceed Uno's 5 V input range. **Never connect the Hornet analog output or a 24 V terminal directly to an Uno pin.** Filament control and status require dedicated, electrically matched interfaces when introduced in Phase 4.

## Power budget

The current Hornet product page states 15 W, while the archived manual cited above specifies a **30 W minimum** supply. Until the actual unit/manual is matched, budget at least **24 V, 1.25 A** for the instrument alone. Reuse its approved supply if present. A **Mean Well GST60A24-P1J, 24 V / 2.5 A / 60 W**, is a candidate when a supply is missing, after checking harness, polarity, grounding and applicable instrument requirements. Its barrel connector does not connect directly to the Hornet or the Uno.

No 24 V enters the Phase 1 breadboard. Keep gauge and coil supply budgets separate; a proposed 24 V / 1 A coil supply would not cover the conservative Hornet requirement.

## Firmware work for Phase 2

1. Implement **read-only** communication first. Match address, baud rate and documented ASCII or binary protocol. RS-485 is an electrical interface; this instrument must not be assumed to speak Modbus.
2. Parse pressure together with sensor identity, unit, status and receive timestamp. Accept only complete, addressed and valid replies. Apply the documented checksum/CRC for the selected protocol.
3. Normalize pressure to Torr internally. Never interpret timeout, zero-filled buffers, overrange, sensor absent or filament-off status as “good vacuum.”
4. Derive `pressure_valid` from both reply validity and freshness. Use configurable enter/leave thresholds with hysteresis; thresholds and stale-data limit stay unset until reviewed.
5. Display `pressure`, `unit`, `source`, `age`, `validity` and a blocked reason on the laptop. Keep LED outputs during this phase.

Read commands and control commands are different. The archived manual describes serial control taking ownership of filament operation, which can change how digital filament inputs are honored. Do not add filament control commands during this read-only phase. Phase 4 must choose and verify a single compatible filament-control/status scheme.

## Phase 2 acceptance

Compare numeric pressure and units against the Hornet at several stable pressures within each installed sensor's range. Disconnect the bus, power down the gauge, send malformed replies, change address/units and simulate stale readings. None may leave cryo pressure permission true. Retain raw replies, firmware revision, parser tests and comparison results. The numeric crossover limit remains a separate commissioning decision.

Source manuals and module/product links: [references](references/README.md). Final terminal assignments are recorded in [the field I/O register](interfaces/field-io-register.csv).
