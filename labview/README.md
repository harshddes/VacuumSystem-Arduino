# MAIZE Vacuum Console

Open **MAIZE Vacuum.lvproj** in desktop LabVIEW. Under **My Computer**, double-click **MAIZE Vacuum Console.vi** and click the Run arrow or press **Ctrl+R**. The VI opens in simulation. Its front-panel controls, scan loop, waveform chart and indicators are native LabVIEW objects. **End session** stops the VI.

Keep `MAIZE.Telemetry.exe` beside the VI. The block diagram calls this Windows .NET Framework helper once per scan for simulation, bounded Ethernet acquisition and CSV storage. The helper exits after each sample. The panel uses neither a serial port nor an Opta-specific NI driver.

## What each valve indication means

MAIZE has **two instrumented gates, Cryo and Turbo**. Each has a CLOSED and an OPEN reed. The other two valves have no position switches. Their names and the assignment of the four relays to physical valves are unknown. This corrects the eight-reed assumption in the November 17 implementation plan.

| CLOSED reed | OPEN reed | Gate feedback |
|---|---|---|
| 1 | 0 | CLOSED |
| 0 | 1 | OPEN |
| 0 | 0 | NO PROOF |
| 1 | 1 | CONFLICT |

S1–S4 display selector requests. R1–R4 display software coil commands. K1 is the independent inhibit device's feedback contact. The display keeps these three signals distinct. It makes no association between a relay number and a named gate. When the named contact mapping is unverified, both gate rows read **UNKNOWN**, and the raw four-bit input value is still available for commissioning.

## Try the operator panel

1. Run the VI. The simulator starts disarmed with both CLOSED reeds made. The pressure chart shows an illustrative Torr signal sampled twice per simulated second.
2. With all four simulated selectors off, press **Sim ARM / RESET**, then switch **Sim selector S1** on. The request and R1 command turn on. Both gate positions still follow their own reed inputs.
3. Switch **Sim air loss** on. The fault latches, and the relay commands clear. Restore air, turn the selector off and press **Sim ARM / RESET** again. Holding an old request through recovery cannot reopen a channel.
4. Use the four simulated reed switches to exercise the truth table. **Sim gauge loss** puts a gap in the chart. **Sim AUTO mode**, followed by a fresh arm and a pumpdown or vent start, displays a hold for missing path mapping and closure evidence.
5. Enable **Record CSV** to record the session. The CSV recording indicator shows the file in the Windows Documents folder under `MAIZE Vacuum Logs`. Switching source or stopping and starting recording creates a new file. A live transport failure records a timestamped gap with empty measurement and command fields. **End session** stops acquisition.

## Connect over Ethernet

Enter the IPv4 address of a controller implementing the protocol below, then turn on **Opta Ethernet**. The address prefilled in the VI, `192.168.10.42`, is a proposed bench address. No physical controller was discovered at that address during development. The client sends a read request about twice per second and waits up to 430 ms for its reply. A missing or rejected reply clears equipment readings to UNKNOWN. The simulation controls have no effect on live equipment.

For an end-to-end desktop check, start the included loopback fixture and select `127.0.0.1` in the VI. The sequence field will show `LOOPBACK_FIXTURE`. Stop the fixture with Ctrl+C to see the disconnected display.

```powershell
python .\verify.py --fixture
```

## Opta commissioning sketch

`firmware/OptaTelemetry/OptaTelemetry.ino` compiles for the Opta and one D1608E mechanical expansion. It publishes actual digital inputs and identifies its operating state as `HOLD / COMMISSIONING`. It issues no actuator or indicator relay commands. It is a separate commissioning image. Uploading it would replace the Opta's resident program. An existing machine controller can implement the same telemetry message in its own firmware.

| Proposed input | Signal |
|---|---|
| Base I1, I2 | Cryo CLOSED and OPEN |
| Base I3, I4 | Turbo CLOSED and OPEN |
| Base I5–I8 | Unassigned |
| E1 I1–I4 | Four selector contacts |
| E1 I5–I8 | MANUAL, AUTO, ARM/RESET, CLOSE/STOP healthy |
| E1 I9–I12 | PUMPDOWN START, VENT START, AIR OK, ROUGH READY |
| E1 I13–I16 | CRYO READY, FILAMENT OFF proof, LAB ENABLE, K1 feedback |

