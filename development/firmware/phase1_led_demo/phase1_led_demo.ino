// MAIZE desk exercise: ARDUINO UNO R3, 5 V, SWITCHES AND LEDs ONLY.
// Do not attach this demonstration to any valve driver, coil or pressure instrument.
// It lacks real sensor diagnostics, motion timing and hardware failure protection.
#include "bench_logic.h"
const uint8_t inputPins[10]={2,3,4,5,6,7,8,9,10,11};
const uint8_t cryoLed=A0, ventLed=A1, faultLed=A2;
bool rawState[10]={false}, stableState[10]={false};
unsigned long changedAt[10]={0};
const unsigned long debounceMs=30; // Desk contact filtering only, not a field response limit.
BenchLogic logic;
bool lastCryo=false,lastVent=false,lastArmed=false,lastDenied=false;
void setup() {
  digitalWrite(cryoLed,LOW); digitalWrite(ventLed,LOW); digitalWrite(faultLed,HIGH);
  pinMode(cryoLed,OUTPUT); pinMode(ventLed,OUTPUT); pinMode(faultLed,OUTPUT);
  for(uint8_t i=0;i<10;i++) {
    pinMode(inputPins[i],INPUT_PULLUP);
    // Seed actual boot levels: a held RE-ARM must not look like a fresh press.
    rawState[i]=stableState[i]=(digitalRead(inputPins[i])==LOW);
    changedAt[i]=millis();
  }
  Serial.begin(9600);
  Serial.println(F("BENCH ONLY: simulated inputs; LED outputs"));
}
void loop() {
  const unsigned long now=millis();
  for(uint8_t i=0;i<10;i++) {
    const bool sample=digitalRead(inputPins[i])==LOW;
    if(sample!=rawState[i]) {rawState[i]=sample;changedAt[i]=now;}
    if(now-changedAt[i]>=debounceMs) stableState[i]=rawState[i];
  }
  Inputs in;
  in.cryoRequest=stableState[0];in.ventRequest=stableState[1];
  in.cryoClosed=stableState[2];in.ventClosed=stableState[3];
  in.pressureValid=stableState[4];in.pressureBand=stableState[5];
  in.cryoReady=stableState[6];in.otherPathsClosed=stableState[7];
  in.filamentProcessSafe=stableState[8];in.reset=stableState[9];
  logic.tick(in);
  digitalWrite(cryoLed,logic.out.cryo?HIGH:LOW);
  digitalWrite(ventLed,logic.out.vent?HIGH:LOW);
  digitalWrite(faultLed,(!logic.out.armed||logic.out.denied)?HIGH:LOW);
  if(logic.out.cryo!=lastCryo||logic.out.vent!=lastVent||logic.out.armed!=lastArmed||logic.out.denied!=lastDenied) {
    if(Serial.availableForWrite()>=50) {
      Serial.print(F("SIM armed="));Serial.print(logic.out.armed);
      Serial.print(F(" cryo="));Serial.print(logic.out.cryo);
      Serial.print(F(" vent="));Serial.print(logic.out.vent);
      Serial.print(F(" denied="));Serial.println(logic.out.denied);
      lastCryo=logic.out.cryo;lastVent=logic.out.vent;lastArmed=logic.out.armed;lastDenied=logic.out.denied;
    }
  }
}
