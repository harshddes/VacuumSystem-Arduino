# Arduino Uno Rev3 reference pack

Downloaded 2026-10-06 from the official Arduino and Microchip pages. The laptop sees this board as an official Uno Rev3 (`VID 2341`, `PID 0043`, serial `5583833383235121B1D0`). That identity is shared by the socket board and the flat-chip board, so both official packs are here.

Look at the middle of the board, not the small chip beside the USB socket.

- Long black chip in a socket: use `uno-r3-dip-A000066`. Product code A000066.
- Small square chip soldered flat: use `uno-r3-smd-A000073`. Product code A000073.

## What to open first

The editable drawings are Eagle (`.sch`, `.brd`). Altium Viewer cannot open them. The schematic PDF is the picture. The searchable copy of every PDF, with page numbers, is in `index/text/`. The wiring lookup built from the Eagle files is in `index/`. Start at `index/BOARD.md`.

Rebuild the lookup with `python docs/tools/build_index.py`. Ask it a question with `python docs/tools/lookup.py pin D13` or `python docs/tools/lookup.py text 500mA`.

| File | What it is |
| --- | --- |
| `*-full-pinout.pdf` | Every metal leg, named the way the board silk and the chip both call it |
| `*-schematics.pdf` | The wiring picture |
| `A000066-datasheet.pdf` | Arduino's short product manual for the socket Uno. The flat-chip page does not publish a separate one |
| `cad/*.sch` | Eagle schematic, same design as the PDF |
| `cad/*.brd` | Eagle board layout |
| `chips/ATmega328P-complete-DS40002061B.pdf` | Full manual for the worker chip. About 660 pages |
| `chips/ATmega16U2-complete-doc7799.pdf` | Full manual for the small USB translator chip |

## Sources

Socket board, A000066:

- https://docs.arduino.cc/hardware/uno-rev3/
- https://docs.arduino.cc/resources/pinouts/A000066-full-pinout.pdf
- https://docs.arduino.cc/resources/datasheets/A000066-datasheet.pdf
- https://docs.arduino.cc/resources/schematics/A000066-schematics.pdf
- https://docs.arduino.cc/static/6bb7a3ca51ebee82a252f60c0b418787/A000066-cad-files.zip

Flat-chip board, A000073:

- https://docs.arduino.cc/hardware/uno-rev3-smd/
- https://docs.arduino.cc/resources/pinouts/A000073-full-pinout.pdf
- https://docs.arduino.cc/resources/schematics/A000073-schematics.pdf
- https://docs.arduino.cc/static/218e8c938107e2e814c4b7e048e303fb/A000073-cad-files.zip

Chips:

- ATmega328P complete datasheet, DS40002061B: https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATmega48A-PA-88A-PA-168A-PA-328-P-DS-DS40002061B.pdf
- ATmega16U2 complete datasheet, doc7799: https://ww1.microchip.com/downloads/en/DeviceDoc/doc7799.pdf

## License

The board design files include Arduino's notice: Creative Commons Attribution-ShareAlike 4.0 International. https://creativecommons.org/licenses/by-sa/4.0/deed.en

The two chip manuals are Microchip documents, saved here from Microchip's own download links.
