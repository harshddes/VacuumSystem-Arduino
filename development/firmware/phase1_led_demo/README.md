# Uno LED bench firmware

Open `phase1_led_demo.ino` in Arduino IDE with `bench_logic.h` beside it. Select Arduino Uno and upload. No additional Arduino libraries are required. Serial status is 9600 baud.

Use [the wires guide](../../02-wires.md), with this board's two moves: the vent-closed wire is on D12 and the pressure-valid wire is on D13. D5, D6, and D11 are unused. Inputs are true when connected to GND. Outputs A0–A2 each need a series 470 Ω resistor and an LED.

There is no start-over button. The vent lamp follows the vent button while the cryo button is off. The cryo lamp follows the cryo button while the vent button is off. Both buttons on turns both door lamps off and the fault lamp on. A button that is already on still counts.

`bench_logic.h` contains the decision logic. The sketch handles contact filtering and nonblocking status printing. The tests in `../../tests/` cover the core on a host compiler and perform a host-stub syntax check of the sketch.

**BENCH ONLY:** no real pressure, temperature, valve feedback, coil outputs, motion timers or independently supervised closing service are implemented. Do not repurpose the LED pins as field driver outputs. Later firmware is developed after the field interfaces are identified and tested.
