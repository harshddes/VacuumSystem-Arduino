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
or pull it; it is not the real gate. Open false is never treated as
closed.

Related pages:

- Desk package: [README.md](README.md)
- Pin map: [pin-map.csv](pin-map.csv)
- Wire list for this circuit: [phase3-wire-schedule.csv](phase3-wire-schedule.csv)
- Test names: [04-tests.md](04-tests.md)
- What is still unread: [06-field-holds.md](06-field-holds.md)
- Pass or fail lines: [verification/physical-test-log.csv](verification/physical-test-log.csv)
- Sketch: [firmware/gpio_interlock_bench/gpio_interlock_bench.ino](firmware/gpio_interlock_bench/gpio_interlock_bench.ino)

## What the sheets already say

SG position switches are two-wire, normally open reeds. Each closes only
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

A closed reed that ohms as a dead short looks like “valve is closed” all
the time, including when the gate is open. That pair stays off B4.
Operator reports the closed switch is not working. **Do not land it on
B4.** Open-switch false means “not proven open.” It does not mean closed.

## Parts on the desk

- Adafruit 5346 already at 0x21, already on Uno 5V / GND / A4 / A5
- Red 1-channel 5 V relay module, screws DC+ / DC− / IN and NC / COM / NO
- One 1N400x diode across the Humphrey coil only. Stripe toward 24 V +
- 24 V DC supply for the Humphrey coil only
- Meter

Put the black H/L cap on the two pins next to **H**. Leave **NC** empty.

## Meter the reeds before they land

USB unplugged. 24 V off. If a pair already has more than 5 V on it from
an old lamp circuit, lift that circuit first.

1. Find the two wires marked open. Meter ohms. Record the number with
   the gate as it sits.
2. Find the two wires marked closed. Meter ohms with the gate as it
   sits, then again after the gate has been moved if that is already
   possible by hand or by a prior pilot. If that pair is about 0 ohms
   both times, it is a stuck short. It stays off B4.
3. The open pair lands even if the closed pair stays off.

## One wiring pass

Wire IDs are in [phase3-wire-schedule.csv](phase3-wire-schedule.csv).

Reed pairs, 5 V only:

- Closed reed: one wire to 5346 **A4**, the other to logic ground.
  Operator corrected this pair on 2026-11-04. It is the closed mark,
  and it works.
- Open reed: one wire to 5346 **B4**, the other to logic ground.

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

Upload `gpio_interlock_bench`. Serial Monitor **115200**. Boot line:

```text
GATE BENCH - MCP 0x21; A4 open reed, B4 closed reed; D8 LOW
```

Each second it prints `OPEN=`, `CLOSED=`, `POS=`, and `D8=`.

| OPEN | CLOSED | POS | Meaning |
| --- | --- | --- | --- |
| 1 | 0 | OPEN | Magnet at the open switch |
| 0 | 1 | CLOSED | Magnet at the closed switch |
| 0 | 0 | UNKNOWN | Neither switch proven |
| 1 | 1 | FAULT | Impossible pair; do not treat as closed |

`OPEN=0` is “not proven open.” It is not closed.

Type `o` only after P01. That raises D8 for at most 8 seconds. Type `x`
to drop it sooner. If the expander is offline, `o` is refused and D8
stays low.

## Tests after the wires are in

Follow [04-tests.md](04-tests.md) P01 then P02. Look at the gate while
the numbers print. Do not type `o` until P01 has been read. Save
captures under `verification/runs/` with the date of the run.
