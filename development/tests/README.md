# Software verification

From the repository root, run:

```bash
bash development/tests/run_tests.sh
```

Requires Bash and a C++11 compiler; default `g++`, configurable using `CXX`. Build outputs go to a temporary directory and are removed. No hardware or Arduino libraries are required for these host checks.

The core checks **519 scenarios**: every combination of seven fake sensor flags and two requests (512), plus seven history cases covering startup, denied held requests, lost permissions, conflicts and a RE-ARM button held at boot. Safety properties include mutually exclusive cryo/vent outputs and required permissions for every accepted output.

The separate syntax check compiles the sketch with `arduino_stub.h`. Stubs are test-only and are never part of an Arduino upload. This check does not emulate the processor, serial buffer or electrical inputs. It is not an AVR target build.

For target compilation, use Arduino IDE Verify/Upload with board **Arduino Uno**, then perform [the desk tests](../06-tests.md). An optional Arduino CLI command, when that tool is installed, is:

```bash
arduino-cli compile --fqbn arduino:avr:uno development/firmware/phase1_led_demo
```

Install the Arduino AVR Boards core through the normal IDE/CLI workflow if absent. The committed results record reports exactly which checks were actually run.
