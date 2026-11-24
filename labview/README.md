# MAIZE vacuum rack

Open **MAIZE Vacuum.lvproj** in desktop LabVIEW. Under **My Computer**, open **MAIZE Vacuum Console.vi** and press **Ctrl+R**. **End session** stops the display. The Opta runs its own control loop when the PC is disconnected.

To operate the panel without a board, open the separate [MAIZE Offline project](offline/MAIZE%20Offline.lvproj). Its [offline controls and exercises](offline/README.md) cover manual requests, pumpdown, venting and fault recovery.

The live LabVIEW console retains its valve telemetry layout. Each lever reads its physical manual selector. Its four screen indicators show **red for OPEN**, **green for CLOSED**, and **grey for unknown or contradictory position**. Loss of telemetry clears all four indications. See the [replacement faceplate layout](MAIZE_Front_Panel_Opta.svg) for the physical panel and the [offline console](offline/README.md) for the updated operator controls.

| Rack position | Valve | Source of the lamp |
|---|---|---|
| Upper left | Roughing | Physical Roughing toggle |
| Upper middle | Let-up | Physical Let-up toggle |
| Upper right | Turbo gate | Turbo gate OPEN and CLOSED contacts |
| Lower right | Cryo gate | Cryo gate OPEN and CLOSED contacts |

A gate with both contacts active shows **CONFLICT**. A gate between endpoints shows **UNKNOWN**. The controller allows an interval between contacts during a commanded movement and trips if the gate misses its travel deadline. The operator can read **Opening outputs** to see which OPEN commands the Opta issued and which manual requests it inhibited. For example, an inhibited Let-up request leaves its selector-derived lamp red. In AUTO, these same two selector-derived lamps continue to follow their toggles while **Opening outputs** reports sequence commands.

## Test with an Arduino Uno R3

On the LabVIEW panel, the lever is the **left-hand graphic** in each valve group and the colored lamp is on its right. The lever follows the physical switch over USB on the bench. The dark circle with no lever means there is no current selector reading. Use the switch or jumper wired to the Uno to change the request.

The [bench test screenshot](Front%20Panel.png) shows the lever positions and the expected LabVIEW response to conflicting Roughing and Let-up requests. It was captured using a test frame with the Uno disconnected.

The Uno runs the shared controller and drives low-voltage test LEDs. Use the Uno's own GND for every switch or jumper below. Keep the bench circuit electrically separate from the rack, its 24 V I/O, its interlock power and its valve coils. For each external LED, connect the output through a 330 Ω series resistor to the LED anode and connect the cathode to GND.

| Function | Uno pins | Bench connection |
|---|---|---|
| Four toggles | D2 Roughing, D3 Let-up, D4 Turbo, D5 Cryo | Connect each SPST toggle between its pin and GND. Grounded requests OPEN. Floating requests CLOSED. A jumper can stand in for a switch. |
| Turbo feedback | D6 CLOSED, D7 OPEN | Ground only the active endpoint. Start with D6 grounded. |
| Cryo feedback | D8 CLOSED, D9 OPEN | Ground only the active endpoint. Start with D8 grounded. |
| ARM/RESET | D10 | Momentary connection to GND, then release. |
| Combined bench permissive | D11 | Ground to enable bench readiness. Removing this jumper forces an inhibit. |
| OPEN command LEDs | D12 Roughing, D13 Let-up, A0 Turbo, A1 Cryo | Optional external LEDs. The Uno's built-in D13 LED also reports Let-up OPEN command. |
| Bench pressure input | A2 | For a low reading, ground A2. For a high reading, leave A2 disconnected. For an adjustable reading, put a 10 kΩ potentiometer across the Uno's 5 V and GND with its wiper on A2. |
| Optional AUTO inputs | A3 AUTO mode, A4 PUMPDOWN, A5 VENT | Leave A3 open for MANUAL. Ground A3 to select AUTO. With all four valve toggles at CLOSED, momentarily ground A4 or A5 to start the corresponding sequence after arming. |

