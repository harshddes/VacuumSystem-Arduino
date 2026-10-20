# Install the exact libraries used for the supplied sketches

Use Arduino IDE's **Sketch > Include Library > Add .ZIP Library**. Choose each ZIP below; do not unzip it first for that menu action. If the IDE says a library already exists, check its version in Library Manager rather than creating several competing copies.

| Sketch | Required library ZIPs |
|---|---|
| `uart_loopback` | `DFRobot_IICSerial-1.0.2.zip` |
| `gpio_interlock_bench` | `Adafruit_MCP23017_Arduino_Library-2.3.2.zip` and `Adafruit_BusIO-1.17.4.zip` |

The ZIPs are in this directory. Wire and SPI come with the **Arduino AVR Boards 1.8.6** core used for validation. Both sketches target **Arduino Uno / arduino:avr:uno**. They do not use Uno D5/D6/D7 and do not require LabVIEW.

Then open the `.ino` inside its same-name folder, select **Tools > Board > Arduino AVR Boards > Arduino Uno**, and click **Verify**. To upload later, select the actual USB port and click Upload. The GPIO sketch's `bench_logic.h` must stay beside its `.ino`.

The DFRobot ZIP is assembled from the manufacturer's 1.0.2 source files and MIT license, with blob hashes recorded in the source register. Its original raw source is also under `vendor/DFRobot_IICSerial`. The two Adafruit ZIPs are unchanged Arduino Library Manager distribution archives, retaining their license files. SHA-256 hashes are recorded in `bundled-files.json`.

Manufacturer sources: https://github.com/DFRobot/DFRobot_IICSerial and https://github.com/adafruit/Adafruit-MCP23017-Arduino-Library and https://github.com/adafruit/Adafruit_BusIO.

Library installation is not firmware installation: uploading a sketch replaces the program on the Uno. Save the old sketch first. Use the exact sketch named for each drawing.
