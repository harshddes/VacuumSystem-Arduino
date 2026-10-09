# Editable schematics

Revision 2026-10-09

| Drawing | Meaning |
|---|---|
| [phase1-uno.svg](phase1-uno.svg) | Exact electrical connections for the LED exercise; three 470 Ω series resistors |
| [test-stand-concept.svg](test-stand-concept.svg) | Proposed cryo / roughing / vent paths with reported equipment models |
| [control-architecture.svg](control-architecture.svg) | Requests, field inputs, Uno decisions, driver, power and pilot/actuator services |
| [maize-vacuum-concept.svg](maize-vacuum-concept.svg) | Future MAIZE branch concept including optional turbo/backing function |
| [maize-uno.drawio](maize-uno.drawio) | All four sheets as editable diagrams.net geometry |

The Phase 1 sheet is a pin-connection schematic, not an assumed breadboard row layout. Input contacts represent the three buttons and seven removable sensor-simulation jumpers. The guide supplies the exact wire count.

Vacuum gauge/valve conventions are adapted from the Leybold vacuum-diagram symbol reference. Resistors, contact switches, LEDs and ground use conventional circuit symbols. Pump family markings are explanatory. These are functional development drawings, **not a certification of ISO/DIN compliance or an as-built survey**. Line legend and tags are included on each vacuum sheet. Every chamber path still has to be traced physically.

The control architecture separates electrical signals, coil power and pneumatic service. Cryogenic helium/cooling connections are equipment services, not chamber vacuum pipes; see [the equipment guide](../07-equipment-and-services.md).

To edit, open diagrams.net and select File → Open From → Device, then choose `maize-uno.drawio`. To regenerate the baseline SVGs and drawing from source:

```bash
python development/schematics/build_schematics.py
```

The generator uses only Python's standard library. It overwrites the generated drawings, so retain manual edits in a separately named drawing or update the generator accordingly. Create actual connector/driver circuit drawings in KiCad once field terminals are identified; do not infer a field terminal map from the conceptual arrows.

SVGs are vector files and can be viewed in a browser or exported to PDF from diagrams.net. The state-machine diagram is maintained in [controller-design.md](../05-controller-design.md).
