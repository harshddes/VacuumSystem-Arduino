# Phase 3: one cryo-gate circuit

This is the only page to follow while wiring the HVA SG reeds, the 5 V
relay module (Tongling JQC-3FF-S-Z cube on the six-screw board), and the
Humphrey 24 V coil. The three KiCad bench drawings do not include this
circuit. The 6318 is not in it. No extra transistor.

USB stays unplugged while the wires go on. Air at or below 80 psig. Do
not move the speed-controller screws. Leave D5, D6, and D7 empty. The
three Day 2 LEDs on Uno A0, A1, and A2 are off this desk. Do not put
them back for Phase 3. The laptop print is the read. Uno A4 and A5 stay
the 5346 data and clock. Hornet and DFR0627 can stay on the bus. 24 V
negative does not join Uno ground.

Expander A2 may still have the old fake “cryo closed” jumper. Leave it
or pull it; it is not the real gate. The only position is the closed
reed on B3. A4 is empty. The open switch is a melted short. It is not a sensor.

Related pages:

- Desk package: [README.md](README.md)
- Pin map: [pin-map.csv](pin-map.csv)
- Wire list for this circuit: [phase3-wire-schedule.csv](phase3-wire-schedule.csv)
- Test names: [04-tests.md](04-tests.md)
- What is still unread: [06-field-holds.md](06-field-holds.md)
- Pass or fail lines: [verification/physical-test-log.csv](verification/physical-test-log.csv)
- Sketch: [firmware/gpio_interlock_bench/gpio_interlock_bench.ino](firmware/gpio_interlock_bench/gpio_interlock_bench.ino)

## What the sheets already say

The closed-position switch is a two-wire contact. It closes only
when the cylinder magnet is next to it. Ratings in the HVA / Lesker
installation manual: 3 W, 0.25 A switching, 100 V DC class. The Lesker
SG sheet caps the indicator circuit at 28 V DC and 20 mA. A 5 V pull-up
is inside both limits. 24 V across a reed is not the Arduino interface.

Air service is 80 psig maximum. Valves 6 inch ID and smaller lock closed
if air is lost. Valves 8 inch ID and larger that shipped with a solenoid
do not. Cryo-Torr 8 is an 8 inch pump; the gate ID is still unread, so
air-loss behavior stays unknown until the nameplate is read.

The Humphrey coil in this build is 24 V DC, 6.7 W, about 0.28 A,
spring-return 4-way. `062-4E1` and `125-4E1` are the same electrical
coil. A Uno pin cannot drive it.

The desk part is a 1-channel 5 V module with DC+ / DC− / IN and
COM / NO / NC. The cube is Tongling `JQC-3FF-S-Z` 5 V: coil about 69 ohm /
71.4 mA, form C, max 30 V DC. That is the same job as a Songle
SRD-05VDC-SL-C cube on the same six-screw board. The board already has
the driver, so Uno D8 goes only to IN. Set the H/L jumper on **H** so D8
high means click. 24 V at 0.28 A is inside the contact window. The
contact table is for a resistive load, so the Humphrey coil still gets a
diode across it.

The switch that used to mark open has melted. Its wires are shorted
together. That pair is not a sensor. Do not land it on any pin. No
sketch reads it. Position comes only from the closed reed on B3.

## Parts on the desk

- Adafruit 5346 already at 0x21, already on Uno 5V / GND / A4 / A5
- Red 1-channel 5 V relay module, screws DC+ / DC− / IN and NC / COM / NO
- One 1N400x diode across the Humphrey coil only. Stripe toward 24 V +
- 24 V DC supply for the Humphrey coil only
- Meter

Put the black H/L cap on the two pins next to **H**. Leave **NC** empty.

## The closed reed is the only switch

USB unplugged. 24 V off. If a pair already has more than 5 V on it from
an old lamp circuit, lift that circuit first.

The wires marked open are a melted short. Leave them off the board.
5346 A4 and B4 stay empty.

On 2026-11-16 the closed pair still had continuity, and A4 still read
NOT_CLOSED. Lift that signal wire off A4 and land it on B3.

## One wiring pass

Wire IDs are in [phase3-wire-schedule.csv](phase3-wire-schedule.csv).

Closed reed, 5 V only:

- One wire to 5346 **B3**, the other to logic ground.
  This pair is the closed mark. It moved off A4 on 2026-11-16.
- The melted open pair stays off the board. A4 and B4 have no wire.

Gate button. No resistor. The press pops back up; the Uno remembers it.

- One switched leg to 5346 **A0**.
- The other switched leg to 5346 **GND**, the same ground as the reed.

Uno **L**, next to **D13**, needs no wire. It stays lit while the closed reed is made, and it goes dark when that reed lets go. Vent **A1** and re-arm **B2** stay lamp-game contacts. They do not move this coil.

Relay module and Humphrey coil:

| From | To |
| --- | --- |
| Uno **5V** | module **DC+** |
| Uno **GND** | module **DC−** |
| Uno **D8** | module **IN** |
| 24 V **+** | module **COM** |
| module **NO** | Humphrey coil lead A |
| Humphrey coil lead B | 24 V **−** |
| 1N400x across Humphrey | stripe toward 24 V **+** |
| module **NC** | empty |

H/L jumper on **H**. 24 V negative stays off Uno ground. The 6318 V+
terminal and every 6318 load terminal stay empty. No 2N3904. No NTE159.

## Sketch

Upload `gpio_interlock_bench`. Serial Monitor **115200**, or open the Hornet window. Its gate page sends the same `o` and `c`, and the words change only after the Uno answers. Boot lines:

```text
GATE BENCH - MCP 0x21; B3 closed reed only; A4 empty; D8 LOW; L follows closed
A0 press toggles. USB o forces open. USB c or x releases.
```

One press of A0 holds the coil on after the finger lifts. The next press drops it and the spring returns. USB `o`, or the gate-page Open button, forces the coil on. USB `c` or `x`, or the gate-page Close button, drops it. The finger and the screen share one memory. The page does not decide on its own. If the expander falls off the bus, that memory clears and D8 stays low. Coming back does not reopen the gate. A press or `o` while the expander is offline is refused.

Each second, and on each change, it prints a line the Hornet window reads:

```text
GATE ASK=OPEN D8=1 REED=CLOSED SRC=BUTTON
```

ASK is `OPEN` or `RELEASED`. REED is `CLOSED` or `NOT_CLOSED` from the closed reed. SRC is `BUTTON`, `USB`, `BOOT`, or `BUS`. Once a second it also prints `CLOSED=`, `POS=`, `D8=`, and `L=`. `L=1` means the closed reed is made and the Uno L lamp is lit. `POS=` is `CLOSED` or `NOT_CLOSED`.

## Tests after the wires are in

Follow [04-tests.md](04-tests.md) P01 then P02. Look at the gate while
the numbers print. Do not type `o` or press A0 until P01 has been read. Save
captures under `verification/runs/` with the date of the run.
