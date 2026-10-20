# Phase 1 — build this now

> **Legacy direct-pin baseline:** this page assumes working D5/D6/D7 and the original re-arm sketch. The current board has reported failures on those pins, and the later simplified direct-pin sketch has different behavior. For the ordered expander, use the complete [2026-10-20 bench package](bench-prep/README.md), its own drawing, pin map and matching sketch. Do not wire this legacy table to that new firmware.

Revision 2026-10-09 • Arduino Uno R3 • USB-powered buttons and LEDs only

## Parts on the desk

| Part | Quantity used |
|---|---:|
| Uno R3, breadboard, laptop and suitable USB data cable | 1 each |
| Male-to-male jumper wires | **20** |
| Ordinary visible LEDs | 3 |
| 470 Ω, ¼ W resistors | 3 |
| Momentary normally-open buttons | 3 |

Buying 40 jumpers gives spares. You do not need female jumpers, a relay board, a 24 V supply or a display for this phase. Borrow a multimeter to check breadboard rails and button contacts.

## Pins and labels

All inputs use `INPUT_PULLUP`: connected to Uno GND means **true**, disconnected means **false**. Do not connect these inputs to any real gauge or equipment terminal.

| Uno pin | Label | Connection |
|---|---|---|
| D2 | CRYO REQUEST | Button to GND |
| D3 | VENT REQUEST | Button to GND |
| D4 | CRYO CLOSED | Removable simulation jumper to GND |
| D5 | VENT CLOSED | Removable simulation jumper to GND |
| D6 | PRESSURE VALID | Removable simulation jumper to GND |
| D7 | PRESSURE LOW ENOUGH | Removable simulation jumper to GND |
| D8 | CRYO COLD / READY | Removable simulation jumper to GND |
| D9 | OTHER PUMP PATHS CLOSED | Removable simulation jumper to GND |
| D10 | FILAMENT OFF / PROCESS SAFE | Removable simulation jumper to GND |
| D11 | RE-ARM | Third button to GND |
| A0 | CRYO OPEN ALLOWED | 470 Ω → LED anode; LED cathode to GND |
| A1 | VENT OPEN ALLOWED | 470 Ω → LED anode; LED cathode to GND |
| A2 | DISARMED / REJECTED | 470 Ω → LED anode; LED cathode to GND |

A0–A2 are digital outputs in this sketch. D0/D1 remain available for USB serial. A4/A5 remain reserved for later I²C interfaces.

## The exact 20-wire count

| Wires | Connection |
|---|---|
| W01 | Uno GND → one continuous breadboard ground rail |
| W02–W03 | D2 → cryo button; its other switched contact → ground rail |
| W04–W05 | D3 → vent button; its other switched contact → ground rail |
| W06–W07 | D11 → re-arm button; its other switched contact → ground rail |
| W08–W14 | D4, D5, D6, D7, D8, D9, D10 → ground rail, one removable wire each |
| W15–W17 | A0, A1, A2 → the free end of their respective resistor |
| W18–W20 | Each LED cathode → ground rail |

Put each resistor's second lead and that LED's anode in the **same connected breadboard strip**. This needs no additional jumper. Each resistor's two leads must occupy different strips. Each LED's two legs must occupy different strips. Use three separate branches.

If the ground rail is split in the middle, use an extra wire to bridge it, or keep every connection on the same continuous segment. The 20-wire count assumes that single segment. With USB unplugged, verify rail continuity rather than trusting the painted line.

For four-leg tactile buttons, two legs are often already internally connected. Identify two contacts that are disconnected at rest and join when pressed. Use a continuity meter with the circuit unpowered. Using the permanently joined pair makes the request permanently true. Position buttons across the breadboard center gap only after checking their contact orientation.

An ordinary untrimmed LED's long lead is generally its anode; its shorter lead/flat body edge generally marks the cathode. Check the component if leads have been cut. Resistors work either direction. Use one series resistor for **every** LED.

See [the Phase 1 electrical schematic](schematics/phase1-uno.svg). This is a connection diagram; breadboard row numbers depend on your actual breadboard.

## Upload

1. Unplug USB while wiring. Leave both request buttons released. Install the seven simulation jumpers for an initially permissive fake sensor state.
2. Open Arduino IDE. Open `firmware/phase1_led_demo/phase1_led_demo.ino`; keep `bench_logic.h` in the same sketch folder.
3. Select **Arduino Uno** and the correct USB port. Click Verify, then Upload. This sketch uses no additional libraries.
4. Open Serial Monitor at **9600 baud**. Allow at least 100 ms for contacts to settle.
5. Initially only DISARMED / REJECTED lights. Press and release RE-ARM. That LED goes off if no request is active.
6. Hold CRYO REQUEST: cryo LED lights. Release: it goes off. Hold VENT REQUEST: vent LED lights when all its fake permissions are true. Release: it goes off.
7. Complete [the desk tests](06-tests.md), including unplugging a permission while the corresponding LED is on.

Use the separate D11 RE-ARM button, not the Uno board's hardware RESET button. Board RESET restarts the sketch in the disarmed state.

## What the LEDs mean

They show accepted requests, **not measured valve position**. Your jumpers do not change automatically when an LED turns on. They are fictional sensor states deliberately set by you. For example, unplug D4 to pretend the cryo gate is no longer closed before testing whether vent is rejected.

Hold-to-request operation is intentional in this exercise. A denied request is not queued: restoring a jumper while holding the button will not open its LED. Release and make a fresh request. Loss of a required permission during an accepted request or simultaneous requests disarms the system; release both requests, press/release RE-ARM, then make a new request.

The 30 ms debounce is for desk contacts. It is not a validated chamber fault-response time. The code has no actual pressure parser, coil driver, valve travel timer, temperature readout or independent hardware shutdown. Those belong to the later phases.

