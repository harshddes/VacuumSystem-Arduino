# Uno LED bench firmware

Open `phase1_led_demo.ino` in Arduino IDE with `bench_logic.h` beside it. Select Arduino Uno and upload. No additional Arduino libraries are required. Serial status is 9600 baud.

Use [the exact wiring guide](../../02-phase1-breadboard.md). Inputs are true when connected to GND. Outputs A0–A2 each need a series 470 Ω resistor and an LED.

Startup is disarmed. RE-ARM must first be released, then newly pressed with both request buttons released. Hold a request to light its permitted output; release to turn it off. A conflicting request or loss of an active permission disarms. Restoring a sensor cannot reopen an output without the appropriate fresh request/re-arm action.

`bench_logic.h` contains the decision logic. The sketch handles contact filtering and nonblocking status printing. The tests in `../../tests/` cover the core on a host compiler and perform a host-stub syntax check of the sketch.

**BENCH ONLY:** no real pressure, temperature, valve feedback, coil outputs, motion timers or independently supervised closing service are implemented. Do not repurpose the LED pins as field driver outputs. Later firmware is developed after the field interfaces are identified and tested.
