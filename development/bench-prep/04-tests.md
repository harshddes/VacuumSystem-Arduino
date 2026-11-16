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
| R01 | Inspect the separate RS485 logic harness unpowered | No loopback wires; matched T/T and R/R; bus/12V-IN terminals unused |

L03/L06 are practical bench targets, not a proof of long-term reliability or a diagnosis of all Uno damage. If Uno power, USB or I2C remains unstable, use a known-good controller for further development.

## Day 2

Start with seven simulated-sensor ground jumpers fitted, both request buttons released and REARM released. Allow at least 100ms after changing a desk contact. All tests use LEDs only.

| ID | Action | Expected observation |
|---|---|---|
| G01 | Power up | Cryo/vent LEDs OFF, fault LED ON; MCP online at 0x21 |
| G02 | Hold a request at startup and try REARM | No arming/open indication; requests must be released first |
| G03 | Release requests and REARM, then press/release REARM | Armed; fault LED OFF |
| G04 | Hold CRYO, then release | Cryo LED follows only an accepted request |
| G05 | While CRYO is accepted, remove A3, B5, A5 or A6 ground, one at a time | Cryo LED OFF, disarmed; restoring the jumper alone does not reopen |
| G06 | With B5 absent, make a denied CRYO request; restore B5 while holding | Stays OFF; release and make a new request |
| G07 | After re-arm, hold VENT with all fake permissions true | Vent LED ON |
| G08 | Remove A2, B0 or B1 while VENT is accepted, one at a time | Vent OFF and disarmed |
| G09 | Hold both requests | Both accepted LEDs OFF, disarmed |
| G10 | Restore permissions, release requests, re-arm and make fresh request | Correct LED can activate again |
| G11 | Start with expander absent, then connect it only while power is removed | Offline/disarmed before connection; normal startup requires deliberate re-arm after connection |
| G12 | Reset the Uno while a request is held | No automatic accepted request |

For a powered communication-loss test, use a prewired switch in the SDA test lead and operate only that switch; do not unplug powered module connectors. Opening the switch must cancel accepted LEDs and reset the bench logic. Restoring it must not re-arm. This is a bench fault injection, not qualification of a real valve shutdown path.

The optional 6318 is not needed to pass G01-G12. Its load output function is untested by this package.

## Hornet read-only trial

Follow only [07-hornet-read-trial.md](07-hornet-read-trial.md) while wiring. This is not a released gauge harness. Take the expander, lamps, buttons, and jumpers off first. Leave D5, D6, and D7 empty. Do not load `uart_loopback`. Do not send a filament-on or degas command. Leave 3123 screw 2 empty. Do not join DFR0845 logic `-` to the isolated RS485 ground. Save each capture under `verification/runs/2026-10-29/hornet-read/`.

| ID | Action | Expected observation |
|---|---|---|
| H01 | Menu check, data cable still off the pins | FORMAT ASCII; 19200, 8 data bits, no parity, 1 stop bit; address 1. Record firmware 3351-100. If FORMAT is still binary, stop; do not send the ASCII sentence |
| H02 | Three gauge wires with the Uno unplugged; plug the Uno in only after they are on the named screws | 3123 screw 6 to DFR0845 `A`; screw 9 to `B`; screw 4 to the isolated RS485 ground beside `A`/`B`. Screws 1, 2, 3, 5, 7, 8 and shell GND empty. 12 V screws empty. Logic `-` not joined to that isolated ground |
| H03 | One ASCII read `#01RDCG1` plus carriage return | Reply matches the gauge screen, including the unit. If no convection gauge is plugged in, `*01_1.01E+03` is the book's "no convection gauge" reply, not a chamber pressure. Optional `#01RD` while the filament is off may return `9.90E+09`; that is an off flag, not a pressure, and must not light a permission lamp |
| H04 | Unplug the three data wires | Laptop shows no reading. A number that remains is a fail |

If H01 is ASCII, the address is 1, and H03 has no reply, unplug the Uno and swap only Hornet pins 6 and 9. Try the same one read again. No other pin moves.

## Phase 3: gate circuit

Follow only [08-gate-position.md](08-gate-position.md) while wiring. USB unplugged while the wires go on. Air at or below 80 psig. Do not move the speed-controller screws. Leave D5, D6, and D7 empty. 24 V negative stays off Uno ground. Do not type `o` until P01 has been read. Save captures under `verification/runs/` with the date of the run.

| ID | Action | Expected observation |
|---|---|---|
| P01 | Upload `gpio_interlock_bench`. Do not type `o`. Look at the gate. Read `CLOSED=`, `POS=`, `D8=`, and `L=` | `D8=0`. `POS=` follows the closed reed. `L=1` while that reed is made. The melted open switch is not in this print |
| P02 | After P01 is sane, type `o` once. Watch the relay, the Humphrey coil, the gate, and the printed bits. Type `c` to release | Relay clicks. Humphrey coil gets 24 V. The closed reed turns off. `c` drops D8 and the spring returns the closed reed |
| P06 | With air and 24 V on, command open, then release, twice | `CLOSED` goes from 1 to 0 in under 1 s, then back to 1 in about 7 s. `L` follows that reed. End with `POS=CLOSED` and `D8=0` |

Record date, operator, sketch commit, wiring revision, observed result and measurements. Do not replace NOT TESTED with PASS because the expected behavior looks plausible.