1. Connect the Uno by USB. Close Serial Monitor so the bench bridge can own its COM port.
2. In PowerShell from the repository root, run `powershell -ExecutionPolicy Bypass -File .\labview\Start-UnoBench.ps1 -Upload`. This uploads the bench build to the Uno. If autodetection finds no unique Uno, add its Arduino IDE port, for example `-Port COM5`. Omit `-Upload` on later starts when the bench sketch is already loaded. You can also upload `OptaTelemetry.ino` from Arduino IDE with **Arduino Uno** selected and use the launcher without `-Upload`.
3. In the LabVIEW project opened by the launcher, run **MAIZE Vacuum Console.vi**. Look for **UNO R3 BENCH** under Controller link. The launcher uses a temporary project copy so your Opta address is preserved.
4. Start with D6, D8 and D11 grounded and D2–D5 open. Briefly ground D10 to arm. Turn Let-up OPEN. Its LabVIEW lamp goes red and the Uno's **L** LED lights when the opening is granted. With Let-up still OPEN, turn Roughing OPEN to trip the mutual exclusion. The two selector-derived lamps stay red, the **L** LED goes out, and the panel lists the conflicting requests and inhibited outputs.
5. To test the Turbo or Cryo lamp independently of its toggle, ground A2, arm, and request OPEN on D4 or D5. Move the corresponding feedback jumper from CLOSED to OPEN within eight seconds. The gate lamp follows that feedback jumper. On closing, move the jumper back to CLOSED. After a fault, return the requests and feedback to CLOSED, correct the cause, then press and release D10 once to acknowledge and again to arm.

Press **Ctrl+C** in the launcher to release the COM port. The bench uses its own pressure scale, timers and one-pump-at-a-time configuration. This exercises the controller and its display. Actual chamber pressure, the field wiring and Opta hardware still require commissioning.

## Operating logic

The physical MANUAL/OFF/AUTO selector chooses the source of requests. A fresh ARM edge with neutral requests and closed valves arms the controller. CLOSE/STOP takes priority. Changing mode cancels openings. After a protective trip, return requests to neutral, correct the failing conditions and close the gates. One ARM/RESET press acknowledges the latch and a subsequent press arms the system. Holding a selector through recovery cannot restart motion.

| Opening | Required conditions in addition to healthy common interlocks |
|---|---|
| Roughing | Let-up closed, no vent opening request, roughing ready and an approved pump-path combination |
| Let-up | No pump opening request, Roughing switch CLOSED, Turbo and Cryo physically CLOSED, hot filaments OFF and vent process permission |
| Turbo | Let-up closed, approved pump-path combination, fresh chamber pressure within the turbo limits, turbo at speed and backing ready |
| Cryo | Let-up closed, approved pump-path combination, fresh chamber pressure within the cryo limits and cryopump cold/ready |

Roughing and Let-up have selector indications. Their provisional closure condition requires a CLOSE selection, an opening output that is off, and the configured closing interval. The controller waits for the interval at startup and after panel I/O recovery before arming. It counts the Roughing path and any incompletely closed gate when checking a change of pump path. Field release requires validating the closing behavior and closure condition against the actual plumbing. Faults involving air, lab enable, coil-feed feedback, selector I/O, contradictory gate feedback or missed travel can inhibit openings. LabVIEW shows current and latched causes and evaluates the same rules in **Vacuum permissions.vi**.

Automatic pumpdown progresses from roughing to roughing isolation to cryo high vacuum. Automatic vent cancels pump openings, waits for isolation and filament-OFF proof, monitors the vent-complete pressure and then closes Let-up. Both sequences use the same opening rules as manual operation. Pressure units, entry dwell, trip hysteresis, travel limits, sequence deadlines and permitted pump combinations are installation settings. The physical lab inhibit remains independent.

## Replacement wiring and field release

This schedule follows the replacement panel. The controls are four black CLOSE/OPEN valve selectors, a black MANUAL/OFF/AUTO selector, four round action buttons, a green 24 V power indicator and a red 24 V latched fault indicator. The Widgetlords VP-EC-RDU-MINI is the local 20 × 4 character display. Verify field identity, polarity and actuator response before enabling the corresponding group in [Installation.h](firmware/OptaTelemetry/Installation.h).

| Terminals | Assignment |
|---|---|
| Opta I1–I4 | Cryo CLOSED, Cryo OPEN, Turbo CLOSED, Turbo OPEN |
| Opta I5–I7 | Turbo at speed, backing ready, vent process safe |
| D1608S I1–I4 | Roughing, Let-up, Turbo, Cryo manual OPEN requests |
| D1608S I5–I10 | MANUAL and AUTO mode contacts, blue ARM/RESET, red NC CLOSE/STOP healthy, white PUMPDOWN and yellow VENT START |
| D1608S I11–I16 | Air OK, roughing ready, cryo ready, filament OFF, lab enable, coil-feed inhibit feedback |
| Base relays 1–4 | Roughing, Let-up, Turbo and Cryo opening outputs, respectively |
| D1608S Q1 | Switch the external 24 V supply to the red fault lamp when a fault is latched, once the lamp's wiring is verified |
| Protected 24 V control rail | Green control-power lamp |
| Opta RS-485 | Hornet gauge. Bench-qualify the LCD addressing, bus isolation and gauge coexistence before adding display writes |

