# Board in front of the laptop

Read this file first.

- A wire fact comes from the Eagle schematic, via `docs/index/pin-index.jsonl`.
- A sentence in a manual comes from `docs/index/text/`, and the page banner is the page to open in the PDF.
- The header names in the product manual are joined to those wires in `docs/index/connector-crosswalk.json`.
- The USB identity below was read from this PC. It is not a line in a PDF.

## Measured on this PC

- Date: 2026-10-06
- Windows name: USB Serial Device (COM3)
- USB vendor/product/revision: 2341 / 0043 / 0001
- Serial: 5583833383235121B1D0
- Worker-chip package: unresolved. This USB identity is shared by the socket board A000066 and the flat-chip board A000073. The worker-chip package is a visual check.

## Fitted chips, from the schematics

- A000066 `ZU4` value `(blank)` device `PU` package `DIL28-3`
  - Library blurb, not a specification: MICROCONTROLLER 4 Kbytes FLASH 128 bytes SRAM 256 bytes EEPROM UART 6-channel 10 bit ADC
- A000066 `U3` value `ATMEGA16U2-MU(R)` device `MU` package `MLF32`
- A000073 `U3` value `16U2` device `` package `ATMEL_QFN32`
  - Library blurb, not a specification: AVR AVR® ATmega Microcontroller IC 8-Bit 16MHz 16KB (8K x 16) FLASH 32-VQFN (5x5)
- A000073 `U4` value `ATMEGA328P-MU` device `-MUR` package `MLF32`
  - Library blurb, not a specification: MICROCONTROLLER 8 Kbytes FLASH 1 kbytes SRAM 512 bytes EEPROM USART 6-channel 10 bit ADC 2-channel 8 bit ADC Source: avr.lbr

Use the Microchip page text for memory size and electrical limits. The library blurb above still describes an older, smaller chip.

## Drawings compared

- Worker ports with the same wire: 21.
- Same wire, different net label: 7.
- Pin exists on only one package: 2 (ADC6, ADC7).
- Real wiring disagreements: 0.
- Manual header rows that disagree with the drawing: 0.

Open `docs/index/A000066-pins.md` for the socket board and `docs/index/A000073-pins.md` for the flat-chip board.

## Page text

- `docs/index/text/A000066-datasheet.txt` — 27 pages, 37866 characters, source `docs/uno-r3-dip-A000066/A000066-datasheet.pdf`
- `docs/index/text/A000066-full-pinout.txt` — 5 pages, 29824 characters, source `docs/uno-r3-dip-A000066/A000066-full-pinout.pdf`
- `docs/index/text/A000066-schematics.txt` — 2 pages, 86781 characters, source `docs/uno-r3-dip-A000066/A000066-schematics.pdf`
- `docs/index/text/A000073-full-pinout.txt` — 4 pages, 23722 characters, source `docs/uno-r3-smd-A000073/A000073-full-pinout.pdf`
- `docs/index/text/A000073-schematics.txt` — 2 pages, 188253 characters, source `docs/uno-r3-smd-A000073/A000073-schematics.pdf`
- `docs/index/text/ATmega328P-complete-DS40002061B.txt` — 653 pages, 2014026 characters, source `docs/chips/ATmega328P-complete-DS40002061B.pdf`
- `docs/index/text/ATmega16U2-complete-doc7799.txt` — 310 pages, 1132576 characters, source `docs/chips/ATmega16U2-complete-doc7799.pdf`

Search with `python docs/tools/lookup.py pin D13` or `python docs/tools/lookup.py text 500mA`.
Rebuild with `python docs/tools/build_index.py` after a source file changes.
