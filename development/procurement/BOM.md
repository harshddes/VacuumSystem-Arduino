# Bill of materials — buy in phases

Revision 2026-10-09 • USD • Excludes shipping, tax and tariffs

## Phase 1: the entire shopping list for now

You already have the Uno, breadboard and laptop. Confirm that the USB cable carries data. Use your existing jumpers if you have enough.

| Item | Actually used | Example order | Snapshot price |
|---|---:|---|---:|
| 470 Ω, ¼ W resistors | 3 | [Adafruit 2781, 25-pack](https://www.adafruit.com/product/2781) | $0.75 |
| Visible LEDs | 3 | [Adafruit 779, 25-pack](https://www.adafruit.com/product/779) | $4.95 |
| Momentary buttons | 3 | [Adafruit 1119, 10-pack](https://www.adafruit.com/product/1119) | $2.50 |
| Male-to-male jumpers, about 150 mm | **20**; 40 suggested on hand | [Adafruit 1957, two 20-packs](https://www.adafruit.com/product/1957) | $3.90 optional |

**$8.20 for the three component packs; $12.10 if you also buy 40 jumpers.** These listed prices were rechecked on 2026-10-09. Borrow a multimeter. One continuous ground rail is assumed; a split rail needs a bridge wire. See [the exact 20-wire connections](../02-phase1-breadboard.md).

You are buying spare components in packs, not building 25 channels. No relay board, valve supply or screen is needed to run the supplied sketch.

## Phase 2: purchase after confirming the Hornet firmware and existing cables

| Item | Qty | Candidate | Snapshot price |
|---|---:|---|---:|
| I²C dual UART | 1 | [DFRobot DFR0627, DigiKey](https://www.digikey.com/en/products/detail/dfrobot/DFR0627/12091972) | $8.00 |
| Isolated UART / RS-485 interface | 1 | [DFRobot DFR0845, DigiKey](https://www.digikey.com/en/products/detail/dfrobot/DFR0845/15283078) | $19.90 |
| Male DE-9 breakout for Hornet RS-485 socket | 1 | [Adafruit 3123](https://www.adafruit.com/product/3123) | $2.95 |
| Shielded data cable and appropriate terminals | As needed | Match length, reference and connector mapping | Quote |
| Hornet–Worker Bee sensor cable, if absent | 1 | InstruTech HB431-1-03F or appropriate length; verify compatibility | Quote |
| Instrument supply, only if missing | 1 | [Mean Well GST60A24-P1J, 24 V / 2.5 A](https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST60A24-P1J/7703715) | $19.40 |
| Existing Worker Bee CVG101GC | Reuse if working | Locate before buying a replacement sensor | No new purchase yet |

The first three items total **$30.85**, excluding cable, instrument supply and sensor cable. DFR0627, DFR0845 and the supply prices were rechecked on 2026-10-09; the breakout price is the 2026-10-08 snapshot. Reuse the Hornet's approved supply if present. A 24 V barrel supply needs a proper instrument harness; it does not plug into an Uno or a Hornet DE-9 socket.

## Phases 3–5: identify before purchasing

| Phase | Essential function | Purchase decision |
|---|---|---|
| 3 | Cryo gate pilot / actuator interface | Reuse the existing pilot if compatible; otherwise select after model/coil identification |
| 3 | Rated coil driver and suppression | Adafruit 6318, $14.95 snapshot, is only a compatible-DC-load candidate |
| 3 | OPEN/CLOSED and cold-ready inputs | Reuse actual end switches/readout outputs; add appropriate isolated/conditioned inputs |
| 3 | Independent opening inhibit and qualified closing service | Design from actual actuator failure behavior; quote |
| 3 | Regulated clean actuation gas, fittings and adequate-pressure proof | Reuse suitable lab services; never feed tank maximum pressure directly |
| 3 | Supplies, wiring, terminals, strain relief and protection | Size to measured loads; secure assembly before a real-valve trial |
| 4 | Automatic rough isolation and automatic metered vent | Reuse existing compatible actuated valves first |
| 4 | Individual physical valve closure, rough pump ready and filament-off proof | Required for the complete vent guardrail |
| 4 | Vacuum-rated fittings, vent restriction and bypass handling | Determine from as-built survey |
| 5 | Mode selector, CLOSE/STOP, ARM and sequence controls | Select after panel request wiring is mapped |
| 5 | Standalone regulated logic power, enclosure and final labeled harness | Required to operate independently of laptop USB |
| 5 | Front-panel pressure/status readout | Choose economical display after interface/memory budget; laptop suffices earlier |

Lesker **SAV0100PVQF** ($394 snapshot per valve) with separate **SE024D3XX** ($68 snapshot per pilot) was an OEM-documented example for roughing/vent planning. Two of each would be **$924 before fittings and supplies**. These are **not a required order or a cheapest-system claim**. Reuse/borrow or choose a properly sized lower-cost alternative after actual valve requirements are known. Vent valve sizing and flow restriction need separate review. A pneumatic pilot is not itself the vacuum isolation valve.

Optional GPIO expanders and single-channel MOSFET alternatives have quantity zero in the workbook; do not buy both a substitute driver and the selected driver without a reason. Turbo equipment and oil-pump accessories are outside the initial cryo build.

## Complete editable register

[maize-uno-bom.xlsx](maize-uno-bom.xlsx) contains 52 procurement lines, the hardware identification register and phase/fault acceptance records. [bom-data.json](bom-data.json) is the corresponding source data. Unknown prices stay **Quote**, not zero. Reuse zero-cost lines mean no planned new purchase, not proof that an item is present or functioning.

Supplier links favor manufacturers and authorized distributors. Product review ratings were not verified; no fabricated ratings are used. Prices and stock are snapshots, not delivery guarantees. Preserve the recorded check date and recheck at checkout. The priced HOLD subtotal is deliberately **not** presented as the total cost of the finished controller.