The as-delivered sketch holds actuator commands inhibited. The actuator adapter supports verified maintained, energized-to-open equipment with the established de-energized close response. Field confirmation includes the independent inhibit, input polarity, closing behavior after power or air loss, actual pump routing, qualified pressure/readiness interfaces, limits and travel times. The locally mounted LCD still needs its RS-485 write integration and an on-bench check. The Opta owns the opening permits.

The repository gives the operating conditions and keeps the commissioning values open. Its pressure record has unset cryo limits and travel times. The measured single-gate travel and pressure traces in the Uno bench folder describe a separate rig. The replacement firmware leaves numerical process settings unset until MAIZE values are entered. See the [permission rules](../development/05-rules.md), the [configuration record](../development/interfaces/configuration-record.json) and the [bench field record](../development/bench-prep/06-field-holds.md).

### Supply and coil protection

The proposed 120 V Humphrey coil feed uses a supplemental **1 A, 250 VAC, time-delay ceramic 5 × 20 mm fuse** on its line conductor, with the independent lab inhibit in series. Buy one working fuse and one spare plus one holder if the cabinet lacks them. The existing fuse specification is Littelfuse 0215001.MXP. The [0215001.HXP](https://www.tme.com/us/en-us/details/0215001.hxp/fuses-5x20mm-time-lag/littelfuse/) is the same electrical rating in a different package quantity. The planned internal holder is the [01500274Z](https://www.tme.com/us/en-us/details/01500274z/fuseholders-for-cable/littelfuse/). Check coil inrush, wire sizes, available fault current and upstream branch protection against the lab's cabinet drawing.

The [HDR-60-24](https://www.meanwell.com/Upload/PDF/HDR-60/HDR-60-SPEC.PDF) has a separate AC input feed with its own protection sizing. Mean Well specifies 30 A typical cold-start inrush at 115 VAC. Size the 24 V outgoing protection against the installed wiring and loads and verify that a branch fault clears with the supply's current limiting. The NC **CLOSE/STOP** contact goes to the controller as an operating stop. The independent lab inhibit removes the coil feed directly.

## Ethernet and records

The matching Opta firmware and [Opta.address](Opta.address) use **192.168.10.42** on the proposed local Ethernet segment. Set the PC-side address file to the actual controller address when installed. The native VI invokes the supplied Windows helper **MAIZE.Telemetry.exe** from its own directory. The application uses read-only UDP on port **44820**. No Opta-specific LabVIEW driver is needed.

MAIZE3 responses carry a request nonce, controller sequence and uptime, mode and stage, physical selectors and their quality, four positions, requested and commanded openings, readiness and timing flags, current and latched faults, and the Hornet CG1 pressure in Torr with sample age. A timeout, stalled sample or rejected packet clears the display. Valid samples and communication-loss transitions are recorded to daily CSV files under **%LOCALAPPDATA%\MAIZE Vacuum\Logs**. An acquisition failure records empty measurements. The controller continues enforcing interlocks independently of recording.

## Build and verification

- The project contains all four editable VIs. The shipped binaries run directly in desktop LabVIEW. Edit the block diagrams with **Ctrl+E**. If the shared permission source changes, rebuild the matching Formula Node before deploying the pair.
- The firmware entry point is [OptaTelemetry.ino](firmware/OptaTelemetry/OptaTelemetry.ino). It builds for `arduino:mbed_opta:opta` with Arduino Mbed OS Opta Boards 4.6.0, Arduino Opta Blueprint 0.2.9 and ArduinoRS485 1.1.1. Compiling the sketch leaves the connected hardware untouched.
- From this folder, build the helper with the .NET Framework C# compiler using `csc /nologo /target:winexe /optimize+ /out:MAIZE.Telemetry.exe Telemetry.cs`. Run `python verify.py` with `CXX` set to a C++14 compiler. Verification runs the controller source and a temporary loopback transport test. Test installation values exist only in the temporary build.
- [build_panel.py](build_panel.py) is the optional source generator. Set `LABVIEW_ROOT` to the installed LabVIEW directory and `AIXML_PYLABVIEW` to the composer's `scripts/aixml-pylabview` directory. The generator used for these files is [labview-mcp revision 6374683](https://github.com/Zuehlke/labview-mcp/tree/63746832b66f9e18b9b12ebaf8fefd7b461e7c18).

The desktop acceptance check exercised the native panel with valid Ethernet frames, rejected openings and a disconnected controller. The firmware and controller regressions were built locally. Physical valve response, installed wiring and pressure thresholds still require commissioning on MAIZE.
