# Bench acceptance checks

Record actual results in `verification/physical-test-log.csv`; every physical result starts NOT TESTED. Software compilation and netlist validation are separate evidence.

## Day 1

| ID | Action | Expected observation |
|---|---|---|
| L01 | Inspect labels, unpowered harness and DIP switches | Matches L-01..L-06, A1=A0=1, no D5/D6/D7 or external equipment |
| L02 | Power from USB; measure module supply | Suitable 5V logic supply with correct polarity |
| L03 | Run 20 repeated loopback cycles | UART1 and UART2 both PASS; fail counter stays zero |
| L04 | Power down, remove UART1 T/R loop, power up | UART1 FAIL; UART2 can still PASS; no false whole-system pass |
| L05 | Restore loop with power removed | Both channels PASS again |
| L06 | Repeat five USB power-up trials | The module initializes and both channels echo on each trial |
| R01 | Inspect the separate RS485 logic harness unpowered | No loopback wires; crossed T/R; bus/12V-IN terminals unused |

L03/L06 are practical bench targets, not a proof of long-term reliability or a diagnosis of all Uno damage. If Uno power, USB or I2C remains unstable, use a known-good controller for further development.

## Day 2

Start with seven simulated-sensor ground jumpers fitted, both request buttons released and REARM released. Allow at least 100ms after changing a desk contact. All tests use LEDs only.

| ID | Action | Expected observation |
|---|---|---|
| G01 | Power up | Cryo/vent LEDs OFF, fault LED ON; MCP online at 0x21 |
| G02 | Hold a request at startup and try REARM | No arming/open indication; requests must be released first |
| G03 | Release requests and REARM, then press/release REARM | Armed; fault LED OFF |
| G04 | Hold CRYO, then release | Cryo LED follows only an accepted request |
| G05 | While CRYO is accepted, remove A3, A4, A5 or A6 ground, one at a time | Cryo LED OFF, disarmed; restoring the jumper alone does not reopen |
| G06 | With A4 absent, make a denied CRYO request; restore A4 while holding | Stays OFF; release and make a new request |
| G07 | After re-arm, hold VENT with all fake permissions true | Vent LED ON |
| G08 | Remove A2, B0 or B1 while VENT is accepted, one at a time | Vent OFF and disarmed |
| G09 | Hold both requests | Both accepted LEDs OFF, disarmed |
| G10 | Restore permissions, release requests, re-arm and make fresh request | Correct LED can activate again |
| G11 | Start with expander absent, then connect it only while power is removed | Offline/disarmed before connection; normal startup requires deliberate re-arm after connection |
| G12 | Reset the Uno while a request is held | No automatic accepted request |

For a powered communication-loss test, use a prewired switch in the SDA test lead and operate only that switch; do not unplug powered module connectors. Opening the switch must cancel accepted LEDs and reset the bench logic. Restoring it must not re-arm. This is a bench fault injection, not qualification of a real valve shutdown path.

The optional 6318 is not needed to pass G01-G12. Its load output function is untested by this package.

Record date, operator, sketch commit, wiring revision, observed result and measurements. Do not replace NOT TESTED with PASS because the expected behavior looks plausible.
