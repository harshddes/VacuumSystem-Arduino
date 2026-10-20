# Connections that are intentionally not released

The bench drawings fix the known low-voltage module connections. They cannot turn unobserved instrument details into verified facts. The following record gives the smallest evidence set needed to finish the next interfaces.

| Interface | Evidence to collect | What becomes possible |
|---|---|---|
| Hornet communication | Full model/connector photos; INFO firmware; approved existing power path; baud/address/protocol; actual cable pin continuity; adapter A/B polarity from applicable data | Exact protected read-only RS485 harness and query implementation |
| Hornet roughdown range | Locate working CVG101GC and matching OEM cable, or identify installed alternative | Valid pressure through the roughdown range |
| SG gate / Humphrey pilot | Exact valve and pilot labels; AC/DC coil voltage/current/duty; ports; actual end-switch truth table and voltage | Rated output stage and protected position inputs |
| Cryo readiness and closing service | Existing temperature readout/status, actual ready condition; measured power/air-loss response; independent opening-inhibit design | One-valve field qualification |
| Full chamber automation | As-built paths, automatic rough/vent hardware, individual closure proof, filament-off proof, reviewed thresholds/times | Complete interlocks and sequencing |

## Hornet reference facts, not a harness release

Archived manual **000861-115** applies to firmware **1769-108**. In that manual, the female RS485 DE-9 port has pin 6 DATA A(-), pin 9 DATA B(+), pin 4 reference/power ground, and pin 2 20-28V supply. The analog DE-9 has a different pin assignment. Numbered connector views can be mirrored between front and rear. The male 3123 breakout is a connector adapter, not a voltage converter.

Do not connect pin 2 as an extra power feed when the approved instrument supply is already feeding the other port. DFR0845's 12V output is not a Hornet supply. Its isolated bus-side reference must be handled as part of the complete grounding/isolation plan, not casually joined to Uno ground. Match polarity rather than assuming different vendors use A/B letters consistently. Termination and biasing follow the actual bus/interface installation.

No Hornet commands are emitted by the supplied bench sketches. The loopback sketch sends arbitrary test bytes and must not be used with an instrument connected. Read-only pressure/status commands will be selected after the firmware/protocol match; do not send generic Modbus queries or filament-control commands by assumption.

## Final controller scope

The present direct-pin sketch remains a separate desk exercise. The supplied expander sketch restores the original bench permission/re-arm behavior using the existing tested logic class, but still has no real pressure parser, field input qualification, actuator travel control or independent physical shutdown. It must never become a valve controller merely by replacing an LED with a driver input.

An actuator may require air or electrical energy to close. Removing all power is not automatically a safe closing design. Existing PPML interlocks remain in place. Complete and verify the actual close/inhibit mechanism before attaching field outputs.
