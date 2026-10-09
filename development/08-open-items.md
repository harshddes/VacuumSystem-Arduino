# Information needed before field implementation

Revision 2026-10-09 • None of these blocks the LED breadboard build

## Before Phase 2

| Item | Exact evidence needed | Decision it resolves |
|---|---|---|
| Hornet firmware | INFO screen photo/transcription, full model label and connector labels | Applicable manual, protocol and connector assignment |
| Hornet power | Existing supply label and which connector powers the gauge | Reuse supply or purchase correctly rated replacement |
| Low-vacuum sensor | Locate CVG101GC; label, flange, cable and working readout | Full roughdown-range pressure availability |
| Sensor cable | Cable label/ends and manufacturer compatibility confirmation | Correct Hornet–Worker Bee cable, not guessed DE-9 lead |

## Before Phase 3

| Item | Exact evidence needed | Decision it resolves |
|---|---|---|
| Cryo gate | Body and actuator nameplates; full view; C/O ports; all existing pilot markings | Single/double acting, allowed differential, pilot/driver selection |
| Position proof | Switch/sensor label, number of conductors and unpowered continuity measurements where appropriate | Dry contact versus powered sensor; OPEN/CLOSED truth table |
| Pilot coil | AC/DC voltage, wattage/current, wiring and normal state | Output rating, suppression, power budget |
| Cryo readiness | Temperature sensor/readout model, live cold temperature and available status outputs | Genuine cold-ready signal and threshold |
| CTI 8200 variant | Full nameplate and cooling connections | Air/water cooling, supply and existing service connections |
| Actuation supply | Actual regulator range, gas, fittings and measured pressure | Pilot compatibility and power/gas-loss response |
| Fault motion | Manufacturer behavior and measured response to lost power/gas | Independent inhibit/closing arrangement |

## Before Phase 4 and autonomous operation

| Item | Exact evidence needed | Decision it resolves |
|---|---|---|
| As-built vacuum plumbing | Annotated overview photos or traced drawing of every chamber-connected path | Required isolation/feedback, bypass removal or supervision |
| Chamber volume | Dimensions/measurement including connected volume | Cryo crossover gas-load calculation |
| Operating limits | Actual cryo/pump/valve manuals and existing lab procedure | Pressure, temperature, hysteresis and trip limits |
| Rough/vent valves | Current installed hardware, actuation and feedback details | Reuse versus minimum necessary purchase |
| Filament control/status | Firmware-matched Hornet control scheme and actual OFF status verification | Vent permission that proves hot filaments off |
| Pump readiness | Existing running/fault contacts or engineered measurement | Valid rough/turbo/backing inputs; power command alone insufficient |
| Panel switches | Continuity matrix for every position and current wire destinations | Request wiring and preserved operator behavior |
| Manual independence | Whether manual control must work if Uno fails | Separate physical permissive circuit, if required |
| Timing | Measured valve motion, roughdown, vent and sensor response | Timeout and fault-response configuration |

When collecting wiring information, label terminal numbers and cable ends, and measure with the circuit de-energized where continuity is involved. Do not infer signal type from wire color. Fill [field-io-register.csv](interfaces/field-io-register.csv), retain photos and update drawings before making the field connection.

Existing evidence is enough to write the development baseline. It is not enough to issue an honest final field pinout. Unset items stay visible rather than becoming fictional “known” specifications.
