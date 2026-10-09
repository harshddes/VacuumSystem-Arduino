# Verification and acceptance

Revision 2026-10-09 • Host results are recorded separately from physical tests

## Phase 1 — perform on your breadboard

Allow at least 100 ms after each input change. A connected simulation jumper is true. Start with all seven installed, both request buttons released, and the sketch disarmed.

| Test | Action | Expected result | Requirement |
|---|---|---|---|
| B01 | Power up or press Uno RESET | Cryo/vent LEDs OFF; disarmed LED ON | R01 |
| B02 | Test holding CRYO at boot while pressing RE-ARM; separately hold RE-ARM at boot with requests released | Neither arms; release RE-ARM and requests before a fresh re-arm | R01 |
| B03 | Release both requests; press/release RE-ARM; hold CRYO | Cryo LED ON only while request held | R03/R07 |
| B04 | With cryo accepted, remove D6, D7, D8 or D5 jumper, one test at a time | Cryo OFF; disarmed; replacing jumper alone does not reopen | R03/R09 |
| B05 | Deny a new cryo request with D6 removed; reinstall D6 while holding request | Stays OFF; release/new request required | R07 |
| B06 | Re-arm; remove D4, D9 or D10; request VENT, one test at a time | Vent rejected | R04 |
| B07 | Re-arm; all fake vent permissions true; hold VENT; remove D4 | Vent OFF and disarmed | R04/R09 |
| B08 | Re-arm; hold both requests together | Both LEDs OFF; disarmed; releasing both does not re-arm | R02 |
| B09 | After fault, restore flags; release requests; press/release RE-ARM; make fresh request | Only newly permitted request accepted | R01 |
| B10 | While accepted, release the request button | Corresponding LED OFF | R07 |
| B11 | Unplug/reconnect USB with requests released | Boots disarmed; no automatic reopening | R01 |
| B12 | Remove pressure-valid D6 but keep D4/D9/D10 true; re-arm and request VENT | Vent may be accepted: pressure is not the fake vent permission | R04 |

B12 is intentional. Real venting still needs all physical closure and filament-off proofs. This test does not demonstrate atmospheric pressure measurement or a safe live vent.

## Later acceptance tests

| Test | Phase | Evidence to collect | Requirement |
|---|---:|---|---|
| P01 | 2 | Hornet INFO firmware, selected manual, connector photos and checked harness | R12 |
| P02 | 2 | Pressure/unit comparisons across available sensor ranges | R03/R10 |
| P03 | 2 | Lost gauge/bus, wrong address, malformed frame, stale sample and wrong-unit results | R09 |
| V01 | 3 | Gate/pilot/coil identification; measured current; driver temperature; input polarity | R12 |
| V02 | 3 | OPEN/CLOSED proofs, travel times and contradictory-feedback tests | R09 |
| V03 | 3 | Cryo temperature/readiness loss blocks and cancels opening | R03 |
| V04 | 3 | Power loss, MCU reset, lost I²C and loss of actuation supply: actual gate response | R01/R11 |
| S01 | 4 | Every chamber path mapped; no unmonitored manual bypass | R13 |
| S02 | 4 | Missing any pump CLOSED proof or filament-off proof inhibits vent | R04 |
| S03 | 4 | Rough readiness and vent closure required for rough opening | R05 |
| S04 | 4 | CLOSE/OFF overrides maintained OPEN; switch recovery cannot reopen | R07 |
| S05 | 4 | Original laboratory interlocks still inhibit their controlled equipment | R14 |
| A01 | 5 | Manual and auto both rejected under the same failed permissions | R08 |
| A02 | 5 | Complete pumpdown and controlled vent with logged transitions | R03–R05/R08 |
| A03 | 5 | Each sequence timeout, sensor fault and stuck-open gate prevents unsafe next step | R09 |
| A04 | 5 | Laptop removed/display failed: local interlocks remain effective | R10/R11 |
| A05 | 5 | Repeated power interruption and controller/output failure tests; fresh re-arm required | R01/R11 |
| A06 | 5 | Secured wiring, supply/fuse/thermal budget, terminal schedule, operating record | R12/R14 |

Optional turbo tests must be added if that branch is installed. An absent branch is documented as absent; it is not silently treated as a working valve with CLOSED proof.

## Test method and records

Do software tests first, then simulated electrical inputs/dummy loads, then unconnected valve motion where appropriate, then controlled vacuum integration. A substituted test valve proves only its own interface; requalify the real valve before live operation.

Use [test-log.csv](verification/test-log.csv). For each run record date, operator, firmware commit, wiring revision, configuration, initial conditions, observed result, measured timing and pass/fail. Leave results NOT TESTED until performed. Store logs and scope/meter observations in a dated subfolder.

The supplied [host tests](tests/README.md) check 519 logic scenarios and compile the sketch against host stubs. They do not measure wiring, debounce timing on an Uno, serial/RS-485 behavior, actuator closure or cryogenic readiness. Arduino IDE target compilation and physical acceptance remain required.

## Completion criteria

Phase 1 is complete when B01–B12 pass on the actual Uno. Each later phase closes its listed evidence before proceeding to the next live connection. Final autonomous acceptance requires A01–A06, completed field drawings, reviewed configuration limits and an operating procedure covering fault recovery. A successful pumpdown once is not a substitute for the fault tests.
