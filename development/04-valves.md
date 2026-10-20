# Phases 3–4 — valves, panel switches and field wiring

Revision 2026-10-09 • Exact installed large-gate model and terminal assignments unresolved

## Identify what moves the valve

Earlier photographs suggest a large gate with a cylindrical pneumatic actuator, C/O fittings and loose position-related wires. The small handwheel angle valves are manual. These observations do not establish the large gate's model, coil rating or feedback wiring. See [still unknown](08-unknowns.md) before buying a pilot or attaching a driver.

| Actuation type | What the controller needs | Critical distinction |
|---|---|---|
| Manual handwheel | Physical operating procedure or engineered actuator replacement | Software cannot prevent a person turning it |
| Spring-return pneumatic | One pilot circuit, appropriate air routing and physical end feedback | Verify actual return position on loss of power AND gas |
| Double-acting pneumatic | Correct directional pilot and air supply for both directions | Removing electrical power may not close it |
| Motor/electric actuator | Its specified controller, power and feedback | Do not treat its motor as a DC solenoid |

An electro-pneumatic pilot is an electrically switched **gas-routing valve**. It is separate from the vacuum-wetted gate. A double-acting C/O cylinder generally needs a suitable directional pilot; one guessed on/off solenoid is not an adequate design.

## Physical connection order

Actuation supply → shutoff → regulator/filter suitable for the actuator → supply-pressure proof → pilot P port → actuator ports specified by the manufacturer. Route pilot exhaust according to the valve instructions. Tube sizes, fittings, pressure range and any lubrication policy are model-dependent.

Nitrogen or clean, dry compressed air may be used only when the actuator/pilot permits it. Workshop compressor tank pressure is not the valve's operating pressure; regulate it. Nitrogen **vent gas** has a separate regulated, metered route into the chamber. It is not the cryogenic helium circuit. Never connect workshop air, nitrogen or generic hose to the CTI helium couplings.

## Panel switches become requests

Disconnect the existing switching circuit from power before mapping it. Use continuity measurements through each switch position. Three connected terminals on a six-terminal DPDT can form **one SPDT pole**, not necessarily SPST. Three visible leads alone do not identify the switch's behavior. Record common, each throw, center position and any pilot connection; label the wires before changing anything.

In the retrofit, existing switches produce requests to the controller's input interface. Accepted requests drive the pilot through a rated output stage. Switches must not directly feed coil power in parallel with the interlock, because that would bypass permission checks.

Manual mode uses the same permissions as auto mode. If manual operation must still function while the Uno is failed or removed, that requires a separately designed physical permissive circuit. The Uno-only architecture does **not** provide that independence. Decide this requirement before final panel wiring. No manual “override” may defeat the stated guardrails.

## Electrical interfaces

Before selecting a driver, record coil AC/DC voltage, current, duty rating, number of coils, suppression, pilot normal state and any close-coil requirement. Driver ratings must cover continuous current and heating, not only a marketing peak rating. Match flyback suppression to a DC coil and required release time; AC coils require a different scheme.

Adafruit **6318, eight-channel I²C solenoid driver**, is a candidate for compatible 3–24 V DC loads. Its extra GPIO may reduce the need for a separate expander. It is **not selected for the actual gate yet**. Neither its outputs nor a generic I²C expander are protected 24 V position inputs.

Provide suitably rated input isolation/conditioning for each field sensor type. Dry contacts, sourcing sensors, sinking sensors and open collectors require different wiring. Read OPEN and CLOSED feedback independently where available; inconsistent states must be detected. Secure terminal blocks, labeled cables, strain relief, appropriate fusing and an enclosure replace loose breadboard field connections before a real-valve trial.

## Physical fault response

The Uno asks for closure, but firmware cannot guarantee closure after a welded output, stuck pilot, loss of air or jammed gate. Confirm the actual actuator behavior. Include an independent means to inhibit opening outputs on controller/watchdog loss. If the actuator needs air or a close coil to close, preserve the needed closing service or engineer an appropriate alternative.

An I²C driver can retain its last output if communication or the MCU stops. A software watchdog alone is insufficient evidence that a valve closes. Test output-enable removal, reset/brownout, lost I²C, lost gas and stuck-open conditions. A valve that fails to prove closed must keep vent inhibited.

## What the one-gate stand can and cannot validate

Phase 3 validates the cryo gate's motion, feedback, driver and cold/pressure permissions. It does not prove a fully automatic vent guardrail if vent or roughing still uses an unmonitored handwheel. Phase 4 must add or verify controllable roughing and vent isolation, real closed proofs and filament-off proof before a full autonomous test.

You can test software with simulated switches and dummy DC loads first. You do not need replicas of every commercial pump. For final validation, the actual field valves and their interfaces must pass the electrical, timing and failure tests.
