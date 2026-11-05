// BENCH ONLY. Hornet read-only trial. No filament, no degas, no valve.
// DFR0627 DIP A1=A0=1. UART1 19200 8N1 to DFR0845. USB Serial 115200.
//
// Boot stays idle so the RS485 plug can be seated before any byte leaves.
// USB c sends the 2444 book's BINARY READ CG1 frame. USB r sends BINARY
// READ IG, filament off, CRC 0xB7. That IG frame is a talk check, not a
// pressure. ASCII #01RDCG1 is USB a only. No IG-ON or degas bytes exist here.

#include <Wire.h>
#include <DFRobot_IICSerial.h>

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
const unsigned long kListenMs = 2000;
bool ready = false;

// Book example, filament off: ! addr=1 cmd=0x02 zeros CRC=0xB7
const uint8_t kBinIg[9] = {0x21, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB7};
// Same layout, cmd 0x03 = READ CG1. CRC-8 poly 0x1D, init 0xFF, no final XOR.
const uint8_t kBinCg1[9] = {0x21, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF1};
const char kAscii[] = "#01RDCG1\r";

void drainUart1() {
  const unsigned long start = millis();
  while (uart1.available() && millis() - start < 50) {
    uart1.read();
  }
}

void printByte(uint8_t b) {
  if (b == '\r') {
    Serial.print(F("\\r"));
    return;
  }
  if (b == '\n') {
    Serial.print(F("\\n"));
    return;
  }
  if (b >= 32 && b < 127) {
    Serial.write(b);
    return;
  }
  Serial.print(F("<"));
  if (b < 16) Serial.write('0');
  Serial.print(b, HEX);
  Serial.write('>');
}

void listenPrint() {
  uint8_t buf[96];
  size_t n = 0;
  const unsigned long start = millis();
  while (n < sizeof(buf) && millis() - start < kListenMs) {
    if (uart1.available()) {
      buf[n++] = static_cast<uint8_t>(uart1.read());
    }
    if (Wire.getWireTimeoutFlag()) break;
  }
  Wire.clearWireTimeoutFlag();
  Serial.print(F("RX n="));
  Serial.print(n);
  Serial.write(' ');
  if (n == 0) {
    Serial.println(F("NONE"));
    return;
  }
  for (size_t i = 0; i < n; i++) printByte(buf[i]);
  Serial.println();
  Serial.print(F("HEX"));
  for (size_t i = 0; i < n; i++) {
    Serial.write(' ');
    if (buf[i] < 16) Serial.write('0');
    Serial.print(buf[i], HEX);
  }
  Serial.println();
}

void sendFrame(const uint8_t *frame, size_t n, const __FlashStringHelper *tag) {
  drainUart1();
  Serial.print(tag);
  Serial.print(F(" TX"));
  for (size_t i = 0; i < n; i++) {
    Serial.write(' ');
    if (frame[i] < 16) Serial.write('0');
    Serial.print(frame[i], HEX);
  }
  Serial.println();
  uart1.write(frame, n);
  uart1.flush();
  listenPrint();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  Wire.clearWireTimeoutFlag();
  Serial.println(F("HORNET READ ONLY. No filament. No degas. No valve."));
  Serial.println(F("USB 115200. UART1 19200 8N1. Idle until a key."));
  const int first = uart1.begin(19200, IICSerial_8N1);
  ready = first == DFROBOT_IICSERIAL_ERR_OK;
  Wire.setWireTimeout(25000, true);
  if (!ready) {
    Serial.println(F("INIT FAIL: power down and inspect supply, A4/A5 and DIP A1=A0=1"));
    return;
  }
  Serial.println(F("IDLE. USB c=CG1 binary, r=IG binary, a=ASCII RDCG1"));
}

void loop() {
  if (!ready) {
    delay(1000);
    return;
  }
  if (!Serial.available()) return;
  const int c = Serial.read();
  if (c == 'r' || c == 'R') sendFrame(kBinIg, sizeof(kBinIg), F("BIN IG"));
  else if (c == 'c' || c == 'C') sendFrame(kBinCg1, sizeof(kBinCg1), F("BIN CG1"));
  else if (c == 'a' || c == 'A') {
    drainUart1();
    Serial.println(F("ASCII TX #01RDCG1\\r"));
    uart1.write(reinterpret_cast<const uint8_t *>(kAscii), sizeof(kAscii) - 1);
    uart1.flush();
    listenPrint();
  }
}