This proposed allocation uses **20 inputs**. Set `controllerIP` to the chosen bench address. Match the four entries in `gatePins` to the verified contact assignments before setting `gateWiringConfirmed`. The sketch checks the D1608E type and digital-read transaction. A missing expansion or failed read makes its signals unknown.

Hornet acquisition defaults off. The optional reader implements only the repository's address-1 binary CG1 read at 19200 8N1. It checks exact frame length, reply marker, address, command, status, CRC and finite positive pressure. Enable `readHornet` after the gauge settings and isolated connection are confirmed. Set `gaugeConfiguredInTorr` only after verifying that unit on the gauge. Native-unit readings remain labeled NATIVE. Only fresh Torr values enter the chart. The reader rejects the known off sentinel, and the Torr path rejects the repository's 1100 ± 1 Torr open-jack indication. The installed Hornet firmware/manual match remains open. This pressure channel is for display and logging.

## Read protocol

The UDP port is **44820**. Each request is exactly 18 ASCII bytes, `MAIZE2 R ` followed by eight hexadecimal nonce characters and LF. Replies contain one ASCII CSV record with no header.

```text
MAIZE2,nonce,seq,uptime_ms,gate_bits,e1_ok,e1_bits,coil_cmd,aux_cmd,step,pressure,unit,age_ms,fault,gate_map_verified
```

- All bit masks and counters are decimal on the wire. Gate bits 0–3 correspond to the four contacts in the input table. E1 bit 0 is I1. Command bits 0–3 correspond to R1–R4. Auxiliary bits 0–4 correspond to READY, MOVING, FAULT, buzzer and filament-OFF request.
- `e1_ok` and `gate_map_verified` are each 0 or 1. A verified gate map refers only to the reed assignments. A command bit reports the controller's requested output state, independently of physical position.
- The sample sequence and uptime are unsigned 32-bit values. The commissioning sketch updates its input scan every 100 ms. A stalled sequence, bad nonce or malformed reply produces a gap. A backwards clock is marked in the log.
- `pressure` is a number in the supplied unit or `-` for unavailable. `unit` is `TORR` or `NATIVE`. The panel suppresses samples older than 2000 ms. This display timeout has no standing as a process permission. Step and fault codes contain up to 32 uppercase ASCII letters, digits or underscores.

## Build and verify

Run these commands in this directory. The executable and editable VI are already included.

```powershell
& "$env:windir\Microsoft.NET\Framework\v4.0.30319\csc.exe" /nologo /target:winexe /optimize+ /r:System.Web.Extensions.dll /out:MAIZE.Telemetry.exe Telemetry.cs
python .\verify.py
$cli = 'C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
& $cli compile --fqbn arduino:mbed_opta:opta .\firmware\OptaTelemetry
```

The local build used Arduino Mbed OS Opta Boards 4.6.0, Arduino_Opta_Blueprint 0.2.9 and ArduinoRS485 1.1.1. The desktop tests cover all sixteen reed combinations, the distinction between command and proof, fault and re-arm behavior, sequence holds, loopback UDP, wrong and stale replies, pressure validity and CSV gap handling.

The project and its VI were opened in the installed 32-bit LabVIEW 2026 editor. A LabVIEW test drove the actual front panel through ARM, an S1 request, simulated air loss, Ethernet acquisition from a loopback responder and loss of that responder. The VI's CSV showed R1 turn on while the gate bits stayed at 5 (both CLOSED), then R1 clear on air loss. In Ethernet mode it recorded gate bits 6 (Cryo OPEN, Turbo CLOSED) followed by an explicit gap with blank equipment data.

Production motion still requires a verified relay-to-valve map, the two remaining valve functions, an agreed way to establish required isolation on unsensed paths, the actual readiness interfaces and limits, and installed-system acceptance. Physical Opta, gate and Hornet operation remains unverified.
