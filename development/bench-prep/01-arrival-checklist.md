# Module bench checklist

All ordered electronics are now reported received. The checklist order still applies. Historical Day 1/Day 2 project names identify separate setups; they no longer imply waiting for delivery. Receipt is not a physical test result.

## Preparation before connecting hardware

1. Pull this repository update into your existing Cursor checkout. If you already have local edits, save/commit them before pulling; do not overwrite them.
2. Install KiCad from https://www.kicad.org/download/windows/ (or your actual OS page). KiCad 9/10 can open the compatible-format files; retain a git checkpoint before any version conversion. GUI menu locations can differ slightly by version.
3. Open `kicad/day1-loopback/day1-loopback.kicad_pro`, then double-click the `.kicad_sch` in KiCad's project tree. Read the drawing without editing it.
4. In Arduino IDE, install **Arduino AVR Boards 1.8.6**, select **Arduino Uno**. Obtain dependencies using `resources/library-installation.md`. Verify the two sketches before connecting hardware; no Uno connection is needed merely to compile.
5. Put on the desk: Uno, USB data cable, laptop, multimeter, breadboard, suitable jumper leads. For Day 1 loopback there are six connections: four power/I2C and two T/R loops. Connector type determines which leads fit; inspect the actual supplied Gravity cable/header before assembly.
6. For Day 2 reserve three LEDs, three 470 ohm resistors, three normally-open momentary buttons, seven simulation jumpers, and leads for the common rails and modules. Do not invent breadboard row numbers; trace the actual connected strips with the meter while unpowered.
7. Locate the Hornet supply, connector/cable labels, INFO firmware and communications settings. This is preparation, not authorization to modify a running instrument.

## Setup 1: DFR0627 loopback, then separate DFR0845 logic harness

- Inspect part labels and connector orientation. Photograph the top/silkscreen if it differs from the source drawing.
- Disconnect the old LED-bench harness. Leave D5/D6/D7 disconnected. Build only `day1-loopback`.
- With USB unplugged, check polarity and wiring against L-01 through L-06. Check for an unintended 5V/GND short; a simple continuity beep is not by itself a full short-circuit diagnosis on populated electronics.
- Power from USB. Check the voltage across the DFR0627 + and - terminals before running the test.
- Upload `uart_loopback`. Serial Monitor **115200**, both module UARTs **9600**. Require repeated UART1 PASS and UART2 PASS. Record 20 successful cycles and five power-up trials; these are bench acceptance targets, not a reliability certification.
- With power removed, remove only UART1's loopback and repeat the test. UART1 must report FAIL while UART2 can still PASS. Restore the wiring unpowered and verify recovery.
- Only after the loopback passes, power down and change to `day1-rs485-logic`: remove both loops and fit R-01 through R-08. Do not leave T1/R1 shorted while connecting the adapter.
- DFR0845 bus terminals remain disconnected unless the additional Hornet/second-endpoint prerequisites in `06-field-holds.md` are satisfied. Do not use the UART loopback firmware with this harness.

## Setup 2: separate Adafruit input/LED bench

- Change to `day2-gpio-bench`; this is a separate setup. Disconnect both DFRobot modules for this test to reduce troubleshooting variables.
- Set 5346 address to **0x21** using its front address pin **D0 to VIN** as shown. Front D1/D2 remain at their default low setting. Alternative: close only the **+1** solder jumper instead of the D0 wire. Do not mistake this D0 for Uno D0.
- Build the three LED branches and the ten control/simulation contacts using the pin map. Verify the two switched contacts on each four-leg button with the meter.
- The optional 6318 can share 5V, GND, SDA and SCL at default **0x20**. Leave its V+ supply terminal and all eight load outputs unconnected. It is not needed for the input test to pass.
- Upload `gpio_interlock_bench`, Serial Monitor **115200**, and execute the acceptance table.
- Park the 5648, DE-9 breakouts and Perma-Proto. No additional board must be connected just because it arrived.
