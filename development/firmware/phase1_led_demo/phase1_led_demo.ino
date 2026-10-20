// MAIZE desk exercise: ARDUINO UNO R3, 5 V, SWITCHES AND LEDs ONLY.
// Do not attach this demonstration to any valve driver, coil or pressure instrument.
//
// This board: pins 5 and 6 failed the fast half-blink check, so the two wires
// that used to land there now land on 12 and 13. Pin 11 has no button.
//
// Pseudocode
//   read nine wires; touching ground counts as true
//   vent lamp on when the vent button is on, the cryo button is off,
//     and the cryo-closed, other-paths, and filament wires are on
//   cryo lamp on when the cryo button is on, the vent button is off,
//     and the vent-closed, pressure, and cryo-ready wires are on
//   both buttons on: both door lamps off, fault lamp on
//   a button that is already on still counts. There is no start-over press.
#include "bench_logic.h"

const uint8_t inputPins[9] = {2, 3, 4, 12, 13, 7, 8, 9, 10};
const uint8_t cryoLed = A0, ventLed = A1, faultLed = A2;
bool rawState[9] = {false}, stableState[9] = {false};
unsigned long changedAt[9] = {0};
const unsigned long debounceMs = 30; // Desk contact filtering only, not a field response limit.
unsigned long nextReport = 0;

void setup() {
  digitalWrite(cryoLed, LOW);
  digitalWrite(ventLed, LOW);
  digitalWrite(faultLed, HIGH);
  pinMode(cryoLed, OUTPUT);
  pinMode(ventLed, OUTPUT);
  pinMode(faultLed, OUTPUT);
  for (uint8_t i = 0; i < 9; i++) {
    pinMode(inputPins[i], INPUT_PULLUP);
    rawState[i] = stableState[i] = (digitalRead(inputPins[i]) == LOW);
    changedAt[i] = millis();
  }
  Serial.begin(9600);
  Serial.println(F("BENCH ONLY"));
  Serial.println(F("D2 cryo button, D3 vent button"));
  Serial.println(F("Vent lamp follows D3. Cryo lamp follows D2."));
}

void loop() {
  const unsigned long now = millis();
  for (uint8_t i = 0; i < 9; i++) {
    const bool sample = digitalRead(inputPins[i]) == LOW;
    if (sample != rawState[i]) {
      rawState[i] = sample;
      changedAt[i] = now;
    }
    if (now - changedAt[i] >= debounceMs) stableState[i] = rawState[i];
  }

  const bool cryoReq = stableState[0];
  const bool ventReq = stableState[1];
  const bool cryoClosed = stableState[2];
  const bool ventClosed = stableState[3];
  const bool pressOk = stableState[4];
  const bool pressLow = stableState[5];
  const bool cryoReady = stableState[6];
  const bool paths = stableState[7];
  const bool filament = stableState[8];

  const bool cryoPermit = ventClosed && pressOk && pressLow && cryoReady;
  const bool ventPermit = cryoClosed && paths && filament;
  const bool both = cryoReq && ventReq;
  const bool cryoOn = cryoReq && !ventReq && cryoPermit;
  const bool ventOn = ventReq && !cryoReq && ventPermit;
  const bool fault = both || (cryoReq && !cryoOn) || (ventReq && !ventOn);

  digitalWrite(cryoLed, cryoOn ? HIGH : LOW);
  digitalWrite(ventLed, ventOn ? HIGH : LOW);
  digitalWrite(faultLed, fault ? HIGH : LOW);

  if (now >= nextReport) {
    nextReport = now + 1000;
    Serial.print(F("cryoBtn="));
    Serial.print(cryoReq ? '1' : '0');
    Serial.print(F(" ventBtn="));
    Serial.print(ventReq ? '1' : '0');
    Serial.print(F(" cryoLight="));
    Serial.print(cryoOn ? '1' : '0');
    Serial.print(F(" ventLight="));
    Serial.print(ventOn ? '1' : '0');
    Serial.print(F(" faultLight="));
    Serial.println(fault ? '1' : '0');
  }
}
