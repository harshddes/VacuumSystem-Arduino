# Connections that are intentionally not released

The bench drawings fix the known low-voltage module connections. They cannot turn unobserved instrument details into verified facts. The following record gives the smallest evidence set needed to finish the next interfaces.

| Interface | Evidence to collect | What becomes possible |
|---|---|---|
| Hornet communication | Operator-reported menu 19200 8N1 address 1, ASCII or binary (FORMAT still needs H01). Still need connector photos, approved existing power path, actual pin continuity, and A/B polarity from a matching reply | Exact protected read-only RS485 harness and query implementation |
| Hornet roughdown range | Locate working CVG101GC and matching OEM cable, or identify installed alternative | Valid pressure through the roughdown range |
| SG gate / Humphrey pilot | Gate ID still unread, so air-off lock is untested. Plate is inside the casing. Humphrey body is 0624E136, a 062-4E1 spring-return, not the manual's 410. Closed reed on 5346 A4 cycles: coil on clears it in about 0.8 s, coil off makes it again in about 6.8 s. B4 open reed stays 1 and is ignored. Cryo-ready and Hornet permission are not in this circuit | Phase 3 wiring is in [08-gate-position.md](08-gate-position.md): 5346 A4 is the closed reed, B4 is ignored, Uno D8 to 5 V module IN with jumper on H, module NO in the 24 V Humphrey loop, diode on the Humphrey coil. 24 V negative stays off Uno ground. No extra transistor. The 6318 is not in this circuit. This is not a full Phase 3 pass |
| Cryo readiness and closing service | Existing temperature readout/status, actual ready condition; measured power/air-loss response; independent opening-inhibit design | One-valve field qualification |
| Full chamber automation | As-built paths, automatic rough/vent hardware, individual closure proof, filament-off proof, reviewed thresholds/times | Complete interlocks and sequencing |

## Hornet reference facts, not a harness release

Reported on 2026-10-29: the installed controller is an InstruTech IGM402 Hornet hot-cathode gauge, firmware **3351-100**. The manual supplied with that report is InstruTech **000861-116**, and its cover says it applies to firmware part **2444**, versions 100 and higher. **3351-100 does not appear in that manual.** The pin numbers and read commands below are from 000861-116. They are the candidate for the first read-only trial only after the gauge's own comms menu shows the same baud, address, and format. They are not a released harness for 3351-100.

On 2026-11-02 a crossed pair between the small serial board and the RS485 board left the TX light dark. Matching T to T and R to R kept that light lit for eight seconds. With the Hornet RS485 plug seated, one binary convection read returned `2A 01 03 00 7F 2D 48 44 23`. The checksum matches. The units byte is 0, which the 2444 book calls Torr. The four data bytes read as about 800.7, in line with the earlier screen photo of 8.01E+2 Torr. That is a reply, not a released pressure permission. Firmware 3351-100 is still outside the book that supplied the frame.

Operator-reported on-gauge comms menu, 2026-10-29: **19200**, 8 data bits, no parity, 1 stop bit, **ADDR 1**, **ADDR OFFSET 0**. FORMAT was set to **ASCII**, then later switched to **BINARY**. ADDR OFFSET 0 with ADDR 1 is the book's `#01` / binary address 0x01. ASCII `#01RDCG1` and the book's binary READ IG frame both got no reply. This recorded menu is still not a released 3351-100 harness. Wiring for that one trial is in [07-hornet-read-trial.md](07-hornet-read-trial.md).

In 000861-116, the female RS485 DE-9 has pin 6 DATA A(-), pin 9 DATA B(+), and pin 4 power ground. Pin 2 on that same plug is 20-28 V power. The analog DE-9 uses different pins for power and ground. Do not power both plugs. If the gauge is already powered, leave pin 2 unconnected. Factory defaults in that manual are 19200 baud, 8 data bits, no parity, 1 stop bit, address 1, format BINARY. The manual recommends ASCII when the menu allows it. A read of ion-gauge pressure while the filament is off returns `9.90E+09`, which is an off flag, not a pressure.

Archived manual **000861-115** applies to firmware **1769-108**. That older book is not the manual for the reported 3351-100 unit.

Do not connect pin 2 as an extra power feed when the approved instrument supply is already feeding the other port. DFR0845's 12V output is not a Hornet supply. Its isolated bus-side reference must be handled as part of the complete grounding/isolation plan, not casually joined to Uno ground. Match polarity rather than assuming different vendors use A/B letters consistently. Termination and biasing follow the actual bus/interface installation.

No Hornet commands are emitted by the supplied bench sketches. The loopback sketch sends arbitrary test bytes and must not be used with an instrument connected. Read-only pressure/status commands will be selected after the firmware/protocol match; do not send generic Modbus queries or filament-control commands by assumption.

## Final controller scope

The present direct-pin sketch remains a separate desk exercise. The supplied expander sketch restores the original bench permission/re-arm behavior using the existing tested logic class. Phase 3 adds expander A4/B4 reed prints and a typed D8 coil request. It still has no real pressure parser, travel timeout as a permission, or independent physical shutdown. It must never become a valve controller merely by replacing an LED with a driver input. A2 stays the simulated closed jumper. OPEN false is never treated as closed.

An actuator may require air or electrical energy to close. Removing all power is not automatically a safe closing design. Existing PPML interlocks remain in place. Complete and verify the actual close/inhibit mechanism before attaching field outputs.
