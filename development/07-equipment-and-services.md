# Equipment inventory and services

Revision 2026-10-09 • Models below are user-reported unless noted; functionality is not yet certified

| Equipment | Intended role | What is still needed or must be checked |
|---|---|---|
| Arduino Uno R3 | Controller prototype | USB data cable, board upload test; later secured power/I/O |
| Cryo-Torr 8 | Test-stand high-vacuum pump | Correct helium pair, coldhead electrical connection, temperature readout, pre-evacuation route and readiness proof |
| CTI 8200 compressor | Cryogenic helium compressor | Exact variant, mains requirements, air/water cooling, matching service condition and hoses |
| Agilent IDP-15 | Preferred dry roughing source | Installed variant, inlet isolation/control, fittings, exhaust route and running-ready proof |
| InstruTech IGM402YFD | Chamber pressure instrument | INFO firmware, working supply, installed sensor range, cables and connector labels |
| Worker Bee CVG101GC, possibly available | Low-vacuum convection sensor | Locate/test; verify flange, matching Hornet cable and readings |
| Large cryo gate, model unknown | Cryo isolation | Nameplate, actuator/pilot, power/gas behavior and feedback wiring |
| Small handwheel angle valves | Manual isolation presently available | Route/function; legacy label appears SA0100MVQF, current-product equivalence unconfirmed |
| Nitrogen cylinder | Potential vent or permitted actuation gas | Appropriate regulator, independent secured routes, metering and actual actuator compatibility |
| DeWalt 175 max PSI / Bostitch 8 gal | Potential actuation-air source | Clean/dry regulated service, actuator-compatible pressure, supply-pressure proof |
| Alcatel 2008A / Varian SD-90 | Oil-sealed roughing alternatives | Actual condition, correct oil/service, inlet isolation and exhaust management |
| KJL TSR4MS100QF | Foreline molecular-sieve trap | Confirm label, location, service/regen procedure; not an exhaust mist filter |
| Turbo-V 250, possibly available | Optional future branch | Exact pump/controller, flange, compatible backing, readiness and cooling; outside initial build |

## Cryogenic compressor connections

The CTI compressor circulates **helium** through supply and return hoses to the cryopump coldhead. The coldhead also has an electrical drive connection. Mains power is separate. Cooling requirements depend on the **actual 8200 variant**: inspect the rear/side label and cooling ports rather than assuming every 8200 needs water.

The compressor's adsorber, helium charge and service instructions belong to the CTI system. They are not interchangeable with workshop-compressor parts. Do not buy helium, replacement adsorbers or cooling hardware before identifying what is already present and whether service is actually due.

The cryopump temperature/readiness signal needs a compatible existing readout or controller. Identify the installed sensor and connector first; the Cryo-Torr family manual describes cryogenic temperature sensing. A room-temperature Arduino sensor such as a DS18B20 cannot replace a sensor at cryogenic temperatures. Compressor ON alone does not prove the pump is cold enough.

## Scroll pump and oil-pump alternatives

Agilent's standard IDP-15 has a KF25 inlet and KF16 exhaust; confirm the actual installation. Use appropriate vacuum-rated fittings and an approved exhaust route. An optional inlet-valve kit exists, but whether your pump has it, and whether it can be independently controlled as chamber isolation, must be checked. Power-linked anti-suckback is not automatically an independently commanded roughing valve.

Prefer reusing the dry scroll for the initial stand if serviceable. No oil-backstreaming trap is needed merely because that pump is a scroll. If an oil-sealed pump is used, distinguish:

- **Inlet/foreline trap:** reduces selected vapors/backstreaming between chamber and pump.
- **Exhaust mist filter:** handles oil mist at the pump outlet.
- **CTI compressor adsorber:** part of the separate helium refrigeration circuit.

The reported KJL molecular-sieve foreline trap is not proof that oil-pump exhaust mist is handled. Identify the actual exhaust arrangement and trap regeneration requirements separately. Heater supply for trap regeneration is not an Uno-controlled task in this plan.

## Test-stand topology

The [test-stand drawing](schematics/test-stand-concept.svg) is a proposed functional arrangement: chamber gauge, cryo isolation, roughing isolation and metered vent. It is not an as-built survey. Record every existing tee, manual bypass, pump-to-chamber path and flange before installing automatic outputs.

No turbo is needed to validate the initial cryo controller. A turbo installation may require KF, ISO or ConFlat hardware depending on its actual flange; do not buy a guessed ConFlat adapter. Sharing one scroll between turbo backing and chamber roughing changes the routing and interlock design and must be explicitly engineered if that configuration is later used.
