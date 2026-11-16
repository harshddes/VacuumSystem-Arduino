// Read-only listen for the two Hornet boxes on one RS485 pair.
// D8 stays LOW for the whole run. No filament, no degas, no valve.
//
// Bench wires, after the swap: Hornet pin 6 to DFR0845 A, pin 9 to B,
// pin 4 to the isolated ground beside them. The UART frame does not
// carry A or B. The transceiver turns each bit into that pair, so a
// wire swap is not a byte the sketch can flip.
//
// 1. Force the relay pin low before any serial start.
// 2. Open UART1 at 19200 8N1, the speed the working gauge already used.
// 3. Ask address 1, then address 2, for BINARY READ CG1 only.
// 4. Print every byte that comes back, including a short or a long frame.
// Wiring under test: pin 6 to A, pin 9 to B, pin 4 to the isolated ground.

#include <Wire.h>
#include <DFRobot_IICSerial.h>

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
const uint8_t kRelayPin = 8;

// Same CRC the working CG1 frame used: poly 0x1D, init 0xFF, no final XOR.
uint8_t crc8(const uint8_t *d, uint8_t n) {
  uint8_t crc = 0xFF;
  for (uint8_t i = 0; i < n; i++) {
    crc ^= d[i];
    for (uint8_t b = 0; b < 8; b++) {
      crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x1D) : (uint8_t)(crc << 1);
    }
  }
  return crc;
}

void printHex(uint8_t b) {
  if (b < 16) Serial.write('0');
  Serial.print(b, HEX);
}

void askBinary(uint8_t addr) {
  uint8_t frame[9] = {0x21, addr, 0x03, 0, 0, 0, 0, 0, 0};
  frame[8] = crc8(frame, 8);
  while (uart1.available()) uart1.read();
  Serial.print(F("ADDR "));
  Serial.print(addr);
  Serial.print(F(" TX"));
  for (uint8_t i = 0; i < 9; i++) {
    Serial.write(' ');
    printHex(frame[i]);
  }
  Serial.println();
  uart1.write(frame, 9);
  uart1.flush();

  uint8_t buf[48];
  uint8_t n = 0;
  const unsigned long start = millis();
  while (millis() - start < 500 && n < sizeof(buf)) {
    if (uart1.available()) buf[n++] = (uint8_t)uart1.read();
  }
  Serial.print(F("RX n="));
  Serial.print(n);
  if (n == 0) {
    Serial.println(F(" NONE"));
    return;
  }
  Serial.print(F(" HEX"));
  for (uint8_t i = 0; i < n; i++) {
    Serial.write(' ');
    printHex(buf[i]);
  }
  const bool crcOk = n >= 9 && crc8(buf, 8) == buf[8];
  Serial.print(crcOk ? F(" CRC_OK") : F(" CRC_BAD"));
  Serial.println();
  delay(80);
}

void setup() {
  digitalWrite(kRelayPin, LOW);
  pinMode(kRelayPin, OUTPUT);
  digitalWrite(kRelayPin, LOW);
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  Wire.clearWireTimeoutFlag();
  Serial.println(F("TWO HORNET READ. D8 LOW. CG1 only. No filament."));
  if (uart1.begin(19200, IICSerial_8N1) != DFROBOT_IICSERIAL_ERR_OK) {
    Serial.println(F("INIT FAIL"));
    return;
  }
  Wire.setWireTimeout(25000, true);
  // Two boxes may both still be address 1. Ask each address twice.
  askBinary(1);
  askBinary(1);
  askBinary(2);
  askBinary(2);
  Serial.println(F("DONE. D8 still LOW."));
}

void loop() {
  digitalWrite(kRelayPin, LOW);
}
