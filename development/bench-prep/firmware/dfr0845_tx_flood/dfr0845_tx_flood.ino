// BENCH ONLY. Keeps DFR0627 UART1 busy so the DFR0845 TX lamp can be seen.
// Boot is idle. 'g' is an 8 second run of 0x00. No Hornet frame, no filament, no degas.
// The Hornet RS485 plug has to be out before 'g'. DFR0627 DIP A1=A0=1. USB 115200.
//
// write() returns at once when the 256-byte FIFO is full, so a timed burst that
// ignores that return only occupies the wire for one FIFO. Retry until the FIFO
// accepts the byte. Do not call flush(): its FIFO wait reads the flag once.

#include <Wire.h>
#include <DFRobot_IICSerial.h>

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
const unsigned long kFloodMs = 8000;
bool ready = false;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  Wire.clearWireTimeoutFlag();
  Serial.println(F("TX FLOOD IDLE. No filament. No degas. No Hornet frame."));
  const int started = uart1.begin(19200, IICSerial_8N1);
  ready = started == DFROBOT_IICSERIAL_ERR_OK;
  Wire.setWireTimeout(25000, true);
  if (!ready) {
    Serial.println(F("INIT FAIL: power down and inspect supply, A4/A5 and DIP A1=A0=1"));
    return;
  }
  Serial.println(F("UART1 19200 ready. Hornet RS485 plug out, then USB g."));
}

void loop() {
  if (!ready || !Serial.available()) return;
  const int key = Serial.read();
  if (key != 'g' && key != 'G') return;

  Serial.println(F("FLOOD START"));
  const unsigned long start = millis();
  while (millis() - start < kFloodMs) {
    if (uart1.write(static_cast<uint8_t>(0x00)) != 1) continue;
  }
  Serial.println(F("FLOOD STOP"));
}
