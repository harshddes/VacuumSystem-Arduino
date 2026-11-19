// MAIZE commissioning image. Reads contacts and answers one read-only UDP request.
// Loading a sketch replaces the controller program. Use on a separate commissioning Opta.
#include <OptaBlue.h>
#include <ArduinoRS485.h>
#include <Ethernet.h>
#include <EthernetUdp.h>
#include <math.h>

using namespace Opta;
const IPAddress controllerIP(192, 168, 10, 42); // select the address for the bench network
constexpr uint16_t port = 44820;
constexpr bool readHornet = false; // enable after checking isolation, address and binary mode
constexpr bool gaugeConfiguredInTorr = false; // confirm on the physical gauge
// Proposed I1/I2 = Cryo CLOSED/OPEN, I3/I4 = Turbo CLOSED/OPEN.
// Set true only after matching these four terminals to the two actual gates.
constexpr bool gateWiringConfirmed = false;
constexpr int gatePins[] = {A0, A1, A2, A3};
EthernetUDP udp;
uint32_t sequence, sampled, gaugeStarted, gaugeReceived;
uint8_t baseBits, rx[10], rxLength;
uint16_t expansionBits;
bool expansionOK, waiting, gaugeOK;
float gaugeValue;

uint8_t checksum(const uint8_t *p) {
  uint8_t crc = 0xff;
  for (unsigned i = 0; i < 8; ++i) {
    crc ^= p[i];
    for (unsigned bit = 0; bit < 8; ++bit)
      crc = (crc & 0x80) ? (crc << 1) ^ 0x1d : crc << 1;
  }
  return crc;
}

void updateGauge(uint32_t now) {
  if (!readHornet) return;
  // Capture excess bytes so long frames cannot pass a first-nine-bytes check.
  for (unsigned i = 0; i < 24 && RS485.available(); ++i) {
    uint8_t b = RS485.read();
    if (waiting && rxLength < sizeof(rx)) rx[rxLength++] = b;
  }
  if (waiting && now - gaugeStarted >= 180) {
    waiting = false;
    gaugeOK = rxLength == 9 && rx[0] == 0x2a && rx[1] == 1 &&
              rx[2] == 3 && rx[3] == 0 && rx[8] == checksum(rx);
    if (gaugeOK) {
      // Bench capture 2A 01 03 00 7F 2D 48 44 23, little-endian binary32.
      memcpy(&gaugeValue, rx + 4, sizeof(gaugeValue));
      gaugeOK = isfinite(gaugeValue) && gaugeValue > 0 && gaugeValue < 9.0e9f &&
                (!gaugeConfiguredInTorr || fabsf(gaugeValue - 1100.0f) > 1.0f);
      if (gaugeOK) gaugeReceived = now;
    }
  }
  if (!waiting && now - gaugeStarted >= 1000) {
    const uint8_t query[] = {0x21, 1, 3, 0, 0, 0, 0, 0, 0xf1}; // READ CG1 only
    RS485.noReceive();
    RS485.beginTransmission();
    RS485.write(query, sizeof(query));
    RS485.endTransmission();
    RS485.receive();
    rxLength = 0;
    gaugeStarted = now;
    waiting = true;
  }
}

void sampleInputs(uint32_t now) {
  baseBits = 0;
  for (uint8_t i = 0; i < 4; ++i)
    if (digitalRead(gatePins[i]) == HIGH) baseBits |= 1u << i;
  expansionOK = OptaController.getExpansionNum() == 1 &&
                OptaController.getExpansionType(0) == EXPANSION_OPTA_DIGITAL_MEC;
  expansionBits = 0;
  if (expansionOK) {
    DigitalMechExpansion e = OptaController.getExpansion(0);
    expansionOK = e && e.execute(GET_DIGITAL_INPUT) == EXECUTE_OK;
    if (expansionOK) {
      for (uint8_t i = 0; i < 16; ++i)
        if (e.digitalRead(i, false) == HIGH) expansionBits |= 1u << i;
    }
  }
  ++sequence;
  sampled = now;
}

void answerRead(uint32_t now) {
  char request[20];
  int size = udp.parsePacket();
  if (size <= 0) return;
  int count = udp.read(request, sizeof(request));
  // The caller supplies an eight-character hex transaction ID.
  if (size != 18 || count != size || memcmp(request, "MAIZE2 R ", 9) ||
      request[17] != '\n') return;
  for (uint8_t i = 9; i < 17; ++i) if (!isxdigit(request[i])) return;
  request[17] = 0;
  char pressure[32] = "-";
  bool valid = gaugeOK && now - gaugeReceived < 2000;
  if (valid) snprintf(pressure, sizeof(pressure), "%.8g", (double)gaugeValue);
  char packet[200];
  snprintf(packet, sizeof(packet), "MAIZE2,%s,%lu,%lu,%u,%d,%u,0,0,HOLD,%s,%s,%lu,COMMISSIONING,%d",
           request + 9, (unsigned long)sequence, (unsigned long)now, baseBits,
           expansionOK ? 1 : 0, expansionBits, pressure,
           gaugeConfiguredInTorr ? "TORR" : "NATIVE",
           (unsigned long)(valid ? now - gaugeReceived : 0), gateWiringConfirmed ? 1 : 0);
  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  udp.write((const uint8_t*)packet, strlen(packet));
  udp.endPacket();
}

void setup() {
  for (int p : gatePins) pinMode(p, INPUT);
  OptaController.begin();
  if (readHornet) {
    RS485.begin(19200, SERIAL_8N1);
    RS485.receive();
  }
  Ethernet.begin(controllerIP);
  udp.begin(port);
  sampleInputs(millis());
}

void loop() {
  OptaController.update();
  uint32_t now = millis();
  updateGauge(now);
  if (now - sampled >= 100) sampleInputs(now);
  answerRead(now);
}
