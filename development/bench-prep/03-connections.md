# Wire connections and component identification

Use one setup at a time. Disconnect USB before changing between them. Terminal names refer to silkscreen on the purchased module, not wire colour or the schematic box's orientation.

## Day 1: DFR0627 loopback


| Wire ID | From              | To              | Purpose                                   |
| ------- | ----------------- | --------------- | ----------------------------------------- |
| L-01    | Uno 5V            | DFR0627 I2C `+` | Logic supply                              |
| L-02    | Uno GND           | DFR0627 I2C `-` | Logic reference                           |
| L-03    | Uno A4/SDA        | DFR0627 `D`     | I2C data                                  |
| L-04    | Uno A5/SCL        | DFR0627 `C`     | I2C clock                                 |
| L-05    | DFR0627 UART1 `T` | Same UART1 `R`  | Return transmitted bytes to that receiver |
| L-06    | DFR0627 UART2 `T` | Same UART2 `R`  | Test the other UART                       |


Set the two address **DIP switches** A1 and A0 to **1**. The bundled sketch uses those settings. No Uno expansion shield is required if the four labelled connections are made correctly. Do not connect DFR0627 T/R to an RS232 port or directly to the Hornet's RS485 pins.

The diagnostic sketch prints PASS/FAIL repeatedly, sends a known byte pattern including 0x00 and 0xFF, and reports cumulative counts. USB Serial Monitor is **115200**; module UARTs are **9600**. Those two baud rates serve different links and need not match.

## Day 1: change to RS485 logic harness

Remove both loopback jumpers with power disconnected. The complete connection schedule is:


| Wire ID | From | To |
| --- | --- | --- |
| R-01 | Uno 5V | DFR0627 `+` |
| R-02 | Uno 5V | DFR0845 Gravity logic `+` |
| R-03 | Uno GND | DFR0627 `-` |
| R-04 | Uno GND | DFR0845 Gravity logic `-` |
| R-05 | Uno A4/SDA | DFR0627 `D` |
| R-06 | Uno A5/SCL | DFR0627 `C` |
| R-07 | DFR0627 UART1 `T` | DFR0845 logic `T` |
| R-08 | DFR0627 UART1 `R` | DFR0845 logic `R` |


Match the letters. On 2026-11-02 a crossed pair left the DFR0845 TX light dark, and the matched pair brought a Hornet reply. No D5/D6/D7 connection is involved.

DFR0845 has separate **logic-side GND** and **isolated bus-side GND**. Their locations are different; do not join them just because both include the word ground. Its RS485-side 12V output and its separate 12V-IN terminals remain unused. A power check alone does not prove RS485 data communication. Another working RS485 endpoint and its verified harness are required for that test.

Do not use the UART loopback sketch to query the Hornet. It emits test bytes, not documented instrument queries.

The one Hornet read-only trial uses these eight R-wires plus three gauge-side jumpers on Adafruit 3123 screws 6, 9, and 4. Follow only [07-hornet-read-trial.md](07-hornet-read-trial.md) while making those three wires. That page is still not a released harness.

## Day 2: fixed input-expander map

Start a separate bench setup; remove the two DFRobot modules for this test. Connect Uno 5V/GND/A4/A5 to the 5346 **VIN/GND/SDA/SCL** respectively. Set the 5346 to **0x21** by connecting its front address **D0** to **VIN**. Front D1/D2 remain at their default low setting. Alternative: close only the +1 solder jumper instead of adding the D0 wire.


| 5346 terminal | Library index | Signal                             | Desk connection                   |
| ------------- | ------------- | ---------------------------------- | --------------------------------- |
| A0            | 0             | Cryo request                       | Normally-open button to LOGIC_GND |
| A1            | 1             | Vent request                       | Normally-open button to LOGIC_GND |
| A2            | 2             | Cryo physically closed, simulated  | Removable ground jumper           |
| A3            | 3             | Vent physically closed, simulated  | Removable ground jumper           |
| B5            | 13            | Pressure valid, simulated          | Removable ground jumper           |
| A5            | 5             | Pressure low enough, simulated     | Removable ground jumper           |
| A6            | 6             | Cryo cold/ready, simulated         | Removable ground jumper           |
| B0            | 8             | Other pump paths closed, simulated | Removable ground jumper           |
| B1            | 9             | Filament off, simulated            | Removable ground jumper           |
| B2            | 10            | Re-arm                             | Normally-open button to LOGIC_GND |


Inputs use internal pull-ups: grounded=true; open=false. On this physical board, pressure valid is expander **B5** and re-arm is expander **B2**. For the Day 2 lamp bench, expander A4, B3, and B4 stay empty. Phase 3 lands only the closed reed on **B3**. A4 is empty and not read. The melted open switch stays off the board, so B4 stays empty. Follow only [08-gate-position.md](08-gate-position.md) for that wire and for D8. The 5346 **A7 and B7 are not used as inputs**, following the current Adafruit warning about changing inputs on these bits. The sketch holds them as unused LOW outputs with no external wires. A2 stays the simulated cryo-closed jumper and is not reused as the real gate.

Uno A0 -> 470 ohm resistor -> cryo LED anode; cathode -> LOGIC_GND.

Uno A1 -> another 470 ohm resistor -> vent LED anode; cathode -> LOGIC_GND.

Uno A2 -> another 470 ohm resistor -> fault LED anode; cathode -> LOGIC_GND.

The 6318 driver is **optional** for this drawing. Connect only its logic Vcc/GND/SDA/SCL to the same four shared connections. Keep its address at default **0x20**. The sketch does not drive it. Leave **V+ and every load output unconnected**. The single-channel 5648 is a spare, not a required extra connection.

The complete Day 2 wire IDs G-01 onward are in `wire-schedule.csv`. Same-net connections can use a verified common rail; check whether your breadboard rails are split. These are desk contacts, not electrically qualified interfaces for long field cables or 24V sensors.

## Phase 3: gate reeds, Tongling relay, Humphrey 24 V

This circuit is not in the three KiCad bench drawings. Follow only [08-gate-position.md](08-gate-position.md). Wire IDs P-01 through P-11 are in [phase3-wire-schedule.csv](phase3-wire-schedule.csv). The 5 V board is a module: DC+ / DC− / IN and COM / NO / NC. No extra transistor. H/L jumper on **H**. 24 V negative does not join Uno ground. The 6318 is not in this circuit. The melted open switch stays off the board. A4 and B4 have no wire. The closed reed signal is on B3.

## Physical identification rule

Read the actual printed label or moulded connector pin number. A commercial Gravity cable can contain a convenient set of wires, but neither its colours nor a diagram viewed from the back proves terminal identity. If the delivered board's markings differ, leave it unpowered and compare its revision against the source register.