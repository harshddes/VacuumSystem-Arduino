#pragma once
#include <Arduino.h>

// Synthetic units for the physical potentiometer. The AVR build only drives LEDs.
namespace installation {
constexpr bool autoPathQualified = true;
constexpr uint32_t travelOpenMs = 8000, travelCloseMs = 8000;
constexpr uint32_t pressureDwellMs = 500, roughdownMs = 60000, ventMs = 60000;
constexpr float cryoEnterTorr = 1, cryoTripTorr = 2;
constexpr float turboEnterTorr = 1, turboTripTorr = 2;
constexpr float roughCrossoverTorr = 0.8f, ventCompleteTorr = 10;
constexpr uint16_t allowedPumpMasks = (1u << 1) | (1u << 4) | (1u << 8);
}
#include "Controller.h"

namespace uno_bench {
constexpr uint8_t selectors[] = {2, 3, 4, 5}; // Roughing, Let-up, Turbo, Cryo
constexpr uint8_t contacts[] = {6, 7, 8, 9}; // Turbo closed/open, Cryo closed/open
constexpr uint8_t leds[] = {12, 13, A0, A1};
constexpr uint8_t arm = 10, healthy = 11, pressure = A2, automatic = A3, pump = A4, vent = A5;
maize::Controller control;
uint16_t stable, candidate;
uint32_t changed, lastScan, lastReport, sequence;

bool grounded(uint8_t pin) { return digitalRead(pin) == LOW; }
uint16_t readContacts() {
  uint16_t bits = 0;
  for (unsigned i = 0; i < 4; i++) {
    if (grounded(selectors[i])) bits |= 1u << i;
    if (grounded(contacts[i])) bits |= 1u << (4+i);
  }
  if (grounded(arm)) bits |= 1u << 8;
  if (grounded(automatic)) bits |= 1u << 9;
  if (grounded(pump)) bits |= 1u << 10;
  if (grounded(vent)) bits |= 1u << 11;
  if (grounded(healthy)) bits |= 1u << 12;
  return bits;
}
void report(const maize::Snapshot& s, unsigned adc) {
  const maize::Decision& d = control.d;
  // Payload order matches MAIZE3. Offset by one to keep the bench scale positive.
  unsigned centi = 1 + adc * 1200UL / 1023;
  Serial.print(F("UNO3,"));
  Serial.print(++sequence); Serial.print(',');
  Serial.print(s.time); Serial.print(',');
  Serial.print(unsigned(s.mode)); Serial.print(',');
  Serial.print(unsigned(control.stage)); Serial.print(',');
  Serial.print(s.selectors); Serial.print(',');
  Serial.print(s.positions); Serial.print(',');
  Serial.print(d.attempt); Serial.print(',');
  Serial.print(d.status); Serial.print(',');
  Serial.print(d.site); Serial.print(',');
  Serial.print(d.events); Serial.print(',');
  Serial.print(d.alarms); Serial.print(',');
  Serial.print(control.latch); Serial.print(',');
  Serial.print(control.command); Serial.print(',');
  Serial.print(centi / 100); Serial.print('.');
  if (centi % 100 < 10) Serial.print('0');
  Serial.print(centi % 100);
  Serial.println(F(",0,15"));
}
}

void setup() {
  using namespace uno_bench;
  for (auto pin: selectors) pinMode(pin, INPUT_PULLUP);
  for (auto pin: contacts) pinMode(pin, INPUT_PULLUP);
  const uint8_t otherInputs[] = {arm, healthy, pressure, automatic, pump, vent};
  for (auto pin: otherInputs) pinMode(pin, INPUT_PULLUP);
  for (auto pin: leds) {
    digitalWrite(pin, LOW);
    pinMode(pin, OUTPUT);
  }
  stable = candidate = readContacts();
  Serial.begin(115200);
}

void loop() {
  using namespace uno_bench;
  uint32_t now = millis();
  if (now-lastScan < 10) return;
  lastScan = now;
  uint16_t input = readContacts();
  if (input != candidate) {
    candidate = input;
    changed = now;
  }
  if (now-changed >= 25) stable = candidate;

  maize::Snapshot s;
  s.time = now;
  s.selectors = stable & 15;
  s.positions = ((s.selectors & 1) ? 2 : 1) | ((s.selectors & 2) ? 8 : 4) | (stable & 240);
  s.mode = stable & (1u << 9) ? maize::Auto : maize::Manual;
  s.arm = stable & (1u << 8);
  s.pump = stable & (1u << 10);
  s.vent = stable & (1u << 11);
  s.validPanel = true;
  // Removing the permissive jumper drops permission immediately.
  bool permitted = (stable & input & (1u << 12)) != 0;
  s.basic = permitted ? (1 | 2 | 4 | 8 | 16 | 64 | 128 | 256 | 512 | 1024) : 16;
  s.processSafe = permitted;
  s.roughClosure = (s.positions & 3) == 1 && control.closedOutput(0, now);
  s.ventClosure = (s.positions & 12) == 4 && control.closedOutput(1, now);
  unsigned adc = analogRead(pressure);
  s.pressureValid = true;
  s.torr = (1 + adc * 1200UL / 1023) / 100.0f;
  control.tick(s, true);
  for (unsigned i = 0; i < 4; i++) digitalWrite(leds[i], control.command & (1u << i) ? HIGH : LOW);
  if (now-lastReport >= 150) {
    lastReport = now;
    report(s, adc);
  }
}
